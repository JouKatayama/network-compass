from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from hashlib import sha256
from uuid import UUID, uuid5

from app.domain.entities import (
    Activity,
    Community,
    CommunityMembership,
    OrganizationUnit,
    Person,
    PersonActivity,
    PersonSkill,
    ProjectContext,
    ProjectParticipation,
    Skill,
)
from app.domain.enums import (
    DurationBucket,
    HireType,
    InteractionChannel,
    InteractionSource,
    InteractionType,
    RelationshipState,
    Visibility,
)
from app.domain.interactions import InteractionEvent
from app.domain.value_objects import Confidence, ExternalIdentifier
from network_compass_synthetic.models import DatasetFamily, ScenarioExpectation, SyntheticDataset

DEFAULT_SEED = 20_260_809
DEMO_VERSION = "demo-v0.1.1"
DEMO_ID_VERSION = "demo-v0.1.0"
EDGE_CASES_VERSION = "edge-cases-v0.1.0"
REFERENCE_TIME = datetime(2026, 8, 9, 12, tzinfo=UTC)
UUID_NAMESPACE = UUID("f4526691-e3cd-5d9d-931c-283b814a9f4f")


@dataclass(frozen=True, slots=True)
class _OrganizationSpec:
    code: str
    name: str
    count: int


ORGANIZATION_SPECS = (
    _OrganizationSpec("TECH", "Technology / AI & Data", 80),
    _OrganizationSpec("STRATEGY", "Strategy", 35),
    _OrganizationSpec("INDUSTRY", "Industry", 45),
    _OrganizationSpec("OPERATIONS", "Operations", 30),
    _OrganizationSpec("PEOPLE", "HR / People", 20),
    _OrganizationSpec("GLOBAL", "Global / Regional", 25),
    _OrganizationSpec("CORPORATE", "Corporate / Other", 15),
)

COMMUNITY_NAMES = (
    "AI Builders",
    "Sustainability Circle",
    "New Joiner Community",
    "Design Practice",
    "Working Parents Network",
    "Regional Connectors",
    "Data Guild",
    "Facilitation Community",
)
ACTIVITY_NAMES = ("Cycling", "Running", "Coffee", "Photography", "Cooking", "Music")
SKILL_NAMES = (
    "Data Engineering",
    "Machine Learning",
    "Strategy",
    "Facilitation",
    "Service Design",
    "Operations",
    "People Development",
    "Cloud Architecture",
    "Sustainability",
    "Program Management",
)
ROLES = (
    "Data Consultant",
    "Strategy Consultant",
    "Industry Specialist",
    "Operations Consultant",
    "People Advisor",
    "Regional Coordinator",
    "Corporate Specialist",
)
CAREER_LEVELS = ("Analyst", "Consultant", "Manager", "Director")
LOCATIONS = ("Tokyo", "Osaka", "Fukuoka", "Sapporo", "Remote Japan")


def _stable_number(seed: int, key: str, modulus: int) -> int:
    digest = sha256(f"{seed}:{key}".encode()).digest()
    return int.from_bytes(digest[:8], "big") % modulus


def _stable_id(seed: int, version: str, kind: str, code: str) -> UUID:
    return uuid5(UUID_NAMESPACE, f"{version}:{seed}:{kind}:{code}")


def _person_code(index: int) -> str:
    return f"P{index:03d}"


class _DemoBuilder:
    def __init__(self, seed: int) -> None:
        self.seed = seed
        self.version = DEMO_VERSION
        self.id_version = DEMO_ID_VERSION
        self.organization_units = self._build_organization_units()
        self.organization_by_code = {
            specification.code: organization
            for specification, organization in zip(
                ORGANIZATION_SPECS,
                self.organization_units,
                strict=True,
            )
        }
        self.people = self._build_people()
        self.person_by_code = {
            _person_code(index): person for index, person in enumerate(self.people, start=1)
        }
        self.communities: tuple[Community, ...] = ()
        self.community_memberships: list[CommunityMembership] = []
        self.activities: tuple[Activity, ...] = ()
        self.person_activities: list[PersonActivity] = []
        self.skills: tuple[Skill, ...] = ()
        self.person_skills: list[PersonSkill] = []
        self.projects: tuple[ProjectContext, ...] = ()
        self.project_participations: list[ProjectParticipation] = []
        self.interaction_events: list[InteractionEvent] = []

    def build(self) -> SyntheticDataset:
        self._build_context_facts()
        self._build_interaction_facts()
        return SyntheticDataset(
            family="demo",
            dataset_version=self.version,
            seed=self.seed,
            generated_at=REFERENCE_TIME,
            people=self.people,
            organization_units=self.organization_units,
            communities=self.communities,
            community_memberships=tuple(self.community_memberships),
            activities=self.activities,
            person_activities=tuple(self.person_activities),
            skills=self.skills,
            person_skills=tuple(self.person_skills),
            projects=self.projects,
            project_participations=tuple(self.project_participations),
            interaction_events=tuple(self.interaction_events),
            scenario_expectations=self._build_scenario_expectations(),
        )

    def _id(self, kind: str, code: str) -> UUID:
        return _stable_id(self.seed, self.id_version, kind, code)

    def _build_organization_units(self) -> tuple[OrganizationUnit, ...]:
        return tuple(
            OrganizationUnit(
                id=self._id("organization", specification.code),
                name=specification.name,
            )
            for specification in ORGANIZATION_SPECS
        )

    def _organization_for_index(self, person_index: int) -> OrganizationUnit:
        upper_bound = 0
        for specification in ORGANIZATION_SPECS:
            upper_bound += specification.count
            if person_index <= upper_bound:
                return self.organization_by_code[specification.code]
        raise ValueError(f"person index outside organization composition: {person_index}")

    def _build_people(self) -> tuple[Person, ...]:
        people: list[Person] = []
        for index in range(1, 251):
            code = _person_code(index)
            organization = self._organization_for_index(index)
            if index == 201:
                days_since_joining = 30
                hire_type = HireType.GRADUATE
            elif index == 202:
                days_since_joining = 45
                hire_type = HireType.EXPERIENCED
            elif 201 <= index <= 225:
                days_since_joining = 20 + _stable_number(self.seed, f"joined:{code}", 151)
                hire_type = HireType.GRADUATE if index % 2 else HireType.EXPERIENCED
            else:
                days_since_joining = 365 + _stable_number(self.seed, f"joined:{code}", 1_461)
                hire_type = HireType.OTHER

            display_name = f"Synthetic Person {code}"
            if index == 249:
                display_name = (
                    "Synthetic Person P249 With An Intentionally Long Display Name For UI Testing"
                )
            avatar_url = (
                None
                if index in {53, 202, 248}
                else (f"https://avatars.example.invalid/{code.lower()}.svg")
            )
            people.append(
                Person(
                    id=self._id("person", code),
                    display_name=display_name,
                    joined_at=REFERENCE_TIME - timedelta(days=days_since_joining),
                    hire_type=hire_type,
                    primary_organization_unit_id=organization.id,
                    external_identifiers=(ExternalIdentifier("synthetic", code),),
                    role=ROLES[_stable_number(self.seed, f"role:{code}", len(ROLES))],
                    career_level=CAREER_LEVELS[
                        _stable_number(self.seed, f"level:{code}", len(CAREER_LEVELS))
                    ],
                    location=LOCATIONS[
                        _stable_number(self.seed, f"location:{code}", len(LOCATIONS))
                    ],
                    avatar_url=avatar_url,
                )
            )
        return tuple(people)

    def _build_context_facts(self) -> None:
        self.communities = tuple(
            Community(self._id("community", f"C{index:02d}"), name)
            for index, name in enumerate(COMMUNITY_NAMES, start=1)
        )
        self.activities = tuple(
            Activity(self._id("activity", f"A{index:02d}"), name)
            for index, name in enumerate(ACTIVITY_NAMES, start=1)
        )
        self.skills = tuple(
            Skill(self._id("skill", f"S{index:02d}"), name)
            for index, name in enumerate(SKILL_NAMES, start=1)
        )
        standard_projects = tuple(
            ProjectContext(
                id=self._id("project", f"PR{index:02d}"),
                name=f"Synthetic Project {index:02d}",
                started_at=REFERENCE_TIME - timedelta(days=1_000 - index * 35),
                ended_at=(
                    REFERENCE_TIME - timedelta(days=220 - index * 15) if index <= 6 else None
                ),
            )
            for index in range(1, 13)
        )
        self.projects = (
            *standard_projects,
            ProjectContext(
                id=self._id("project", "PR13"),
                name="Synthetic Project 13",
                started_at=REFERENCE_TIME - timedelta(days=600),
                ended_at=REFERENCE_TIME - timedelta(days=300),
            ),
        )

        for index, person in enumerate(self.people, start=1):
            if index == 250:
                continue
            community = self.communities[
                _stable_number(self.seed, f"community:{index}", len(self.communities))
            ]
            self._ensure_community_membership(person, community)
            if index % 11 == 0:
                secondary = self.communities[
                    (self.communities.index(community) + 3) % len(self.communities)
                ]
                self._ensure_community_membership(person, secondary)

            activity = self.activities[
                _stable_number(self.seed, f"activity:{index}", len(self.activities))
            ]
            self._ensure_person_activity(person, activity)
            for offset in (0, 4):
                skill = self.skills[
                    (_stable_number(self.seed, f"skill:{index}", len(self.skills)) + offset)
                    % len(self.skills)
                ]
                self._ensure_person_skill(person, skill)

        self._ensure_community_membership(self.person_by_code["P130"], self.communities[0])
        self._ensure_community_membership(self.person_by_code["P137"], self.communities[0])
        self._ensure_person_activity(self.person_by_code["P140"], self.activities[0])
        self._ensure_person_activity(self.person_by_code["P147"], self.activities[0])

        new_joiner_community = self.communities[2]
        for code in ("P201", *(_person_code(index) for index in range(203, 211))):
            self._ensure_community_membership(self.person_by_code[code], new_joiner_community)

        experienced_joiner = self.person_by_code["P202"]
        for community in (self.communities[0], self.communities[5]):
            self._ensure_community_membership(experienced_joiner, community)
        for skill in (self.skills[1], self.skills[2], self.skills[7], self.skills[9]):
            self._ensure_person_skill(experienced_joiner, skill)

        participation_keys: set[tuple[UUID, UUID]] = set()
        for project_index, project in enumerate(standard_projects, start=1):
            for offset in range(12):
                person_index = ((project_index * 17 + offset * 13) % 249) + 1
                person = self.people[person_index - 1]
                started_at = max(project.started_at, person.joined_at + timedelta(days=1))
                if project.ended_at is not None and started_at > project.ended_at:
                    continue
                key = (person.id, project.id)
                if key in participation_keys:
                    continue
                participation_keys.add(key)
                self.project_participations.append(
                    ProjectParticipation(
                        person_id=person.id,
                        project_id=project.id,
                        started_at=started_at,
                        ended_at=project.ended_at,
                    )
                )

        dormant_project = self.projects[12]
        for code in ("P001", "P018"):
            person = self.person_by_code[code]
            dormant_project_key = (person.id, dormant_project.id)
            self.project_participations.append(
                ProjectParticipation(
                    person_id=person.id,
                    project_id=dormant_project.id,
                    started_at=max(
                        dormant_project.started_at,
                        person.joined_at + timedelta(days=1),
                    ),
                    ended_at=dormant_project.ended_at,
                )
            )
            participation_keys.add(dormant_project_key)

        cross_unit_project = self.projects[11]
        for code in ("P160", "P161"):
            person = self.person_by_code[code]
            key = (person.id, cross_unit_project.id)
            if key not in participation_keys:
                self.project_participations.append(
                    ProjectParticipation(
                        person_id=person.id,
                        project_id=cross_unit_project.id,
                        started_at=max(
                            cross_unit_project.started_at,
                            person.joined_at + timedelta(days=1),
                        ),
                    )
                )
                participation_keys.add(key)

        cohort_project = self.projects[11]
        for code in ("P201", *(_person_code(index) for index in range(203, 211))):
            person = self.person_by_code[code]
            key = (person.id, cohort_project.id)
            if key in participation_keys:
                continue
            self.project_participations.append(
                ProjectParticipation(
                    person_id=person.id,
                    project_id=cohort_project.id,
                    started_at=max(
                        cohort_project.started_at,
                        person.joined_at + timedelta(days=1),
                    ),
                )
            )
            participation_keys.add(key)

        for project in self.projects[8:11]:
            key = (experienced_joiner.id, project.id)
            if key in participation_keys:
                continue
            self.project_participations.append(
                ProjectParticipation(
                    person_id=experienced_joiner.id,
                    project_id=project.id,
                    started_at=max(
                        project.started_at,
                        experienced_joiner.joined_at + timedelta(days=1),
                    ),
                )
            )
            participation_keys.add(key)

    def _ensure_community_membership(self, person: Person, community: Community) -> None:
        key = (person.id, community.id)
        if any(
            (membership.person_id, membership.community_id) == key
            for membership in self.community_memberships
        ):
            return
        self.community_memberships.append(
            CommunityMembership(
                person_id=person.id,
                community_id=community.id,
                joined_at=max(
                    person.joined_at + timedelta(days=1), REFERENCE_TIME - timedelta(days=500)
                ),
            )
        )

    def _ensure_person_activity(self, person: Person, activity: Activity) -> None:
        key = (person.id, activity.id)
        if any(
            (person_activity.person_id, person_activity.activity_id) == key
            for person_activity in self.person_activities
        ):
            return
        visibility = (Visibility.PRIVATE, Visibility.NETWORK, Visibility.ORGANIZATION)[
            _stable_number(self.seed, f"visibility:{person.id}:{activity.id}", 3)
        ]
        self.person_activities.append(
            PersonActivity(
                person_id=person.id,
                activity_id=activity.id,
                declared_at=max(
                    person.joined_at + timedelta(days=1), REFERENCE_TIME - timedelta(days=300)
                ),
                visibility=visibility,
            )
        )

    def _ensure_person_skill(self, person: Person, skill: Skill) -> None:
        key = (person.id, skill.id)
        if any(
            (person_skill.person_id, person_skill.skill_id) == key
            for person_skill in self.person_skills
        ):
            return
        self.person_skills.append(
            PersonSkill(
                person_id=person.id,
                skill_id=skill.id,
                declared_at=max(
                    person.joined_at + timedelta(days=1), REFERENCE_TIME - timedelta(days=450)
                ),
            )
        )

    def _add_event(
        self,
        *,
        code: str,
        participant_codes: tuple[str, ...],
        days_ago: int,
        channel: InteractionChannel,
        interaction_type: InteractionType,
        source: InteractionSource,
        confidence: float,
        duration_bucket: DurationBucket | None = None,
        conversation_participant_count: int | None = None,
        activity_id: UUID | None = None,
        community_id: UUID | None = None,
        project_id: UUID | None = None,
        initiator_code: str | None = None,
        created_by_code: str | None = None,
    ) -> None:
        participants = tuple(self.person_by_code[person_code] for person_code in participant_codes)
        desired_time = REFERENCE_TIME - timedelta(days=days_ago)
        earliest_time = max(person.joined_at for person in participants) + timedelta(days=1)
        occurred_at = max(desired_time, earliest_time)
        if occurred_at >= REFERENCE_TIME:
            occurred_at = REFERENCE_TIME - timedelta(minutes=10)
        self.interaction_events.append(
            InteractionEvent(
                id=self._id("interaction", code),
                occurred_at=occurred_at,
                channel=channel,
                type=interaction_type,
                participant_ids=tuple(person.id for person in participants),
                source=source,
                confidence=Confidence(confidence),
                created_at=occurred_at + timedelta(minutes=5),
                conversation_participant_count=(
                    conversation_participant_count or len(participants)
                ),
                duration_bucket=duration_bucket,
                activity_id=activity_id,
                community_id=community_id,
                project_id=project_id,
                initiator_person_id=(
                    self.person_by_code[initiator_code].id if initiator_code is not None else None
                ),
                created_by_person_id=(
                    self.person_by_code[created_by_code].id if created_by_code is not None else None
                ),
                source_system="synthetic" if channel is InteractionChannel.DIGITAL else None,
                external_event_id=code if channel is InteractionChannel.DIGITAL else None,
            )
        )

    def _add_pair_series(
        self,
        *,
        prefix: str,
        first_code: str,
        second_code: str,
        days: tuple[int, ...],
        channels: tuple[InteractionChannel, ...],
        project_id: UUID | None = None,
    ) -> None:
        for index, days_ago in enumerate(days, start=1):
            channel = channels[(index - 1) % len(channels)]
            is_analog = channel is InteractionChannel.ANALOG
            self._add_event(
                code=f"{prefix}-{index:02d}",
                participant_codes=(first_code, second_code),
                days_ago=days_ago,
                channel=channel,
                interaction_type=(
                    InteractionType.COFFEE if is_analog else InteractionType.TEAMS_CHAT
                ),
                source=(InteractionSource.SELF_REPORTED if is_analog else InteractionSource.SYSTEM),
                confidence=0.9 if is_analog else 0.8,
                duration_bucket=DurationBucket.MEDIUM,
                project_id=project_id,
                initiator_code=first_code,
                created_by_code=first_code if is_analog else None,
            )

    def _build_interaction_facts(self) -> None:
        for target_index in range(2, 41):
            target_code = _person_code(target_index)
            if target_index == 18:
                self._add_pair_series(
                    prefix="P001-P018-DORMANT",
                    first_code="P001",
                    second_code=target_code,
                    days=(570, 500, 440, 380, 330),
                    channels=(InteractionChannel.DIGITAL, InteractionChannel.ANALOG),
                    project_id=self.projects[12].id,
                )
            elif 2 <= target_index <= 9:
                self._add_pair_series(
                    prefix=f"P001-{target_code}-CLOSE",
                    first_code="P001",
                    second_code=target_code,
                    days=(5, 15, 25, 35, 45, 55),
                    channels=(InteractionChannel.DIGITAL, InteractionChannel.ANALOG),
                )
            elif target_index <= 25:
                self._add_pair_series(
                    prefix=f"P001-{target_code}-ACTIVE",
                    first_code="P001",
                    second_code=target_code,
                    days=(10, 40, 80),
                    channels=(InteractionChannel.DIGITAL, InteractionChannel.ANALOG),
                )
            else:
                self._add_pair_series(
                    prefix=f"P001-{target_code}-WEAK",
                    first_code="P001",
                    second_code=target_code,
                    days=(150 + target_index,),
                    channels=(InteractionChannel.DIGITAL,),
                )

        self._add_pair_series(
            prefix="P001-P102-RECONNECTED-OLD",
            first_code="P001",
            second_code="P102",
            days=(540, 470, 400, 330),
            channels=(InteractionChannel.DIGITAL, InteractionChannel.ANALOG),
        )
        self._add_event(
            code="P001-P102-RECONNECTED-COFFEE",
            participant_codes=("P001", "P102"),
            days_ago=4,
            channel=InteractionChannel.ANALOG,
            interaction_type=InteractionType.COFFEE,
            source=InteractionSource.MUTUAL_CONFIRMED,
            confidence=1.0,
            duration_bucket=DurationBucket.LONG,
            initiator_code="P001",
        )

        # Keep P001's direct set fixed while providing the specified 40-60 people at
        # exactly two hops. P067 deliberately uses P010 as its expected mutual path.
        for target_index in range(41, 91):
            gateway_index = 2 + ((target_index - 41) % 39)
            if target_index == 67:
                gateway_index = 10
            gateway_code = _person_code(gateway_index)
            target_code = _person_code(target_index)
            self._add_event(
                code=f"SECOND-HOP-{gateway_code}-{target_code}",
                participant_codes=(gateway_code, target_code),
                days_ago=20
                + _stable_number(
                    self.seed,
                    f"second-hop:{gateway_code}:{target_code}",
                    70,
                ),
                channel=InteractionChannel.DIGITAL,
                interaction_type=InteractionType.ONLINE_1ON1,
                source=InteractionSource.SYSTEM,
                confidence=0.75,
                initiator_code=gateway_code,
            )

        skipped_ring_pairs = {
            frozenset(("P116", "P117")),
            frozenset(("P150", "P151")),
        }
        lower_bound = 1
        for specification in ORGANIZATION_SPECS:
            upper_bound = lower_bound + specification.count - 1
            codes = [_person_code(index) for index in range(lower_bound, upper_bound + 1)]
            codes = [code for code in codes if code not in {"P018", "P250"}]
            for first_code, second_code in zip(codes, codes[1:], strict=False):
                if frozenset((first_code, second_code)) in skipped_ring_pairs:
                    continue
                self._add_event(
                    code=f"RING-{first_code}-{second_code}",
                    participant_codes=(first_code, second_code),
                    days_ago=15
                    + _stable_number(
                        self.seed,
                        f"ring:{first_code}:{second_code}",
                        75,
                    ),
                    channel=InteractionChannel.DIGITAL,
                    interaction_type=InteractionType.TEAMS_CHAT,
                    source=InteractionSource.SYSTEM,
                    confidence=0.7,
                    initiator_code=first_code,
                )
            lower_bound = upper_bound + 1

        for first_code, second_code in (
            ("P080", "P081"),
            ("P115", "P116"),
            ("P160", "P161"),
            ("P190", "P191"),
            ("P210", "P211"),
            ("P235", "P236"),
        ):
            self._add_event(
                code=f"BRIDGE-{first_code}-{second_code}",
                participant_codes=(first_code, second_code),
                days_ago=35,
                channel=InteractionChannel.DIGITAL,
                interaction_type=InteractionType.ONLINE_1ON1,
                source=InteractionSource.SYSTEM,
                confidence=0.85,
                initiator_code=first_code,
            )

        self._add_event(
            code="PATH-P010-P067",
            participant_codes=("P010", "P067"),
            days_ago=18,
            channel=InteractionChannel.DIGITAL,
            interaction_type=InteractionType.ONLINE_1ON1,
            source=InteractionSource.SYSTEM,
            confidence=0.9,
            initiator_code="P010",
        )
        self._add_pair_series(
            prefix="EDGE-DIGITAL-ONLY",
            first_code="P114",
            second_code="P115",
            days=(4, 12, 20, 28, 36, 44),
            channels=(InteractionChannel.DIGITAL,),
        )
        self._add_pair_series(
            prefix="EDGE-ANALOG-ONLY",
            first_code="P116",
            second_code="P117",
            days=(6, 16, 26, 36, 46, 56),
            channels=(InteractionChannel.ANALOG,),
        )
        for index in range(5):
            self._add_event(
                code=f"EDGE-ONE-SIDED-{index:02d}",
                participant_codes=("P110", "P111"),
                days_ago=8 + index * 9,
                channel=InteractionChannel.DIGITAL,
                interaction_type=InteractionType.TEAMS_CHAT,
                source=InteractionSource.SYSTEM,
                confidence=0.75,
                initiator_code="P110",
            )
        for index in range(6):
            initiator = "P112" if index % 2 == 0 else "P113"
            self._add_event(
                code=f"EDGE-RECIPROCAL-{index:02d}",
                participant_codes=("P112", "P113"),
                days_ago=7 + index * 8,
                channel=InteractionChannel.DIGITAL,
                interaction_type=InteractionType.TEAMS_CHAT,
                source=InteractionSource.SYSTEM,
                confidence=0.8,
                initiator_code=initiator,
            )
        self._add_event(
            code="EDGE-ONE-TO-ONE-LUNCH",
            participant_codes=("P118", "P119"),
            days_ago=12,
            channel=InteractionChannel.ANALOG,
            interaction_type=InteractionType.LUNCH,
            source=InteractionSource.MUTUAL_CONFIRMED,
            confidence=1.0,
            duration_bucket=DurationBucket.LONG,
            initiator_code="P118",
        )
        large_group = tuple(_person_code(index) for index in range(120, 160, 2))
        self._add_event(
            code="EDGE-LARGE-EVENT-ONLY",
            participant_codes=large_group,
            days_ago=25,
            channel=InteractionChannel.ANALOG,
            interaction_type=InteractionType.COMMUNITY,
            source=InteractionSource.SYSTEM,
            confidence=0.2,
            conversation_participant_count=len(large_group),
            community_id=self.communities[1].id,
        )
        self._add_event(
            code="EDGE-OLD-PROJECT",
            participant_codes=("P150", "P151"),
            days_ago=420,
            channel=InteractionChannel.DIGITAL,
            interaction_type=InteractionType.GROUP_MEETING,
            source=InteractionSource.SYSTEM,
            confidence=0.8,
            project_id=self.projects[0].id,
            initiator_code="P150",
        )
        self._add_pair_series(
            prefix="EDGE-MISSING-ANALOG",
            first_code="P152",
            second_code="P153",
            days=(10, 30, 60),
            channels=(InteractionChannel.DIGITAL,),
        )
        for suffix in ("A", "B"):
            self._add_event(
                code=f"EDGE-DUPLICATE-ANALOG-{suffix}",
                participant_codes=("P154", "P155"),
                days_ago=9,
                channel=InteractionChannel.ANALOG,
                interaction_type=InteractionType.COFFEE,
                source=InteractionSource.SELF_REPORTED,
                confidence=0.9,
                duration_bucket=DurationBucket.MEDIUM,
                activity_id=self.activities[2].id,
                initiator_code="P154",
                created_by_code="P154",
            )
        self._add_pair_series(
            prefix="NEW-JOINER-GRADUATE",
            first_code="P201",
            second_code="P203",
            days=(5, 12, 20),
            channels=(InteractionChannel.DIGITAL, InteractionChannel.ANALOG),
        )
        for cohort_index in range(204, 211):
            cohort_code = _person_code(cohort_index)
            self._add_pair_series(
                prefix=f"NEW-JOINER-COHORT-{cohort_code}",
                first_code="P201",
                second_code=cohort_code,
                days=(6 + (cohort_index - 204), 14 + (cohort_index - 204)),
                channels=(InteractionChannel.DIGITAL, InteractionChannel.ANALOG),
            )
        self._add_pair_series(
            prefix="NEW-JOINER-EXPERIENCED",
            first_code="P202",
            second_code="P211",
            days=(7, 18, 28),
            channels=(InteractionChannel.DIGITAL, InteractionChannel.ANALOG),
        )

    def _build_scenario_expectations(self) -> tuple[ScenarioExpectation, ...]:
        def person_id(code: str) -> UUID:
            return self.person_by_code[code].id

        large_group_ids = tuple(person_id(_person_code(index)) for index in range(120, 160, 2))
        scenarios = (
            ScenarioExpectation(
                "P001_MIXED_RELATIONSHIPS",
                "P001 has forty mixed evidence counterpart candidates",
                (person_id("P001"),),
                "NC-004 should derive a close/active/weak/dormant/reconnected mix from facts.",
            ),
            ScenarioExpectation(
                "P018_DORMANT",
                "P018 has strong old evidence and no recent direct event with P001",
                (person_id("P001"), person_id("P018")),
                "NC-004 should derive DORMANT.",
                RelationshipState.DORMANT,
            ),
            ScenarioExpectation(
                "P067_TWO_HOP",
                "P067 is reachable from P001 only through P010",
                (person_id("P001"), person_id("P010"), person_id("P067")),
                "No P001-P067 direct event exists; the expected path is P001-P010-P067.",
            ),
            ScenarioExpectation(
                "P102_RECONNECTED",
                "P102 has dormant history plus a recent confirmed coffee with P001",
                (person_id("P001"), person_id("P102")),
                "NC-004 should derive RECONNECTED.",
                RelationshipState.RECONNECTED,
            ),
            ScenarioExpectation(
                "DIGITAL_ONLY_CLOSE",
                "Digital-only close evidence",
                (person_id("P114"), person_id("P115")),
                "All direct evidence for this pair is digital.",
            ),
            ScenarioExpectation(
                "ANALOG_ONLY_CLOSE",
                "Analog-only close evidence",
                (person_id("P116"), person_id("P117")),
                "All direct evidence for this pair is analog.",
            ),
            ScenarioExpectation(
                "ONE_SIDED_DIGITAL",
                "Directional digital evidence from one initiator",
                (person_id("P110"), person_id("P111")),
                "Every directional event is initiated by P110.",
            ),
            ScenarioExpectation(
                "RECIPROCAL_DIGITAL",
                "Directional digital evidence from both participants",
                (person_id("P112"), person_id("P113")),
                "Both participants initiate directional events.",
            ),
            ScenarioExpectation(
                "SAME_COMMUNITY_NO_INTERACTION",
                "Shared community without a direct interaction",
                (person_id("P130"), person_id("P137")),
                "Shared context alone must not create a relationship.",
            ),
            ScenarioExpectation(
                "SAME_ACTIVITY_NO_INTERACTION",
                "Shared activity without a direct interaction",
                (person_id("P140"), person_id("P147")),
                "Shared context alone must not create a relationship.",
            ),
            ScenarioExpectation(
                "LARGE_EVENT_ONLY",
                "Large-event co-presence only",
                large_group_ids,
                "Large attendance alone should provide near-zero relationship evidence.",
            ),
            ScenarioExpectation(
                "ONE_TO_ONE_LUNCH",
                "Confirmed one-to-one lunch",
                (person_id("P118"), person_id("P119")),
                "The conversation participant count is two.",
            ),
            ScenarioExpectation(
                "OLD_PROJECT",
                "Old shared-project evidence",
                (person_id("P150"), person_id("P151")),
                "The direct event is old and tied to a completed project.",
            ),
            ScenarioExpectation(
                "MISSING_ANALOG",
                "Digital evidence with unknown analog coverage",
                (person_id("P152"), person_id("P153")),
                "Missing analog evidence affects confidence, not strength by fiat.",
            ),
            ScenarioExpectation(
                "DUPLICATE_ANALOG_ENTRY",
                "Duplicate analog-entry candidate",
                (person_id("P154"), person_id("P155")),
                "Validation identifies duplicate fingerprints without mutating raw events.",
            ),
            ScenarioExpectation(
                "GRADUATE_NEW_JOINER",
                "Graduate new joiner P201",
                (person_id("P201"),),
                "P201 joined thirty days before the dataset reference time.",
            ),
            ScenarioExpectation(
                "EXPERIENCED_NEW_JOINER",
                "Experienced new joiner P202",
                (person_id("P202"),),
                "P202 joined forty-five days before the dataset reference time.",
            ),
            ScenarioExpectation(
                "NO_NETWORK",
                "Person with no interaction network",
                (person_id("P250"),),
                "P250 has no InteractionEvent.",
            ),
            ScenarioExpectation(
                "MULTIPLE_ORG_CONTEXT",
                "Cross-organization project context",
                (person_id("P160"), person_id("P161")),
                "Participants from different primary units share an explicit project context.",
            ),
            ScenarioExpectation(
                "LONG_NAME",
                "Intentionally long synthetic display name",
                (person_id("P249"),),
                "The UI must handle the complete display name.",
            ),
            ScenarioExpectation(
                "MISSING_AVATAR",
                "Missing avatar fallback",
                (person_id("P248"),),
                "P248 has no avatar URL.",
            ),
        )
        return tuple(sorted(scenarios, key=lambda scenario: scenario.code))


def _build_edge_cases(demo: SyntheticDataset) -> SyntheticDataset:
    selected_person_ids = {
        person_id for scenario in demo.scenario_expectations for person_id in scenario.person_ids
    }
    people = tuple(person for person in demo.people if person.id in selected_person_ids)
    organization_ids = {
        person.primary_organization_unit_id
        for person in people
        if person.primary_organization_unit_id is not None
    }
    community_memberships = tuple(
        membership
        for membership in demo.community_memberships
        if membership.person_id in selected_person_ids
    )
    community_ids = {membership.community_id for membership in community_memberships}
    person_activities = tuple(
        person_activity
        for person_activity in demo.person_activities
        if person_activity.person_id in selected_person_ids
    )
    activity_ids = {person_activity.activity_id for person_activity in person_activities}
    person_skills = tuple(
        person_skill
        for person_skill in demo.person_skills
        if person_skill.person_id in selected_person_ids
    )
    skill_ids = {person_skill.skill_id for person_skill in person_skills}
    project_participations = tuple(
        participation
        for participation in demo.project_participations
        if participation.person_id in selected_person_ids
    )
    project_ids = {participation.project_id for participation in project_participations}
    interaction_events = tuple(
        event
        for event in demo.interaction_events
        if set(event.participant_ids).issubset(selected_person_ids)
    )
    community_ids.update(
        event.community_id for event in interaction_events if event.community_id is not None
    )
    activity_ids.update(
        event.activity_id for event in interaction_events if event.activity_id is not None
    )
    project_ids.update(
        event.project_id for event in interaction_events if event.project_id is not None
    )
    return SyntheticDataset(
        family="edge_cases",
        dataset_version=EDGE_CASES_VERSION,
        seed=demo.seed,
        generated_at=demo.generated_at,
        people=people,
        organization_units=tuple(
            unit for unit in demo.organization_units if unit.id in organization_ids
        ),
        communities=tuple(
            community for community in demo.communities if community.id in community_ids
        ),
        community_memberships=community_memberships,
        activities=tuple(activity for activity in demo.activities if activity.id in activity_ids),
        person_activities=person_activities,
        skills=tuple(skill for skill in demo.skills if skill.id in skill_ids),
        person_skills=person_skills,
        projects=tuple(project for project in demo.projects if project.id in project_ids),
        project_participations=project_participations,
        interaction_events=interaction_events,
        scenario_expectations=demo.scenario_expectations,
    )


def generate_dataset(
    family: DatasetFamily = "demo",
    *,
    seed: int = DEFAULT_SEED,
) -> SyntheticDataset:
    demo = _DemoBuilder(seed).build()
    if family == "demo":
        return demo
    if family == "edge_cases":
        return _build_edge_cases(demo)
    raise ValueError(f"unsupported dataset family: {family}")
