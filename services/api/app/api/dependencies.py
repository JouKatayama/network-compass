from collections.abc import Iterator
from typing import Annotated
from uuid import UUID

from fastapi import Depends, Header, Request, status
from sqlalchemy.orm import Session

from app.api.errors import ApiError
from app.infrastructure.persistence.repositories import SqlAlchemyFactRepository
from app.settings import ApiEnvironment, ApiSettings


def get_session(request: Request) -> Iterator[Session]:
    with request.app.state.session_factory() as session:
        yield session


DatabaseSession = Annotated[Session, Depends(get_session)]


def resolve_current_person_id(
    request: Request,
    session: DatabaseSession,
    development_persona: Annotated[
        str | None,
        Header(
            alias="X-Network-Compass-Persona",
            description="Development/test-only synthetic persona external ID, for example P001.",
            max_length=32,
        ),
    ] = None,
) -> UUID:
    settings: ApiSettings = request.app.state.settings
    if settings.environment is ApiEnvironment.PRODUCTION:
        raise ApiError(
            status.HTTP_401_UNAUTHORIZED,
            "AUTHENTICATION_REQUIRED",
            "Authentication is required.",
        )

    external_id = (development_persona or settings.development_persona).strip()
    if not external_id:
        raise ApiError(
            status.HTTP_401_UNAUTHORIZED,
            "INVALID_DEVELOPMENT_PERSONA",
            "The development persona is not available.",
        )
    for person in SqlAlchemyFactRepository(session).list_people():
        if any(
            identifier.source_system == "synthetic" and identifier.external_id == external_id
            for identifier in person.external_identifiers
        ):
            return person.id
    raise ApiError(
        status.HTTP_401_UNAUTHORIZED,
        "INVALID_DEVELOPMENT_PERSONA",
        "The development persona is not available.",
    )


CurrentPersonId = Annotated[UUID, Depends(resolve_current_person_id)]
