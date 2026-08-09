import json
from dataclasses import replace
from datetime import timedelta
from pathlib import Path
from uuid import UUID

import pytest
from network_compass_synthetic.generator import DEFAULT_SEED, REFERENCE_TIME, generate_dataset
from network_compass_synthetic.models import SyntheticDataset
from network_compass_synthetic.serialization import canonical_json, write_outputs
from network_compass_synthetic.validation import summarize_dataset, validate_dataset

from app.domain.entities import Person


@pytest.fixture(scope="module")
def demo_dataset() -> SyntheticDataset:
    return generate_dataset("demo")


def person_by_code(dataset: SyntheticDataset, code: str) -> Person:
    for person in dataset.people:
        if any(
            identifier.source_system == "synthetic" and identifier.external_id == code
            for identifier in person.external_identifiers
        ):
            return person
    raise AssertionError(f"missing synthetic person {code}")


def pair_event_count(dataset: SyntheticDataset, first_id: UUID, second_id: UUID) -> int:
    expected = {first_id, second_id}
    return sum(
        len(event.participant_ids) == 2 and set(event.participant_ids) == expected
        for event in dataset.interaction_events
    )


def test_fixed_seed_is_byte_reproducible_and_seed_changes_output() -> None:
    first = canonical_json(generate_dataset("demo", seed=DEFAULT_SEED))
    second = canonical_json(generate_dataset("demo", seed=DEFAULT_SEED))
    changed = canonical_json(generate_dataset("demo", seed=DEFAULT_SEED + 1))

    assert first == second
    assert first != changed


def test_demo_has_exact_composition_and_primary_personas(
    demo_dataset: SyntheticDataset,
) -> None:
    summary = summarize_dataset(demo_dataset)

    assert summary.counts["people"] == 250
    assert summary.organization_counts == {
        "Corporate / Other": 15,
        "Global / Regional": 25,
        "HR / People": 20,
        "Industry": 45,
        "Operations": 30,
        "Strategy": 35,
        "Technology / AI & Data": 80,
    }
    assert person_by_code(demo_dataset, "P201").hire_type.value == "GRADUATE"
    assert person_by_code(demo_dataset, "P202").hire_type.value == "EXPERIENCED"


def test_p001_has_forty_counterparts_and_p067_has_only_expected_two_hop_path(
    demo_dataset: SyntheticDataset,
) -> None:
    p001 = person_by_code(demo_dataset, "P001")
    p010 = person_by_code(demo_dataset, "P010")
    p067 = person_by_code(demo_dataset, "P067")
    counterparts = {
        participant_id
        for event in demo_dataset.interaction_events
        if p001.id in event.participant_ids and len(event.participant_ids) == 2
        for participant_id in event.participant_ids
        if participant_id != p001.id
    }
    graph: dict[UUID, set[UUID]] = {person.id: set() for person in demo_dataset.people}
    for event in demo_dataset.interaction_events:
        for person_id in event.participant_ids:
            graph[person_id].update(set(event.participant_ids) - {person_id})
    exactly_two_hop: set[UUID] = set()
    for counterpart_id in counterparts:
        exactly_two_hop.update(graph[counterpart_id])
    exactly_two_hop.difference_update(counterparts | {p001.id})

    assert len(counterparts) == 40
    assert 40 <= len(exactly_two_hop) <= 60
    assert pair_event_count(demo_dataset, p001.id, p067.id) == 0
    assert pair_event_count(demo_dataset, p001.id, p010.id) > 0
    assert pair_event_count(demo_dataset, p010.id, p067.id) > 0


def test_structural_validation_passes_and_relationship_state_stays_pending(
    demo_dataset: SyntheticDataset,
) -> None:
    report = validate_dataset(demo_dataset)

    assert report.structural_checks_passed
    assert all(check.status != "FAIL" for check in report.checks)
    pending_codes = {check.code for check in report.checks if check.status == "PENDING_NC_004"}
    assert pending_codes == {
        "RELATIONSHIP_ENGINE_P001_MIXED_RELATIONSHIPS",
        "RELATIONSHIP_ENGINE_P018_DORMANT",
        "RELATIONSHIP_ENGINE_P102_RECONNECTED",
    }
    passed_codes = {check.code for check in report.checks if check.status == "PASS"}
    assert {
        "ANALOG_ONLY_CLOSE",
        "DIGITAL_ONLY_CLOSE",
        "LARGE_EVENT_ONLY",
        "LONG_NAME",
        "MISSING_ANALOG",
        "MULTIPLE_ORG_CONTEXT",
        "NEW_JOINER_PERSONAS",
        "P001_MIXED_FACT_PATTERN",
        "P001_TWO_HOP_REACH",
        "P201_GRADUATE_PERSONA",
        "P202_EXPERIENCED_PERSONA",
        "P018_DORMANT_FACT_PATTERN",
        "P102_RECONNECTED_FACT_PATTERN",
        "SAME_ACTIVITY_NO_INTERACTION",
        "SAME_COMMUNITY_NO_INTERACTION",
        "SYNTHETIC_IDENTITIES",
    }.issubset(passed_codes)


def test_validator_rejects_interaction_before_joined_at(
    demo_dataset: SyntheticDataset,
) -> None:
    p001 = person_by_code(demo_dataset, "P001")
    invalid_p001 = replace(p001, joined_at=REFERENCE_TIME - timedelta(minutes=1))
    invalid_dataset = replace(
        demo_dataset,
        people=tuple(
            invalid_p001 if person.id == p001.id else person for person in demo_dataset.people
        ),
    )

    report = validate_dataset(invalid_dataset)
    joined_at_check = next(check for check in report.checks if check.code == "AC-S10")

    assert not report.structural_checks_passed
    assert joined_at_check.status == "FAIL"
    assert joined_at_check.details["offending_event_ids"]


def test_edge_case_family_is_compact_and_keeps_every_scenario() -> None:
    demo = generate_dataset("demo")
    edge_cases = generate_dataset("edge_cases")

    assert len(edge_cases.people) < len(demo.people)
    assert {scenario.code for scenario in edge_cases.scenario_expectations} == {
        scenario.code for scenario in demo.scenario_expectations
    }
    assert validate_dataset(edge_cases).structural_checks_passed


def test_person_identity_edge_states_and_directional_fixtures(
    demo_dataset: SyntheticDataset,
) -> None:
    assert person_by_code(demo_dataset, "P248").avatar_url is None
    assert len(person_by_code(demo_dataset, "P249").display_name) > 60
    p250_id = person_by_code(demo_dataset, "P250").id
    assert all(p250_id not in event.participant_ids for event in demo_dataset.interaction_events)

    p110 = person_by_code(demo_dataset, "P110")
    p111 = person_by_code(demo_dataset, "P111")
    one_sided_initiators = {
        event.initiator_person_id
        for event in demo_dataset.interaction_events
        if set(event.participant_ids) == {p110.id, p111.id}
    }
    assert one_sided_initiators == {p110.id}


def test_output_writer_emits_dataset_summary_and_validation_report(
    demo_dataset: SyntheticDataset,
    tmp_path: Path,
) -> None:
    report = validate_dataset(demo_dataset)
    summary = summarize_dataset(demo_dataset)

    paths = write_outputs(demo_dataset, summary, report, tmp_path)

    assert set(paths) == {"dataset", "summary", "validation_report"}
    assert json.loads(paths["summary"].read_text(encoding="utf-8"))["counts"]["people"] == 250
    assert json.loads(paths["validation_report"].read_text(encoding="utf-8"))[
        "structuralChecksPassed"
    ]
