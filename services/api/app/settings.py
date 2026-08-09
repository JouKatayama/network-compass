import os
from dataclasses import dataclass
from enum import StrEnum


class ApiEnvironment(StrEnum):
    DEVELOPMENT = "development"
    TEST = "test"
    PRODUCTION = "production"


@dataclass(frozen=True, slots=True)
class ApiSettings:
    environment: ApiEnvironment = ApiEnvironment.DEVELOPMENT
    development_persona: str = "P001"
    cors_origins: tuple[str, ...] = ("http://localhost:3000",)

    @classmethod
    def from_environment(cls) -> "ApiSettings":
        environment_value = os.environ.get(
            "NETWORK_COMPASS_ENVIRONMENT",
            ApiEnvironment.DEVELOPMENT.value,
        ).strip()
        try:
            environment = ApiEnvironment(environment_value)
        except ValueError as error:
            raise ValueError(
                "NETWORK_COMPASS_ENVIRONMENT must be development, test, or production"
            ) from error
        persona = os.environ.get("NETWORK_COMPASS_DEVELOPMENT_PERSONA", "P001").strip()
        if not persona:
            raise ValueError("NETWORK_COMPASS_DEVELOPMENT_PERSONA must not be empty")
        origins = tuple(
            origin.strip()
            for origin in os.environ.get(
                "NETWORK_COMPASS_CORS_ORIGINS",
                "http://localhost:3000",
            ).split(",")
            if origin.strip()
        )
        if not origins:
            raise ValueError("NETWORK_COMPASS_CORS_ORIGINS must contain at least one origin")
        return cls(
            environment=environment,
            development_persona=persona,
            cors_origins=origins,
        )
