from typing import Any

from fastapi import APIRouter, status

from app.api.dependencies import CurrentPersonId, DatabaseSession
from app.api.errors import ApiError
from app.application.network_projection import PersonalNetworkProjectionQueryService
from app.infrastructure.persistence.repositories import (
    SqlAlchemyFactRepository,
    SqlAlchemyRelationshipProfileRepository,
)
from app.models.errors import ErrorResponseSchema
from app.models.network import GraphExpansionRequestSchema, GraphProjectionSchema

router = APIRouter(prefix="/me", tags=["network"])

ERROR_RESPONSES: dict[int | str, dict[str, Any]] = {
    status.HTTP_401_UNAUTHORIZED: {
        "model": ErrorResponseSchema,
        "description": "Authentication or development persona is unavailable.",
    },
    status.HTTP_422_UNPROCESSABLE_CONTENT: {
        "model": ErrorResponseSchema,
        "description": "The development persona header is invalid.",
    },
    status.HTTP_500_INTERNAL_SERVER_ERROR: {
        "model": ErrorResponseSchema,
        "description": "Unexpected safe server error.",
    },
}

EXPANSION_ERROR_RESPONSES = {
    **ERROR_RESPONSES,
    status.HTTP_400_BAD_REQUEST: {
        "model": ErrorResponseSchema,
        "description": "The expansion history or selected person is invalid.",
    },
}


@router.get(
    "/network",
    response_model=GraphProjectionSchema,
    response_model_exclude_none=True,
    responses=ERROR_RESPONSES,
    summary="Get the current person's network projection",
)
def get_current_network(
    current_person_id: CurrentPersonId,
    session: DatabaseSession,
) -> GraphProjectionSchema:
    facts = SqlAlchemyFactRepository(session)
    profiles = SqlAlchemyRelationshipProfileRepository(session)
    projection = PersonalNetworkProjectionQueryService(facts, profiles).get_for_current_user(
        current_person_id
    )
    return GraphProjectionSchema.from_domain(projection)


@router.post(
    "/network/expand",
    response_model=GraphProjectionSchema,
    response_model_exclude_none=True,
    responses=EXPANSION_ERROR_RESPONSES,
    summary="Expand the current person's authorized network projection",
)
def expand_current_network(
    request: GraphExpansionRequestSchema,
    current_person_id: CurrentPersonId,
    session: DatabaseSession,
) -> GraphProjectionSchema:
    facts = SqlAlchemyFactRepository(session)
    profiles = SqlAlchemyRelationshipProfileRepository(session)
    service = PersonalNetworkProjectionQueryService(facts, profiles)
    try:
        projection = service.expand_from_history_for_current_user(
            current_person_id,
            expanded_from_person_ids=request.expanded_from_person_ids,
            selected_person_id=request.selected_person_id,
        )
    except ValueError as error:
        raise ApiError(
            status.HTTP_400_BAD_REQUEST,
            "INVALID_NETWORK_EXPANSION",
            "The requested network expansion is not available.",
        ) from error
    return GraphProjectionSchema.from_domain(projection)
