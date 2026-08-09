import argparse
import json
from datetime import UTC

from network_compass_synthetic.generator import DEFAULT_SEED, generate_dataset
from network_compass_synthetic.models import DatasetFamily, SyntheticDataset
from network_compass_synthetic.validation import validate_dataset

from app.application.persistence import DemoResetResult, DemoResetService
from app.domain.facts import CanonicalFactSet
from app.infrastructure.database import create_database_engine, create_session_factory
from app.infrastructure.persistence import (
    SqlAlchemyFactRepository,
    SqlAlchemyRelationshipProfileRepository,
)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Reset canonical facts and rebuild relationship profiles deterministically."
    )
    parser.add_argument("--family", choices=("demo", "edge_cases"), default="demo")
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
    return parser.parse_args()


def _canonical_facts(dataset: SyntheticDataset) -> CanonicalFactSet:
    return CanonicalFactSet(
        people=dataset.people,
        organization_units=dataset.organization_units,
        communities=dataset.communities,
        community_memberships=dataset.community_memberships,
        activities=dataset.activities,
        person_activities=dataset.person_activities,
        skills=dataset.skills,
        person_skills=dataset.person_skills,
        projects=dataset.projects,
        project_participations=dataset.project_participations,
        interaction_events=dataset.interaction_events,
    )


def _result_json(result: DemoResetResult) -> str:
    calculated_at = result.calculated_at.astimezone(UTC).isoformat().replace("+00:00", "Z")
    return (
        json.dumps(
            {
                "calculatedAt": calculated_at,
                "datasetVersion": result.dataset_version,
                "modelVersion": result.model_version,
                "relationshipProfileCount": result.relationship_profile_count,
                "seed": result.seed,
                "sourceCounts": dict(result.source_counts),
            },
            indent=2,
            sort_keys=True,
        )
        + "\n"
    )


def reset_database(family: DatasetFamily, *, seed: int) -> DemoResetResult:
    dataset = generate_dataset(family, seed=seed)
    report = validate_dataset(dataset)
    failed_checks = tuple(check.code for check in report.checks if check.status == "FAIL")
    if failed_checks:
        raise ValueError(f"synthetic dataset validation failed: {', '.join(failed_checks)}")

    engine = create_database_engine()
    session_factory = create_session_factory(engine)
    try:
        with session_factory() as session, session.begin():
            fact_repository = SqlAlchemyFactRepository(session)
            profile_repository = SqlAlchemyRelationshipProfileRepository(session)
            return DemoResetService(fact_repository, profile_repository).reset(
                _canonical_facts(dataset),
                dataset_version=dataset.dataset_version,
                seed=dataset.seed,
                calculated_at=dataset.generated_at,
            )
    finally:
        engine.dispose()


def main() -> None:
    args = _parse_args()
    family: DatasetFamily = args.family
    result = reset_database(family, seed=args.seed)
    print(_result_json(result), end="")


if __name__ == "__main__":
    main()
