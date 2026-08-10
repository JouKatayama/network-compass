from typing import Literal
from uuid import UUID

from pydantic import AwareDatetime

from app.domain.enums import DurationBucket, InteractionType
from app.models.domain import DomainSchema

AnalogCaptureType = Literal[
    InteractionType.OFFICE_CHAT,
    InteractionType.COFFEE,
    InteractionType.LUNCH,
    InteractionType.DINNER,
    InteractionType.COMMUNITY,
    InteractionType.ACTIVITY,
    InteractionType.OTHER,
]


class InteractionCaptureRequestSchema(DomainSchema):
    client_request_id: UUID
    other_person_id: UUID
    type: AnalogCaptureType
    duration_bucket: DurationBucket
    occurred_at: AwareDatetime


class InteractionCaptureResultSchema(DomainSchema):
    interaction_id: UUID
    other_person_id: UUID
    occurred_at: AwareDatetime
    type: AnalogCaptureType
    duration_bucket: DurationBucket
    replayed: bool
