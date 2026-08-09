from typing import Annotated, Any
from uuid import UUID

from fastapi import APIRouter, Path, Query, status

from app.api.dependencies import CurrentPersonId, DatabaseSession
from app.api.errors import ApiError
from app.application.people import (
    PeopleQueryService,
    PersonNotFoundError,
    PersonSearchCriteria,
)
from app.infrastructure.persistence.repositories import (
    SqlAlchemyFactRepository,
    SqlAlchemyRelationshipProfileRepository,
)
from app.models.errors import ErrorResponseSchema
from app.models.people import PersonDetailSchema, PersonSearchPageSchema

router = APIRouter(prefix="/people", tags=["people"])

ERROR_RESPONSES: dict[int | str, dict[str, Any]] = {
    status.HTTP_400_BAD_REQUEST: {
        "model": ErrorResponseSchema,
        "description": "The cursor or search request is invalid.",
    },
    status.HTTP_401_UNAUTHORIZED: {
        "model": ErrorResponseSchema,
        "description": "Authentication or development persona is unavailable.",
    },
    status.HTTP_404_NOT_FOUND: {
        "model": ErrorResponseSchema,
        "description": "The requested person was not found.",
    },
    status.HTTP_422_UNPROCESSABLE_CONTENT: {
        "model": ErrorResponseSchema,
        "description": "A path or query parameter is invalid.",
    },
    status.HTTP_500_INTERNAL_SERVER_ERROR: {
        "model": ErrorResponseSchema,
        "description": "Unexpected safe server error.",
    },
}


def _service(session: DatabaseSession) -> PeopleQueryService:
    return PeopleQueryService(
        SqlAlchemyFactRepository(session),
        SqlAlchemyRelationshipProfileRepository(session),
    )


@router.get(
    "/search",
    response_model=PersonSearchPageSchema,
    responses=ERROR_RESPONSES,
    summary="Search people with current-person-relative context",
)
def search_people(
    current_person_id: CurrentPersonId,
    session: DatabaseSession,
    q: Annotated[str, Query(min_length=1, max_length=100)],
    limit: Annotated[int, Query(ge=1, le=50)] = 20,
    cursor: Annotated[str | None, Query(max_length=2048)] = None,
    organization_id: Annotated[UUID | None, Query(alias="organizationId")] = None,
    community_id: Annotated[UUID | None, Query(alias="communityId")] = None,
    activity_id: Annotated[UUID | None, Query(alias="activityId")] = None,
    skill_id: Annotated[UUID | None, Query(alias="skillId")] = None,
) -> PersonSearchPageSchema:
    page = _service(session).search(
        current_person_id,
        PersonSearchCriteria(
            query=q,
            limit=limit,
            cursor=cursor,
            organization_id=organization_id,
            community_id=community_id,
            activity_id=activity_id,
            skill_id=skill_id,
        ),
    )
    return PersonSearchPageSchema.model_validate(page)


@router.get(
    "/{personId}",
    response_model=PersonDetailSchema,
    responses=ERROR_RESPONSES,
    summary="Get person detail relative to the current person",
)
def get_person_detail(
    person_id: Annotated[UUID, Path(alias="personId")],
    current_person_id: CurrentPersonId,
    session: DatabaseSession,
) -> PersonDetailSchema:
    try:
        detail = _service(session).get_detail(current_person_id, person_id)
    except PersonNotFoundError as error:
        raise ApiError(
            status.HTTP_404_NOT_FOUND,
            "PERSON_NOT_FOUND",
            "The requested person was not found.",
        ) from error
    return PersonDetailSchema.model_validate(detail)
