from collections import Counter, defaultdict
from datetime import timedelta
from uuid import UUID

from app.domain.entities import Person
from app.domain.enums import HireType, InteractionChannel, InteractionSource, InteractionType
from app.domain.interactions import InteractionEvent
from network_compass_synthetic.generator import ORGANIZATION_SPECS, REFERENCE_TIME
from network_compass_synthetic.models import (
    DatasetSummary,
    SyntheticDataset,
    ValidationCheck,
    ValidationReport,
)
from network_compass_synthetic.serialization import collect_keys

REQUIRED_SCENARIO_CODES = {
    "ANALOG_ONLY_CLOSE",
    "DIGITAL_ONLY_CLOSE",
    "DUPLICATE_ANALOG_ENTRY",
    "EXPERIENCED_NEW_JOINER",
    "GRADUATE_NEW_JOINER",
    "LARGE_EVENT_ONLY",
    "LONG_NAME",
    "MISSING_ANALOG",
    "MISSING_AVATAR",
    "MULTIPLE_ORG_CONTEXT",
    "NO_NETWORK",
    "OLD_PROJECT",
    "ONE_SIDED_DIGITAL",
    "ONE_TO_ONE_LUNCH",
    "P001_MIXED_RELATIONSHIPS",
    "P018_DORMANT",
    "P067_TWO_HOP",
    "P102_RECONNECTED",
    "RECIPROCAL_DIGITAL",
    "SAME_ACTIVITY_NO_INTERACTION",
    "SAME_COMMUNITY_NO_INTERACTION",
}
FORBIDDEN_KEYS = {
    "audiobody",
    "bluetoothproximity",
    "emailbody",
    "gpslocation",
    "messagebody",
    "privateaudio",
    "transcript",
}


def _person_code(person: Person) -> str:
    for identifier in person.external_identifiers:
        if identifier.source_system == "synthetic":
            return identifier.external_id
    raise ValueError(f"synthetic person mapping missing for {person.id}")


def _people_by_code(dataset: SyntheticDataset) -> dict[str, Person]:
    return {_person_code(person): person for person in dataset.people}


def _pair_events(
    dataset: SyntheticDataset,
    first_person_id: UUID,
    second_person_id: UUID,
) -> tuple[InteractionEvent, ...]:
    expected = {first_person_id, second_person_id}
    return tuple(
        event
        for event in dataset.interaction_events
        if len(event.participant_ids) == 2 and set(event.participant_ids) == expected
    )


def _interaction_graph(dataset: SyntheticDataset) -> dict[UUID, set[UUID]]:
    graph: dict[UUID, set[UUID]] = defaultdict(set)
    for event in dataset.interaction_events:
        for person_id in event.participant_ids:
            graph[person_id].update(
                participant_id
                for participant_id in event.participant_ids
                if participant_id != person_id
            )
    return graph


def _community_ids(dataset: SyntheticDataset, person_id: UUID) -> set[UUID]:
    return {
        membership.community_id
        for membership in dataset.community_memberships
        if membership.person_id == person_id
    }


def _activity_ids(dataset: SyntheticDataset, person_id: UUID) -> set[UUID]:
    return {
        person_activity.activity_id
        for person_activity in dataset.person_activities
        if person_activity.person_id == person_id
    }


def _project_ids(dataset: SyntheticDataset, person_id: UUID) -> set[UUID]:
    return {
        participation.project_id
        for participation in dataset.project_participations
        if participation.person_id == person_id
    }


def _check(
    code: str,
    condition: bool,
    message: str,
    **details: object,
) -> ValidationCheck:
    return ValidationCheck(
        code=code,
        status="PASS" if condition else "FAIL",
        message=message,
        details=details,
    )


def _duplicate_analog_fingerprints(dataset: SyntheticDataset) -> int:
    fingerprints = Counter(
        (
            event.occurred_at,
            event.type,
            event.participant_ids,
            event.duration_bucket,
            event.activity_id,
            event.community_id,
            event.project_id,
        )
        for event in dataset.interaction_events
        if event.channel is InteractionChannel.ANALOG
    )
    return sum(1 for count in fingerprints.values() if count > 1)


def validate_dataset(dataset: SyntheticDataset) -> ValidationReport:
    people_by_code = _people_by_code(dataset)
    interaction_graph = _interaction_graph(dataset)
    scenario_by_code = {scenario.code: scenario for scenario in dataset.scenario_expectations}
    checks: list[ValidationCheck] = []

    if dataset.family == "demo":
        checks.append(
            _check(
                "AC-S02",
                len(dataset.people) == 250,
                "Demo contains exactly 250 people.",
                actual=len(dataset.people),
                expected=250,
            )
        )
        organization_name_by_id = {
            organization.id: organization.name for organization in dataset.organization_units
        }
        organization_counts = Counter(
            organization_name_by_id[person.primary_organization_unit_id]
            for person in dataset.people
            if person.primary_organization_unit_id is not None
        )
        expected_counts = {
            specification.name: specification.count for specification in ORGANIZATION_SPECS
        }
        checks.append(
            _check(
                "AC-S03",
                dict(organization_counts) == expected_counts,
                "Demo organization composition matches the frozen specification.",
                actual=dict(organization_counts),
                expected=expected_counts,
            )
        )
        recent_joiners = [
            person
            for person in dataset.people
            if REFERENCE_TIME - person.joined_at <= timedelta(days=180)
        ]
        recent_hire_types = {person.hire_type.value for person in recent_joiners}
        checks.append(
            _check(
                "RECENT_JOINERS",
                20 <= len(recent_joiners) <= 30
                and {"GRADUATE", "EXPERIENCED"}.issubset(recent_hire_types),
                "Demo has 20-30 recent joiners including graduate and experienced hires.",
                count=len(recent_joiners),
                hire_types=sorted(recent_hire_types),
            )
        )

        p001 = people_by_code["P001"]
        p001_counterparts = interaction_graph[p001.id]
        p001_two_hop_people: set[UUID] = set()
        for counterpart_id in p001_counterparts:
            p001_two_hop_people.update(interaction_graph[counterpart_id])
        p001_two_hop_people.difference_update(p001_counterparts | {p001.id})
        checks.extend(
            (
                _check(
                    "AC-S04",
                    len(p001_counterparts) == 40,
                    "P001 has exactly forty direct meaningful-interaction counterparts.",
                    actual=len(p001_counterparts),
                    expected=40,
                ),
                _check(
                    "P001_TWO_HOP_REACH",
                    40 <= len(p001_two_hop_people) <= 60,
                    "P001 has the specified forty to sixty people at exactly two hops.",
                    actual=len(p001_two_hop_people),
                    expected_range=[40, 60],
                ),
            )
        )

        close_codes = tuple(f"P{index:03d}" for index in range(2, 10))
        active_codes = tuple(f"P{index:03d}" for index in (*range(10, 18), *range(19, 26)))
        weak_codes = tuple(f"P{index:03d}" for index in range(26, 41))

        def p001_pair_events(code: str) -> tuple[InteractionEvent, ...]:
            return _pair_events(dataset, p001.id, people_by_code[code].id)

        close_patterns_present = all(
            len(events := p001_pair_events(code)) >= 6
            and {event.channel for event in events}
            == {InteractionChannel.DIGITAL, InteractionChannel.ANALOG}
            and all(REFERENCE_TIME - event.occurred_at <= timedelta(days=60) for event in events)
            for code in close_codes
        )
        active_patterns_present = all(
            len(events := p001_pair_events(code)) >= 3
            and {event.channel for event in events}
            == {InteractionChannel.DIGITAL, InteractionChannel.ANALOG}
            and all(REFERENCE_TIME - event.occurred_at <= timedelta(days=90) for event in events)
            for code in active_codes
        )
        weak_patterns_present = all(
            len(events := p001_pair_events(code)) == 1
            and timedelta(days=175) <= REFERENCE_TIME - events[0].occurred_at <= timedelta(days=200)
            for code in weak_codes
        )
        checks.append(
            _check(
                "P001_MIXED_FACT_PATTERN",
                close_patterns_present and active_patterns_present and weak_patterns_present,
                "P001 has explicit recent-hybrid, active, and sparse-old fact cohorts; "
                "dormant and reconnected patterns are checked separately.",
                active_candidate_count=len(active_codes),
                close_candidate_count=len(close_codes),
                weak_candidate_count=len(weak_codes),
            )
        )

        p201 = people_by_code["P201"]
        cohort_ids = {people_by_code[f"P{index:03d}"].id for index in range(203, 211)}
        new_joiner_community_id = next(
            community.id
            for community in dataset.communities
            if community.name == "New Joiner Community"
        )
        cohort_with_p201 = cohort_ids | {p201.id}
        cohort_members = {
            membership.person_id
            for membership in dataset.community_memberships
            if membership.community_id == new_joiner_community_id
        }
        cohort_project_sets = [_project_ids(dataset, person_id) for person_id in cohort_with_p201]
        shared_cohort_projects = cohort_project_sets[0].intersection(*cohort_project_sets[1:])
        checks.append(
            _check(
                "P201_GRADUATE_PERSONA",
                REFERENCE_TIME - p201.joined_at == timedelta(days=30)
                and p201.hire_type is HireType.GRADUATE
                and cohort_ids.issubset(interaction_graph[p201.id])
                and cohort_with_p201.issubset(cohort_members)
                and bool(shared_cohort_projects),
                "P201 is a thirty-day graduate with cohort-heavy interaction and team context.",
                direct_counterpart_count=len(interaction_graph[p201.id]),
                cohort_counterpart_count=len(cohort_ids & interaction_graph[p201.id]),
                shared_cohort_project_count=len(shared_cohort_projects),
            )
        )

        p202 = people_by_code["P202"]
        p202_community_count = len(_community_ids(dataset, p202.id))
        p202_skill_count = sum(
            person_skill.person_id == p202.id for person_skill in dataset.person_skills
        )
        p202_project_count = len(_project_ids(dataset, p202.id))
        checks.append(
            _check(
                "P202_EXPERIENCED_PERSONA",
                REFERENCE_TIME - p202.joined_at == timedelta(days=45)
                and p202.hire_type is HireType.EXPERIENCED
                and len(interaction_graph[p202.id]) <= 5
                and p202_community_count >= 2
                and p202_skill_count >= 4
                and p202_project_count >= 3,
                "P202 is a forty-five-day experienced hire with rich context "
                "and a thin internal network.",
                direct_counterpart_count=len(interaction_graph[p202.id]),
                community_count=p202_community_count,
                skill_count=p202_skill_count,
                project_count=p202_project_count,
            )
        )

    scenario_codes = {scenario.code for scenario in dataset.scenario_expectations}
    checks.append(
        _check(
            "EDGE_CASE_COVERAGE",
            REQUIRED_SCENARIO_CODES.issubset(scenario_codes),
            "Every required hero and edge-case scenario is present.",
            missing=sorted(REQUIRED_SCENARIO_CODES - scenario_codes),
        )
    )

    joined_at_by_person_id = {person.id: person.joined_at for person in dataset.people}
    events_before_joining = [
        str(event.id)
        for event in dataset.interaction_events
        if any(
            event.occurred_at < joined_at_by_person_id[participant_id]
            for participant_id in event.participant_ids
        )
    ]
    checks.append(
        _check(
            "AC-S10",
            not events_before_joining,
            "No interaction occurs before any participant joined.",
            offending_event_ids=events_before_joining,
        )
    )

    p001 = people_by_code["P001"]
    p010 = people_by_code["P010"]
    p067 = people_by_code["P067"]
    direct_p001_p067 = _pair_events(dataset, p001.id, p067.id)
    path_exists = bool(_pair_events(dataset, p001.id, p010.id)) and bool(
        _pair_events(dataset, p010.id, p067.id)
    )
    checks.append(
        _check(
            "AC-S08-S09",
            not direct_p001_p067 and path_exists,
            "P067 is not direct and is reachable through the expected P010 path.",
            direct_event_count=len(direct_p001_p067),
            expected_path=["P001", "P010", "P067"],
        )
    )

    p018_events = _pair_events(dataset, p001.id, people_by_code["P018"].id)
    p018_event_ages = [REFERENCE_TIME - event.occurred_at for event in p018_events]
    checks.append(
        _check(
            "P018_DORMANT_FACT_PATTERN",
            len(p018_events) >= 4
            and all(age > timedelta(days=180) for age in p018_event_ages)
            and {event.channel for event in p018_events}
            == {InteractionChannel.DIGITAL, InteractionChannel.ANALOG},
            "P018 has substantial old hybrid evidence and no recent P001 interaction.",
            event_count=len(p018_events),
            most_recent_days_ago=(
                min(age.days for age in p018_event_ages) if p018_event_ages else None
            ),
        )
    )

    p102_events = _pair_events(dataset, p001.id, people_by_code["P102"].id)
    p102_old_events = [
        event for event in p102_events if REFERENCE_TIME - event.occurred_at > timedelta(days=180)
    ]
    p102_recent_events = [
        event for event in p102_events if REFERENCE_TIME - event.occurred_at <= timedelta(days=30)
    ]
    checks.append(
        _check(
            "P102_RECONNECTED_FACT_PATTERN",
            len(p102_old_events) >= 3
            and any(
                event.channel is InteractionChannel.ANALOG
                and event.source is InteractionSource.MUTUAL_CONFIRMED
                for event in p102_recent_events
            ),
            "P102 has dormant history followed by a recent mutually confirmed analog event.",
            old_event_count=len(p102_old_events),
            recent_event_count=len(p102_recent_events),
        )
    )

    digital_only_events = _pair_events(
        dataset,
        people_by_code["P114"].id,
        people_by_code["P115"].id,
    )
    analog_only_events = _pair_events(
        dataset,
        people_by_code["P116"].id,
        people_by_code["P117"].id,
    )
    checks.extend(
        (
            _check(
                "DIGITAL_ONLY_CLOSE",
                bool(digital_only_events)
                and all(
                    event.channel is InteractionChannel.DIGITAL for event in digital_only_events
                ),
                "The digital-only fixture has direct evidence exclusively from digital channels.",
                event_count=len(digital_only_events),
            ),
            _check(
                "ANALOG_ONLY_CLOSE",
                bool(analog_only_events)
                and all(event.channel is InteractionChannel.ANALOG for event in analog_only_events),
                "The analog-only fixture has direct evidence exclusively from analog channels.",
                event_count=len(analog_only_events),
            ),
        )
    )

    p130 = people_by_code["P130"]
    p137 = people_by_code["P137"]
    shared_communities = _community_ids(dataset, p130.id) & _community_ids(dataset, p137.id)
    p140 = people_by_code["P140"]
    p147 = people_by_code["P147"]
    shared_activities = _activity_ids(dataset, p140.id) & _activity_ids(dataset, p147.id)
    checks.extend(
        (
            _check(
                "SAME_COMMUNITY_NO_INTERACTION",
                bool(shared_communities) and not _pair_events(dataset, p130.id, p137.id),
                "The community-only fixture shares context without direct interaction.",
                shared_community_count=len(shared_communities),
            ),
            _check(
                "SAME_ACTIVITY_NO_INTERACTION",
                bool(shared_activities) and not _pair_events(dataset, p140.id, p147.id),
                "The activity-only fixture shares context without direct interaction.",
                shared_activity_count=len(shared_activities),
            ),
        )
    )

    large_scenario = scenario_by_code.get("LARGE_EVENT_ONLY")
    large_group_ids = set(large_scenario.person_ids) if large_scenario is not None else set()
    events_with_multiple_large_group_people = [
        event
        for event in dataset.interaction_events
        if len(set(event.participant_ids) & large_group_ids) >= 2
    ]
    checks.append(
        _check(
            "LARGE_EVENT_ONLY",
            large_scenario is not None
            and len(events_with_multiple_large_group_people) == 1
            and set(events_with_multiple_large_group_people[0].participant_ids) == large_group_ids
            and events_with_multiple_large_group_people[0].type is InteractionType.COMMUNITY
            and events_with_multiple_large_group_people[0].conversation_participant_count
            == len(large_group_ids),
            "Large-group fixture members only co-occur in one explicit large community event.",
            participant_count=len(large_group_ids),
            shared_event_count=len(events_with_multiple_large_group_people),
        )
    )

    lunch_events = _pair_events(
        dataset,
        people_by_code["P118"].id,
        people_by_code["P119"].id,
    )
    checks.append(
        _check(
            "ONE_TO_ONE_LUNCH",
            any(
                event.type is InteractionType.LUNCH
                and event.channel is InteractionChannel.ANALOG
                and event.conversation_participant_count == 2
                for event in lunch_events
            ),
            "The lunch fixture contains an explicit analog one-to-one conversation.",
            pair_event_count=len(lunch_events),
        )
    )

    one_sided_events = _pair_events(
        dataset,
        people_by_code["P110"].id,
        people_by_code["P111"].id,
    )
    one_sided_initiators = {event.initiator_person_id for event in one_sided_events}
    checks.append(
        _check(
            "ONE_SIDED_DIRECTION",
            one_sided_initiators == {people_by_code["P110"].id},
            "The one-sided digital fixture has exactly one initiator.",
            initiator_count=len(one_sided_initiators),
        )
    )
    reciprocal_events = _pair_events(
        dataset,
        people_by_code["P112"].id,
        people_by_code["P113"].id,
    )
    reciprocal_initiators = {
        event.initiator_person_id
        for event in reciprocal_events
        if event.initiator_person_id is not None
    }
    checks.append(
        _check(
            "RECIPROCAL_DIRECTION",
            reciprocal_initiators == {people_by_code["P112"].id, people_by_code["P113"].id},
            "The reciprocal fixture contains directional evidence from both participants.",
            initiator_count=len(reciprocal_initiators),
        )
    )

    old_project_events = _pair_events(
        dataset,
        people_by_code["P150"].id,
        people_by_code["P151"].id,
    )
    completed_project_ids = {
        project.id
        for project in dataset.projects
        if project.ended_at is not None and project.ended_at < REFERENCE_TIME
    }
    completed_project_events = [
        event
        for event in old_project_events
        if event.project_id is not None
        and event.project_id in completed_project_ids
        and REFERENCE_TIME - event.occurred_at > timedelta(days=180)
    ]
    missing_analog_events = _pair_events(
        dataset,
        people_by_code["P152"].id,
        people_by_code["P153"].id,
    )
    checks.extend(
        (
            _check(
                "OLD_PROJECT",
                bool(completed_project_events),
                "The old-project fixture has old direct evidence tied to a completed project.",
                qualifying_event_count=len(completed_project_events),
            ),
            _check(
                "MISSING_ANALOG",
                bool(missing_analog_events)
                and all(
                    event.channel is InteractionChannel.DIGITAL for event in missing_analog_events
                ),
                "The missing-analog fixture has digital evidence and no analog event.",
                event_count=len(missing_analog_events),
            ),
        )
    )

    p201 = people_by_code["P201"]
    p202 = people_by_code["P202"]
    checks.append(
        _check(
            "NEW_JOINER_PERSONAS",
            REFERENCE_TIME - p201.joined_at == timedelta(days=30)
            and p201.hire_type is HireType.GRADUATE
            and REFERENCE_TIME - p202.joined_at == timedelta(days=45)
            and p202.hire_type is HireType.EXPERIENCED,
            "The graduate and experienced new-joiner fixtures have exact expected tenures.",
            p201_days_since_joining=(REFERENCE_TIME - p201.joined_at).days,
            p202_days_since_joining=(REFERENCE_TIME - p202.joined_at).days,
        )
    )

    p160 = people_by_code["P160"]
    p161 = people_by_code["P161"]
    shared_projects = _project_ids(dataset, p160.id) & _project_ids(dataset, p161.id)
    checks.append(
        _check(
            "MULTIPLE_ORG_CONTEXT",
            p160.primary_organization_unit_id != p161.primary_organization_unit_id
            and bool(shared_projects),
            "The cross-organization fixture shares explicit project context across primary units.",
            shared_project_count=len(shared_projects),
        )
    )

    checks.append(
        _check(
            "DUPLICATE_ANALOG",
            _duplicate_analog_fingerprints(dataset) >= 1,
            "At least one duplicate analog fingerprint is available for reconciliation tests.",
            duplicate_fingerprint_count=_duplicate_analog_fingerprints(dataset),
        )
    )
    p250_event_count = sum(
        people_by_code["P250"].id in event.participant_ids for event in dataset.interaction_events
    )
    checks.append(
        _check(
            "NO_NETWORK",
            p250_event_count == 0,
            "P250 has no interaction network.",
            event_count=p250_event_count,
        )
    )
    checks.append(
        _check(
            "LONG_NAME",
            len(people_by_code["P249"].display_name) > 60,
            "P249 exercises long-display-name rendering.",
            display_name_length=len(people_by_code["P249"].display_name),
        )
    )
    checks.append(
        _check(
            "MISSING_AVATAR",
            people_by_code["P248"].avatar_url is None,
            "P248 exercises the missing-avatar fallback.",
        )
    )
    synthetic_identities_only = all(
        person.display_name.startswith("Synthetic Person P")
        and all(
            identifier.source_system == "synthetic" and identifier.external_id.startswith("P")
            for identifier in person.external_identifiers
        )
        and (person.avatar_url is None or ".example.invalid/" in person.avatar_url)
        for person in dataset.people
    )
    checks.append(
        _check(
            "SYNTHETIC_IDENTITIES",
            synthetic_identities_only,
            "Every identity is obviously synthetic and every avatar uses a reserved domain.",
        )
    )
    forbidden_keys = sorted(collect_keys(dataset) & FORBIDDEN_KEYS)
    checks.append(
        _check(
            "PRIVACY_FIELDS",
            not forbidden_keys,
            "Synthetic facts contain no prohibited content or proximity fields.",
            forbidden_keys=forbidden_keys,
        )
    )

    for scenario in dataset.scenario_expectations:
        if (
            scenario.relationship_state_expectation is None
            and scenario.code != "P001_MIXED_RELATIONSHIPS"
        ):
            continue
        checks.append(
            ValidationCheck(
                code=f"RELATIONSHIP_ENGINE_{scenario.code}",
                status="PENDING_NC_004",
                message="Relationship-state derivation is intentionally deferred to NC-004.",
                details={"expected_assertion": scenario.expected_assertion},
            )
        )

    structural_checks_passed = all(check.status != "FAIL" for check in checks)
    return ValidationReport(
        family=dataset.family,
        dataset_version=dataset.dataset_version,
        seed=dataset.seed,
        structural_checks_passed=structural_checks_passed,
        checks=tuple(checks),
    )


def summarize_dataset(dataset: SyntheticDataset) -> DatasetSummary:
    organization_name_by_id = {
        organization.id: organization.name for organization in dataset.organization_units
    }
    organization_counts = Counter(
        organization_name_by_id[person.primary_organization_unit_id]
        for person in dataset.people
        if person.primary_organization_unit_id is not None
    )
    return DatasetSummary(
        family=dataset.family,
        dataset_version=dataset.dataset_version,
        seed=dataset.seed,
        counts={
            "activities": len(dataset.activities),
            "communities": len(dataset.communities),
            "interaction_events": len(dataset.interaction_events),
            "organization_units": len(dataset.organization_units),
            "people": len(dataset.people),
            "projects": len(dataset.projects),
            "scenario_expectations": len(dataset.scenario_expectations),
            "skills": len(dataset.skills),
        },
        organization_counts=dict(sorted(organization_counts.items())),
        scenario_codes=tuple(sorted(scenario.code for scenario in dataset.scenario_expectations)),
    )
