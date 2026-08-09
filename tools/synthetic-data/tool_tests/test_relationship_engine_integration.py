from collections import Counter

import pytest
from network_compass_synthetic.generator import generate_dataset
from network_compass_synthetic.models import SyntheticDataset

from app.domain.entities import Person
from app.domain.enums import RelationshipState
from app.domain.relationship_engine import RelationshipEngine
from app.domain.relationships import EvidenceCoverage, RelationshipProfile
from app.domain.value_objects import PersonPair


@pytest.fixture(scope="module")
def demo_dataset() -> SyntheticDataset:
    return generate_dataset("demo")


def _person(dataset: SyntheticDataset, code: str) -> Person:
    return next(
        person
        for person in dataset.people
        if any(
            identifier.source_system == "synthetic" and identifier.external_id == code
            for identifier in person.external_identifiers
        )
    )


def _profile(
    dataset: SyntheticDataset,
    first_code: str,
    second_code: str,
    *,
    coverage: EvidenceCoverage | None = None,
) -> RelationshipProfile:
    profile = RelationshipEngine().derive_profile(
        PersonPair.between(
            _person(dataset, first_code).id,
            _person(dataset, second_code).id,
        ),
        dataset.interaction_events,
        calculated_at=dataset.generated_at,
        coverage=coverage,
    )
    assert profile is not None
    return profile


def test_hero_relationship_states_are_derived_from_synthetic_facts(
    demo_dataset: SyntheticDataset,
) -> None:
    assert _profile(demo_dataset, "P001", "P018").state is RelationshipState.DORMANT
    assert _profile(demo_dataset, "P001", "P102").state is RelationshipState.RECONNECTED

    p001 = _person(demo_dataset, "P001")
    counterpart_ids = {
        participant_id
        for event in demo_dataset.interaction_events
        if p001.id in event.participant_ids
        for participant_id in event.participant_ids
        if participant_id != p001.id
    }
    state_counts = Counter(
        profile.state
        for person_id in counterpart_ids
        if (
            profile := RelationshipEngine().derive_profile(
                PersonPair.between(p001.id, person_id),
                demo_dataset.interaction_events,
                calculated_at=demo_dataset.generated_at,
            )
        )
        is not None
    )

    assert {
        RelationshipState.CLOSE,
        RelationshipState.ACTIVE,
        RelationshipState.WEAK,
        RelationshipState.DORMANT,
        RelationshipState.RECONNECTED,
    }.issubset(state_counts)


def test_synthetic_channel_context_and_large_event_invariants(
    demo_dataset: SyntheticDataset,
) -> None:
    digital_only = _profile(demo_dataset, "P114", "P115")
    analog_only = _profile(demo_dataset, "P116", "P117")
    assert digital_only.state is RelationshipState.CLOSE
    assert digital_only.analog_evidence == 0.0
    assert analog_only.state is RelationshipState.CLOSE
    assert analog_only.digital_evidence == 0.0

    engine = RelationshipEngine()
    for first_code, second_code in (("P130", "P137"), ("P140", "P147")):
        assert (
            engine.derive_profile(
                PersonPair.between(
                    _person(demo_dataset, first_code).id,
                    _person(demo_dataset, second_code).id,
                ),
                demo_dataset.interaction_events,
                calculated_at=demo_dataset.generated_at,
            )
            is None
        )

    large_event_only = _profile(demo_dataset, "P120", "P122")
    assert large_event_only.state is RelationshipState.NEW
    assert large_event_only.relationship_strength < 0.05


def test_synthetic_direction_and_missing_analog_affect_expected_components(
    demo_dataset: SyntheticDataset,
) -> None:
    one_sided = _profile(demo_dataset, "P110", "P111")
    reciprocal = _profile(demo_dataset, "P112", "P113")
    assert one_sided.reciprocity == 0.0
    assert reciprocal.reciprocity > 0.8

    fully_observed = _profile(demo_dataset, "P152", "P153")
    analog_missing = _profile(
        demo_dataset,
        "P152",
        "P153",
        coverage=EvidenceCoverage(digital=1.0, analog=0.0),
    )
    assert analog_missing.relationship_strength == fully_observed.relationship_strength
    assert analog_missing.data_confidence < fully_observed.data_confidence
