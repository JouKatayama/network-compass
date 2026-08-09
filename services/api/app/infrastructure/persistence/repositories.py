from collections import defaultdict
from collections.abc import Iterable, Mapping
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import delete, func, or_, select
from sqlalchemy.orm import Session

from app.domain.entities import OrganizationUnit, Person
from app.domain.enums import Visibility
from app.domain.facts import CanonicalFactSet
from app.domain.interactions import InteractionEvent
from app.domain.relationships import RelationshipContext, RelationshipProfile
from app.domain.value_objects import Confidence, ExternalIdentifier, PersonPair, normalize_utc
from app.infrastructure.persistence.models import (
    ActivityRecord,
    CommunityMembershipRecord,
    CommunityRecord,
    InteractionEventRecord,
    InteractionParticipantRecord,
    OrganizationUnitRecord,
    PersonActivityRecord,
    PersonExternalIdentifierRecord,
    PersonRecord,
    PersonSkillRecord,
    ProjectContextRecord,
    ProjectParticipationRecord,
    RelationshipProfileRecord,
    SkillRecord,
    UserRelationshipFeedbackRecord,
)


def _database_utc(value: datetime, *, field_name: str) -> datetime:
    aware = value.replace(tzinfo=UTC) if value.utcoffset() is None else value
    return normalize_utc(aware, field_name=field_name)


SOURCE_RECORD_TYPES = (
    OrganizationUnitRecord,
    PersonRecord,
    PersonExternalIdentifierRecord,
    CommunityRecord,
    CommunityMembershipRecord,
    ActivityRecord,
    PersonActivityRecord,
    SkillRecord,
    PersonSkillRecord,
    ProjectContextRecord,
    ProjectParticipationRecord,
    InteractionEventRecord,
    InteractionParticipantRecord,
    UserRelationshipFeedbackRecord,
)


class SqlAlchemyFactRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def clear_all(self) -> None:
        for record_type in (
            UserRelationshipFeedbackRecord,
            InteractionParticipantRecord,
            InteractionEventRecord,
            ProjectParticipationRecord,
            PersonSkillRecord,
            PersonActivityRecord,
            CommunityMembershipRecord,
            ProjectContextRecord,
            SkillRecord,
            ActivityRecord,
            CommunityRecord,
            PersonExternalIdentifierRecord,
            PersonRecord,
            OrganizationUnitRecord,
        ):
            self._session.execute(delete(record_type))

    def replace_all(self, facts: CanonicalFactSet) -> None:
        self.clear_all()
        self._session.add_all(
            OrganizationUnitRecord(id=item.id, name=item.name) for item in facts.organization_units
        )
        self._session.flush()
        self._session.add_all(
            PersonRecord(
                id=item.id,
                display_name=item.display_name,
                joined_at=item.joined_at,
                hire_type=item.hire_type,
                primary_organization_unit_id=item.primary_organization_unit_id,
                role=item.role,
                career_level=item.career_level,
                location=item.location,
                avatar_url=item.avatar_url,
            )
            for item in facts.people
        )
        self._session.flush()
        self._session.add_all(
            PersonExternalIdentifierRecord(
                person_id=person.id,
                source_system=identifier.source_system,
                external_id=identifier.external_id,
            )
            for person in facts.people
            for identifier in person.external_identifiers
        )
        self._session.flush()
        self._session.add_all(
            CommunityRecord(id=item.id, name=item.name) for item in facts.communities
        )
        self._session.flush()
        self._session.add_all(
            CommunityMembershipRecord(
                person_id=item.person_id,
                community_id=item.community_id,
                joined_at=item.joined_at,
                left_at=item.left_at,
            )
            for item in facts.community_memberships
        )
        self._session.flush()
        self._session.add_all(
            ActivityRecord(id=item.id, name=item.name) for item in facts.activities
        )
        self._session.flush()
        self._session.add_all(
            PersonActivityRecord(
                person_id=item.person_id,
                activity_id=item.activity_id,
                declared_at=item.declared_at,
                visibility=item.visibility,
            )
            for item in facts.person_activities
        )
        self._session.flush()
        self._session.add_all(SkillRecord(id=item.id, name=item.name) for item in facts.skills)
        self._session.flush()
        self._session.add_all(
            PersonSkillRecord(
                person_id=item.person_id,
                skill_id=item.skill_id,
                declared_at=item.declared_at,
            )
            for item in facts.person_skills
        )
        self._session.flush()
        self._session.add_all(
            ProjectContextRecord(
                id=item.id,
                name=item.name,
                started_at=item.started_at,
                ended_at=item.ended_at,
            )
            for item in facts.projects
        )
        self._session.flush()
        self._session.add_all(
            ProjectParticipationRecord(
                person_id=item.person_id,
                project_id=item.project_id,
                started_at=item.started_at,
                ended_at=item.ended_at,
            )
            for item in facts.project_participations
        )
        self._session.flush()
        self._session.add_all(
            InteractionEventRecord(
                id=item.id,
                occurred_at=item.occurred_at,
                channel=item.channel,
                type=item.type,
                source=item.source,
                confidence=item.confidence.value,
                created_at=item.created_at,
                conversation_participant_count=item.conversation_participant_count,
                duration_bucket=item.duration_bucket,
                activity_id=item.activity_id,
                community_id=item.community_id,
                project_id=item.project_id,
                initiator_person_id=item.initiator_person_id,
                created_by_person_id=item.created_by_person_id,
                source_system=item.source_system,
                external_event_id=item.external_event_id,
            )
            for item in facts.interaction_events
        )
        self._session.flush()
        self._session.add_all(
            InteractionParticipantRecord(
                interaction_event_id=event.id,
                person_id=person_id,
            )
            for event in facts.interaction_events
            for person_id in event.participant_ids
        )
        self._session.flush()
        self._session.add_all(
            UserRelationshipFeedbackRecord(
                id=item.id,
                person_a_id=item.pair.person_a_id,
                person_b_id=item.pair.person_b_id,
                created_by_person_id=item.created_by_person_id,
                created_at=item.created_at,
            )
            for item in facts.user_relationship_feedback
        )
        self._session.flush()

    def list_people(self) -> tuple[Person, ...]:
        identifier_rows = self._session.execute(
            select(PersonExternalIdentifierRecord).order_by(
                PersonExternalIdentifierRecord.person_id,
                PersonExternalIdentifierRecord.source_system,
                PersonExternalIdentifierRecord.external_id,
            )
        ).scalars()
        identifiers_by_person: dict[UUID, list[ExternalIdentifier]] = defaultdict(list)
        for row in identifier_rows:
            identifiers_by_person[row.person_id].append(
                ExternalIdentifier(row.source_system, row.external_id)
            )

        person_rows = self._session.execute(
            select(PersonRecord).order_by(PersonRecord.id)
        ).scalars()
        return tuple(
            Person(
                id=row.id,
                display_name=row.display_name,
                joined_at=_database_utc(row.joined_at, field_name="joined_at"),
                hire_type=row.hire_type,
                primary_organization_unit_id=row.primary_organization_unit_id,
                external_identifiers=tuple(identifiers_by_person[row.id]),
                role=row.role,
                career_level=row.career_level,
                location=row.location,
                avatar_url=row.avatar_url,
            )
            for row in person_rows
        )

    def list_organization_units(self) -> tuple[OrganizationUnit, ...]:
        rows = self._session.execute(
            select(OrganizationUnitRecord).order_by(OrganizationUnitRecord.id)
        ).scalars()
        return tuple(OrganizationUnit(id=row.id, name=row.name) for row in rows)

    def list_interaction_events(self) -> tuple[InteractionEvent, ...]:
        participant_rows = self._session.execute(
            select(InteractionParticipantRecord).order_by(
                InteractionParticipantRecord.interaction_event_id,
                InteractionParticipantRecord.person_id,
            )
        ).scalars()
        participants_by_event: dict[UUID, list[UUID]] = defaultdict(list)
        for row in participant_rows:
            participants_by_event[row.interaction_event_id].append(row.person_id)

        event_rows = self._session.execute(
            select(InteractionEventRecord).order_by(
                InteractionEventRecord.occurred_at,
                InteractionEventRecord.id,
            )
        ).scalars()
        return tuple(
            InteractionEvent(
                id=row.id,
                occurred_at=_database_utc(row.occurred_at, field_name="occurred_at"),
                channel=row.channel,
                type=row.type,
                participant_ids=tuple(participants_by_event[row.id]),
                source=row.source,
                confidence=Confidence(row.confidence),
                created_at=_database_utc(row.created_at, field_name="created_at"),
                conversation_participant_count=row.conversation_participant_count,
                duration_bucket=row.duration_bucket,
                activity_id=row.activity_id,
                community_id=row.community_id,
                project_id=row.project_id,
                initiator_person_id=row.initiator_person_id,
                created_by_person_id=row.created_by_person_id,
                source_system=row.source_system,
                external_event_id=row.external_event_id,
            )
            for row in event_rows
        )

    def relationship_contexts(
        self,
        pairs: Iterable[PersonPair],
        *,
        calculated_at: datetime,
    ) -> Mapping[PersonPair, RelationshipContext]:
        calculation_time = normalize_utc(calculated_at, field_name="calculated_at")
        canonical_pairs = tuple(pairs)

        organizations: dict[UUID, UUID | None] = {
            person_id: organization_id
            for person_id, organization_id in self._session.execute(
                select(PersonRecord.id, PersonRecord.primary_organization_unit_id)
            )
        }

        communities_by_person: dict[UUID, set[UUID]] = defaultdict(set)
        community_rows = self._session.execute(
            select(
                CommunityMembershipRecord.person_id,
                CommunityMembershipRecord.community_id,
            ).where(
                CommunityMembershipRecord.joined_at <= calculation_time,
                or_(
                    CommunityMembershipRecord.left_at.is_(None),
                    CommunityMembershipRecord.left_at >= calculation_time,
                ),
            )
        )
        for person_id, community_id in community_rows:
            communities_by_person[person_id].add(community_id)

        activities_by_person: dict[UUID, set[UUID]] = defaultdict(set)
        activity_rows = self._session.execute(
            select(PersonActivityRecord.person_id, PersonActivityRecord.activity_id).where(
                PersonActivityRecord.declared_at <= calculation_time,
                PersonActivityRecord.visibility != Visibility.PRIVATE,
            )
        )
        for person_id, activity_id in activity_rows:
            activities_by_person[person_id].add(activity_id)

        projects_by_person: dict[UUID, set[UUID]] = defaultdict(set)
        project_rows = self._session.execute(
            select(
                ProjectParticipationRecord.person_id,
                ProjectParticipationRecord.project_id,
            ).where(ProjectParticipationRecord.started_at <= calculation_time)
        )
        for person_id, project_id in project_rows:
            projects_by_person[person_id].add(project_id)

        return {
            pair: RelationshipContext(
                shared_community_count=len(
                    communities_by_person[pair.person_a_id]
                    & communities_by_person[pair.person_b_id]
                ),
                shared_activity_count=len(
                    activities_by_person[pair.person_a_id] & activities_by_person[pair.person_b_id]
                ),
                shared_project_count=len(
                    projects_by_person[pair.person_a_id] & projects_by_person[pair.person_b_id]
                ),
                same_primary_organization=(
                    organizations.get(pair.person_a_id) is not None
                    and organizations.get(pair.person_a_id) == organizations.get(pair.person_b_id)
                ),
            )
            for pair in canonical_pairs
        }

    def counts(self) -> dict[str, int]:
        return {
            record_type.__tablename__: self._session.scalar(
                select(func.count()).select_from(record_type)
            )
            or 0
            for record_type in SOURCE_RECORD_TYPES
        }


class SqlAlchemyRelationshipProfileRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def clear_all(self) -> None:
        self._session.execute(delete(RelationshipProfileRecord))

    def replace_all(self, profiles: Iterable[RelationshipProfile]) -> None:
        self.clear_all()
        self._session.add_all(
            RelationshipProfileRecord(
                person_a_id=profile.pair.person_a_id,
                person_b_id=profile.pair.person_b_id,
                current_activation=profile.current_activation,
                historical_depth=profile.historical_depth,
                digital_evidence=profile.digital_evidence,
                analog_evidence=profile.analog_evidence,
                social_context=profile.social_context,
                reciprocity=profile.reciprocity,
                channel_diversity=profile.channel_diversity,
                relationship_strength=profile.relationship_strength,
                state=profile.state,
                first_meaningful_interaction_at=profile.first_meaningful_interaction_at,
                last_meaningful_interaction_at=profile.last_meaningful_interaction_at,
                expected_cadence_days=profile.expected_cadence_days,
                dormancy_ratio=profile.dormancy_ratio,
                data_confidence=profile.data_confidence,
                model_version=profile.model_version,
                calculated_at=profile.calculated_at,
            )
            for profile in profiles
        )
        self._session.flush()

    def get(self, pair: PersonPair) -> RelationshipProfile | None:
        record = self._session.get(
            RelationshipProfileRecord,
            (pair.person_a_id, pair.person_b_id),
        )
        return self._to_domain(record) if record is not None else None

    def list_all(self) -> tuple[RelationshipProfile, ...]:
        records = self._session.execute(
            select(RelationshipProfileRecord).order_by(
                RelationshipProfileRecord.person_a_id,
                RelationshipProfileRecord.person_b_id,
            )
        ).scalars()
        return tuple(self._to_domain(record) for record in records)

    def count(self) -> int:
        return (
            self._session.scalar(select(func.count()).select_from(RelationshipProfileRecord)) or 0
        )

    @staticmethod
    def _to_domain(record: RelationshipProfileRecord) -> RelationshipProfile:
        return RelationshipProfile(
            pair=PersonPair(record.person_a_id, record.person_b_id),
            current_activation=record.current_activation,
            historical_depth=record.historical_depth,
            digital_evidence=record.digital_evidence,
            analog_evidence=record.analog_evidence,
            social_context=record.social_context,
            reciprocity=record.reciprocity,
            channel_diversity=record.channel_diversity,
            relationship_strength=record.relationship_strength,
            state=record.state,
            first_meaningful_interaction_at=_database_utc(
                record.first_meaningful_interaction_at,
                field_name="first_meaningful_interaction_at",
            ),
            last_meaningful_interaction_at=_database_utc(
                record.last_meaningful_interaction_at,
                field_name="last_meaningful_interaction_at",
            ),
            expected_cadence_days=record.expected_cadence_days,
            dormancy_ratio=record.dormancy_ratio,
            data_confidence=record.data_confidence,
            model_version=record.model_version,
            calculated_at=_database_utc(record.calculated_at, field_name="calculated_at"),
        )
