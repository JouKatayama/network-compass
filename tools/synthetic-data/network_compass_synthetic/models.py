from dataclasses import dataclass
from datetime import datetime
from typing import Literal
from uuid import UUID

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
from app.domain.enums import RelationshipState
from app.domain.interactions import InteractionEvent

type DatasetFamily = Literal["demo", "edge_cases"]
type CheckStatus = Literal["PASS", "FAIL"]


@dataclass(frozen=True, slots=True)
class ScenarioExpectation:
    code: str
    title: str
    person_ids: tuple[UUID, ...]
    expected_assertion: str
    relationship_state_expectation: RelationshipState | None = None


@dataclass(frozen=True, slots=True)
class SyntheticDataset:
    family: DatasetFamily
    dataset_version: str
    seed: int
    generated_at: datetime
    people: tuple[Person, ...]
    organization_units: tuple[OrganizationUnit, ...]
    communities: tuple[Community, ...]
    community_memberships: tuple[CommunityMembership, ...]
    activities: tuple[Activity, ...]
    person_activities: tuple[PersonActivity, ...]
    skills: tuple[Skill, ...]
    person_skills: tuple[PersonSkill, ...]
    projects: tuple[ProjectContext, ...]
    project_participations: tuple[ProjectParticipation, ...]
    interaction_events: tuple[InteractionEvent, ...]
    scenario_expectations: tuple[ScenarioExpectation, ...]


@dataclass(frozen=True, slots=True)
class ValidationCheck:
    code: str
    status: CheckStatus
    message: str
    details: dict[str, object]


@dataclass(frozen=True, slots=True)
class ValidationReport:
    family: DatasetFamily
    dataset_version: str
    seed: int
    structural_checks_passed: bool
    checks: tuple[ValidationCheck, ...]


@dataclass(frozen=True, slots=True)
class DatasetSummary:
    family: DatasetFamily
    dataset_version: str
    seed: int
    counts: dict[str, int]
    organization_counts: dict[str, int]
    scenario_codes: tuple[str, ...]
