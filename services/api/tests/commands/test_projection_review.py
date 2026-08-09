from collections.abc import Iterator

import pytest
from network_compass_synthetic.generator import generate_dataset
from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session

from app.application.persistence import DemoResetService
from app.commands.demo_reset import _canonical_facts
from app.commands.projection_review import build_review_artifact, review_artifact_json
from app.infrastructure.database import Base
from app.infrastructure.persistence import (
    SqlAlchemyFactRepository,
    SqlAlchemyRelationshipProfileRepository,
)


@pytest.fixture(scope="module")
def database_engine() -> Iterator[Engine]:
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    dataset = generate_dataset("demo")
    with Session(engine) as session, session.begin():
        facts = SqlAlchemyFactRepository(session)
        profiles = SqlAlchemyRelationshipProfileRepository(session)
        DemoResetService(facts, profiles).reset(
            _canonical_facts(dataset),
            dataset_version=dataset.dataset_version,
            seed=dataset.seed,
            calculated_at=dataset.generated_at,
        )
    yield engine
    Base.metadata.drop_all(engine)
    engine.dispose()


def test_p001_review_artifact_is_deterministic_and_gate_b_ready(
    database_engine: Engine,
) -> None:
    with Session(database_engine) as session:
        first = build_review_artifact(
            SqlAlchemyFactRepository(session),
            SqlAlchemyRelationshipProfileRepository(session),
        )
        second = build_review_artifact(
            SqlAlchemyFactRepository(session),
            SqlAlchemyRelationshipProfileRepository(session),
        )

    assert review_artifact_json(first) == review_artifact_json(second)
    review = first["review"]
    assert isinstance(review, dict)
    assert review["bounds"] == {
        "defaultOneHopLimit": 24,
        "defaultTeaserLimit": 12,
        "hardVisibleLimit": 80,
        "oneHopWithinLimit": True,
        "teaserWithinLimit": True,
        "visibleWithinHardLimit": True,
    }
    assert review["heroPathAvailable"] is True
    hero = review["heroFixtures"]
    assert isinstance(hero, dict)
    assert hero["P018"] == {
        "hop": 1,
        "relationshipState": "DORMANT",
        "visible": True,
    }
    assert hero["P067"] == {
        "hop": 2,
        "shortestPaths": [["P001", "P010", "P067"]],
        "visible": True,
    }
    privacy = review["privacy"]
    assert isinstance(privacy, dict)
    assert privacy["focalRelativeMetricsOnlyOnDirectEdges"] is True
    assert privacy["thirdPartyPathMetricsOmitted"] is True
