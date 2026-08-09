from datetime import datetime
from uuid import UUID

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    UniqueConstraint,
    Uuid,
)
from sqlalchemy import (
    Enum as SqlEnum,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.domain.enums import (
    DurationBucket,
    HireType,
    InteractionChannel,
    InteractionSource,
    InteractionType,
    RelationshipState,
    Visibility,
)
from app.infrastructure.database import Base

HIRE_TYPE_ENUM = SqlEnum(
    HireType,
    name="hire_type",
    native_enum=False,
    create_constraint=True,
    validate_strings=True,
    length=16,
)
VISIBILITY_ENUM = SqlEnum(
    Visibility,
    name="visibility",
    native_enum=False,
    create_constraint=True,
    validate_strings=True,
    length=16,
)
INTERACTION_CHANNEL_ENUM = SqlEnum(
    InteractionChannel,
    name="interaction_channel",
    native_enum=False,
    create_constraint=True,
    validate_strings=True,
    length=16,
)
INTERACTION_TYPE_ENUM = SqlEnum(
    InteractionType,
    name="interaction_type",
    native_enum=False,
    create_constraint=True,
    validate_strings=True,
    length=24,
)
INTERACTION_SOURCE_ENUM = SqlEnum(
    InteractionSource,
    name="interaction_source",
    native_enum=False,
    create_constraint=True,
    validate_strings=True,
    length=24,
)
DURATION_BUCKET_ENUM = SqlEnum(
    DurationBucket,
    name="duration_bucket",
    native_enum=False,
    create_constraint=True,
    validate_strings=True,
    length=16,
)
RELATIONSHIP_STATE_ENUM = SqlEnum(
    RelationshipState,
    name="relationship_state",
    native_enum=False,
    create_constraint=True,
    validate_strings=True,
    length=16,
)


class OrganizationUnitRecord(Base):
    __tablename__ = "organization_units"

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)


class PersonRecord(Base):
    __tablename__ = "people"

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True)
    display_name: Mapped[str] = mapped_column(String(255), nullable=False)
    joined_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    hire_type: Mapped[HireType] = mapped_column(HIRE_TYPE_ENUM, nullable=False)
    primary_organization_unit_id: Mapped[UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("organization_units.id", ondelete="SET NULL"),
        nullable=True,
    )
    role: Mapped[str | None] = mapped_column(String(255), nullable=True)
    career_level: Mapped[str | None] = mapped_column(String(255), nullable=True)
    location: Mapped[str | None] = mapped_column(String(255), nullable=True)
    avatar_url: Mapped[str | None] = mapped_column(String(2048), nullable=True)

    __table_args__ = (Index("ix_people_primary_organization", "primary_organization_unit_id"),)


class PersonExternalIdentifierRecord(Base):
    __tablename__ = "person_external_identifiers"

    person_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("people.id", ondelete="CASCADE"),
        primary_key=True,
    )
    source_system: Mapped[str] = mapped_column(String(100), primary_key=True)
    external_id: Mapped[str] = mapped_column(String(255), primary_key=True)

    __table_args__ = (
        UniqueConstraint(
            "source_system",
            "external_id",
            name="uq_person_external_identifiers_source_external",
        ),
    )


class CommunityRecord(Base):
    __tablename__ = "communities"

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)


class CommunityMembershipRecord(Base):
    __tablename__ = "community_memberships"

    person_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("people.id", ondelete="CASCADE"),
        primary_key=True,
    )
    community_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("communities.id", ondelete="CASCADE"),
        primary_key=True,
    )
    joined_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    left_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        CheckConstraint(
            "left_at IS NULL OR left_at >= joined_at",
            name="membership_interval",
        ),
    )


class ActivityRecord(Base):
    __tablename__ = "activities"

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)


class PersonActivityRecord(Base):
    __tablename__ = "person_activities"

    person_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("people.id", ondelete="CASCADE"),
        primary_key=True,
    )
    activity_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("activities.id", ondelete="CASCADE"),
        primary_key=True,
    )
    declared_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    visibility: Mapped[Visibility] = mapped_column(VISIBILITY_ENUM, nullable=False)


class SkillRecord(Base):
    __tablename__ = "skills"

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)


class PersonSkillRecord(Base):
    __tablename__ = "person_skills"

    person_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("people.id", ondelete="CASCADE"),
        primary_key=True,
    )
    skill_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("skills.id", ondelete="CASCADE"),
        primary_key=True,
    )
    declared_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class ProjectContextRecord(Base):
    __tablename__ = "project_contexts"

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        CheckConstraint(
            "ended_at IS NULL OR ended_at >= started_at",
            name="project_interval",
        ),
    )


class ProjectParticipationRecord(Base):
    __tablename__ = "project_participations"

    person_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("people.id", ondelete="CASCADE"),
        primary_key=True,
    )
    project_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("project_contexts.id", ondelete="CASCADE"),
        primary_key=True,
    )
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        CheckConstraint(
            "ended_at IS NULL OR ended_at >= started_at",
            name="participation_interval",
        ),
    )


class InteractionEventRecord(Base):
    __tablename__ = "interaction_events"

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    channel: Mapped[InteractionChannel] = mapped_column(
        INTERACTION_CHANNEL_ENUM,
        nullable=False,
    )
    type: Mapped[InteractionType] = mapped_column(INTERACTION_TYPE_ENUM, nullable=False)
    source: Mapped[InteractionSource] = mapped_column(INTERACTION_SOURCE_ENUM, nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    conversation_participant_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    duration_bucket: Mapped[DurationBucket | None] = mapped_column(
        DURATION_BUCKET_ENUM,
        nullable=True,
    )
    activity_id: Mapped[UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("activities.id"),
        nullable=True,
    )
    community_id: Mapped[UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("communities.id"),
        nullable=True,
    )
    project_id: Mapped[UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("project_contexts.id"),
        nullable=True,
    )
    initiator_person_id: Mapped[UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("people.id"),
        nullable=True,
    )
    created_by_person_id: Mapped[UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("people.id"),
        nullable=True,
    )
    source_system: Mapped[str | None] = mapped_column(String(100), nullable=True)
    external_event_id: Mapped[str | None] = mapped_column(String(255), nullable=True)

    __table_args__ = (
        CheckConstraint("confidence >= 0 AND confidence <= 1", name="confidence_unit"),
        CheckConstraint("created_at >= occurred_at", name="created_after_occurrence"),
        CheckConstraint(
            "conversation_participant_count IS NULL OR conversation_participant_count >= 2",
            name="conversation_participants_minimum",
        ),
        CheckConstraint(
            "(source_system IS NULL AND external_event_id IS NULL) OR "
            "(source_system IS NOT NULL AND external_event_id IS NOT NULL)",
            name="source_identifier_complete",
        ),
        UniqueConstraint(
            "source_system",
            "external_event_id",
            name="uq_interaction_events_source_external",
        ),
        Index("ix_interaction_events_occurred_at", "occurred_at"),
    )


class InteractionParticipantRecord(Base):
    __tablename__ = "interaction_participants"

    interaction_event_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("interaction_events.id", ondelete="CASCADE"),
        primary_key=True,
    )
    person_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("people.id", ondelete="CASCADE"),
        primary_key=True,
    )

    __table_args__ = (Index("ix_interaction_participants_person", "person_id"),)


class UserRelationshipFeedbackRecord(Base):
    __tablename__ = "user_relationship_feedback"

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True)
    person_a_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("people.id", ondelete="CASCADE"),
        nullable=False,
    )
    person_b_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("people.id", ondelete="CASCADE"),
        nullable=False,
    )
    created_by_person_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("people.id", ondelete="CASCADE"),
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    __table_args__ = (
        CheckConstraint("person_a_id < person_b_id", name="canonical_pair"),
        CheckConstraint(
            "created_by_person_id = person_a_id OR created_by_person_id = person_b_id",
            name="creator_in_pair",
        ),
        Index(
            "ix_user_relationship_feedback_pair",
            "person_a_id",
            "person_b_id",
        ),
    )


class RelationshipProfileRecord(Base):
    __tablename__ = "relationship_profiles"

    person_a_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("people.id", ondelete="CASCADE"),
        primary_key=True,
    )
    person_b_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("people.id", ondelete="CASCADE"),
        primary_key=True,
    )
    current_activation: Mapped[float] = mapped_column(Float, nullable=False)
    historical_depth: Mapped[float] = mapped_column(Float, nullable=False)
    digital_evidence: Mapped[float] = mapped_column(Float, nullable=False)
    analog_evidence: Mapped[float] = mapped_column(Float, nullable=False)
    social_context: Mapped[float] = mapped_column(Float, nullable=False)
    reciprocity: Mapped[float] = mapped_column(Float, nullable=False)
    channel_diversity: Mapped[float] = mapped_column(Float, nullable=False)
    relationship_strength: Mapped[float] = mapped_column(Float, nullable=False)
    state: Mapped[RelationshipState] = mapped_column(RELATIONSHIP_STATE_ENUM, nullable=False)
    first_meaningful_interaction_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
    last_meaningful_interaction_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
    expected_cadence_days: Mapped[float] = mapped_column(Float, nullable=False)
    dormancy_ratio: Mapped[float] = mapped_column(Float, nullable=False)
    data_confidence: Mapped[float] = mapped_column(Float, nullable=False)
    model_version: Mapped[str] = mapped_column(String(100), nullable=False)
    calculated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    __table_args__ = (
        CheckConstraint("person_a_id < person_b_id", name="canonical_pair"),
        CheckConstraint(
            "current_activation >= 0 AND current_activation <= 1",
            name="current_activation_unit",
        ),
        CheckConstraint(
            "historical_depth >= 0 AND historical_depth <= 1",
            name="historical_depth_unit",
        ),
        CheckConstraint(
            "digital_evidence >= 0 AND digital_evidence <= 1",
            name="digital_evidence_unit",
        ),
        CheckConstraint(
            "analog_evidence >= 0 AND analog_evidence <= 1",
            name="analog_evidence_unit",
        ),
        CheckConstraint(
            "social_context >= 0 AND social_context <= 1",
            name="social_context_unit",
        ),
        CheckConstraint("reciprocity >= 0 AND reciprocity <= 1", name="reciprocity_unit"),
        CheckConstraint(
            "channel_diversity >= 0 AND channel_diversity <= 1",
            name="channel_diversity_unit",
        ),
        CheckConstraint(
            "relationship_strength >= 0 AND relationship_strength <= 1",
            name="relationship_strength_unit",
        ),
        CheckConstraint(
            "data_confidence >= 0 AND data_confidence <= 1",
            name="data_confidence_unit",
        ),
        CheckConstraint("expected_cadence_days > 0", name="positive_cadence"),
        CheckConstraint("dormancy_ratio >= 0", name="nonnegative_dormancy"),
        CheckConstraint(
            "first_meaningful_interaction_at <= last_meaningful_interaction_at",
            name="meaningful_interval",
        ),
        CheckConstraint(
            "last_meaningful_interaction_at <= calculated_at",
            name="calculated_after_interaction",
        ),
        Index("ix_relationship_profiles_state", "state"),
        Index("ix_relationship_profiles_model_version", "model_version"),
    )
