from typing import Any

from fastapi import APIRouter, Response, status

from app.api.dependencies import CurrentPersonId, DatabaseSession
from app.api.errors import ApiError
from app.application.interactions import (
    CaptureInteractionCommand,
    IdempotencyConflictError,
    InteractionCaptureService,
    InteractionPersonNotFoundError,
    InvalidInteractionError,
)
from app.infrastructure.database import transaction_boundary
from app.infrastructure.persistence.repositories import (
    SqlAlchemyFactRepository,
    SqlAlchemyRelationshipProfileRepository,
)
from app.models.errors import ErrorResponseSchema
from app.models.interactions import (
    InteractionCaptureRequestSchema,
    InteractionCaptureResultSchema,
)

router = APIRouter(prefix="/interactions", tags=["interactions"])

ERROR_RESPONSES: dict[int | str, dict[str, Any]] = {
    status.HTTP_400_BAD_REQUEST: {
        "model": ErrorResponseSchema,
        "description": "The interaction violates a frozen capture invariant.",
    },
    status.HTTP_401_UNAUTHORIZED: {
        "model": ErrorResponseSchema,
        "description": "Authentication or development persona is unavailable.",
    },
    status.HTTP_404_NOT_FOUND: {
        "model": ErrorResponseSchema,
        "description": "The other person is unavailable.",
    },
    status.HTTP_409_CONFLICT: {
        "model": ErrorResponseSchema,
        "description": "The idempotency identity was reused with different content.",
    },
    status.HTTP_422_UNPROCESSABLE_CONTENT: {
        "model": ErrorResponseSchema,
        "description": "The request shape or enum value is invalid.",
    },
    status.HTTP_500_INTERNAL_SERVER_ERROR: {
        "model": ErrorResponseSchema,
        "description": "Unexpected safe server error.",
    },
}

RESPONSES = {
    **ERROR_RESPONSES,
    status.HTTP_200_OK: {
        "model": InteractionCaptureResultSchema,
        "description": "The same interaction request was replayed without another write.",
    },
}


@router.post(
    "",
    response_model=InteractionCaptureResultSchema,
    responses=RESPONSES,
    status_code=status.HTTP_201_CREATED,
    summary="Capture a factual self-reported analog interaction",
)
def capture_interaction(
    request: InteractionCaptureRequestSchema,
    response: Response,
    current_person_id: CurrentPersonId,
    session: DatabaseSession,
) -> InteractionCaptureResultSchema:
    service = InteractionCaptureService(
        SqlAlchemyFactRepository(session),
        SqlAlchemyRelationshipProfileRepository(session),
        transaction=lambda: transaction_boundary(session),
    )
    try:
        result = service.capture(
            CaptureInteractionCommand(
                current_person_id=current_person_id,
                other_person_id=request.other_person_id,
                type=request.type,
                duration_bucket=request.duration_bucket,
                occurred_at=request.occurred_at,
                client_request_id=request.client_request_id,
            )
        )
    except InvalidInteractionError as error:
        raise ApiError(
            status.HTTP_400_BAD_REQUEST,
            "INVALID_INTERACTION",
            "The interaction could not be recorded with those details.",
        ) from error
    except InteractionPersonNotFoundError as error:
        raise ApiError(
            status.HTTP_404_NOT_FOUND,
            "PERSON_NOT_FOUND",
            "The requested person was not found.",
        ) from error
    except IdempotencyConflictError as error:
        raise ApiError(
            status.HTTP_409_CONFLICT,
            "IDEMPOTENCY_CONFLICT",
            "This interaction request was already used with different details.",
        ) from error

    response.status_code = status.HTTP_200_OK if result.replayed else status.HTTP_201_CREATED
    return InteractionCaptureResultSchema.model_validate(result)
