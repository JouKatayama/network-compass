"""SQLAlchemy persistence adapters for canonical facts and derived profiles."""

from app.infrastructure.persistence.repositories import (
    SqlAlchemyFactRepository,
    SqlAlchemyRelationshipProfileRepository,
)

__all__ = [
    "SqlAlchemyFactRepository",
    "SqlAlchemyRelationshipProfileRepository",
]
