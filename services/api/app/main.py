import logging
from collections.abc import AsyncIterator, Awaitable, Callable
from contextlib import asynccontextmanager
from uuid import uuid4

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.responses import Response

from app.api.errors import ApiError
from app.api.router import api_router
from app.application.people import InvalidSearchCursorError
from app.infrastructure.database import create_database_engine, create_session_factory
from app.settings import ApiSettings

LOGGER = logging.getLogger(__name__)


def _request_id(request: Request) -> str:
    request_id = getattr(request.state, "request_id", None)
    return request_id if isinstance(request_id, str) else f"req_{uuid4().hex}"


def _error_response(request: Request, *, status_code: int, code: str, message: str) -> JSONResponse:
    request_id = _request_id(request)
    return JSONResponse(
        status_code=status_code,
        content={
            "error": {
                "code": code,
                "message": message,
                "requestId": request_id,
            }
        },
        headers={"X-Request-ID": request_id},
    )


def create_app(
    *,
    settings: ApiSettings | None = None,
    session_factory: sessionmaker[Session] | None = None,
) -> FastAPI:
    active_settings = settings or ApiSettings.from_environment()
    owned_engine: Engine | None = None
    if session_factory is None:
        owned_engine = create_database_engine()
        active_session_factory = create_session_factory(owned_engine)
    else:
        active_session_factory = session_factory

    @asynccontextmanager
    async def lifespan(_: FastAPI) -> AsyncIterator[None]:
        try:
            yield
        finally:
            if owned_engine is not None:
                owned_engine.dispose()

    application = FastAPI(
        description="Person-first Network Compass API for Vertical Slice 001.",
        title="Network Compass API",
        version="0.1.0",
        lifespan=lifespan,
    )
    application.state.settings = active_settings
    application.state.session_factory = active_session_factory
    application.add_middleware(
        CORSMiddleware,
        allow_origins=list(active_settings.cors_origins),
        allow_credentials=True,
        allow_methods=["GET", "OPTIONS"],
        allow_headers=["Accept", "Content-Type", "X-Network-Compass-Persona"],
    )

    @application.middleware("http")
    async def attach_request_id(
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        request.state.request_id = f"req_{uuid4().hex}"
        response = await call_next(request)
        response.headers["X-Request-ID"] = request.state.request_id
        return response

    @application.exception_handler(ApiError)
    async def handle_api_error(request: Request, error: ApiError) -> JSONResponse:
        return _error_response(
            request,
            status_code=error.status_code,
            code=error.code,
            message=error.safe_message,
        )

    @application.exception_handler(InvalidSearchCursorError)
    async def handle_invalid_cursor(
        request: Request,
        _: InvalidSearchCursorError,
    ) -> JSONResponse:
        return _error_response(
            request,
            status_code=status.HTTP_400_BAD_REQUEST,
            code="INVALID_CURSOR",
            message="The search cursor is invalid.",
        )

    @application.exception_handler(RequestValidationError)
    async def handle_validation_error(
        request: Request,
        _: RequestValidationError,
    ) -> JSONResponse:
        return _error_response(
            request,
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            code="INVALID_REQUEST",
            message="One or more request parameters are invalid.",
        )

    @application.exception_handler(StarletteHTTPException)
    async def handle_http_error(
        request: Request,
        error: StarletteHTTPException,
    ) -> JSONResponse:
        code = "NOT_FOUND" if error.status_code == status.HTTP_404_NOT_FOUND else "HTTP_ERROR"
        message = (
            "The requested resource was not found."
            if error.status_code == status.HTTP_404_NOT_FOUND
            else "The request could not be completed."
        )
        return _error_response(
            request,
            status_code=error.status_code,
            code=code,
            message=message,
        )

    @application.exception_handler(Exception)
    async def handle_unexpected_error(request: Request, error: Exception) -> JSONResponse:
        LOGGER.error(
            "Unhandled API error request_id=%s",
            _request_id(request),
            exc_info=(type(error), error, error.__traceback__),
        )
        return _error_response(
            request,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            code="INTERNAL_ERROR",
            message="An unexpected error occurred.",
        )

    application.include_router(api_router)
    return application


app = create_app()
