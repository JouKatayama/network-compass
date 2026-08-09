"""Pydantic boundary models."""

from app.models.domain import (
    DomainSchema,
    ExternalIdentifierSchema,
    InteractionEventSchema,
    PersonSchema,
)

__all__ = [
    "DomainSchema",
    "ExternalIdentifierSchema",
    "InteractionEventSchema",
    "PersonSchema",
]
