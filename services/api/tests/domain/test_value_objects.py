from math import inf, nan
from uuid import UUID

import pytest

from app.domain.value_objects import Confidence, ExternalIdentifier, PersonPair


def test_external_identifier_normalizes_system_and_surrounding_whitespace() -> None:
    identifier = ExternalIdentifier("  WorkDay  ", " Employee-007 ")

    assert identifier.source_system == "workday"
    assert identifier.external_id == "Employee-007"


@pytest.mark.parametrize(("source_system", "external_id"), [("", "123"), ("hr", "  ")])
def test_external_identifier_rejects_empty_parts(
    source_system: str,
    external_id: str,
) -> None:
    with pytest.raises(ValueError, match="must not be empty"):
        ExternalIdentifier(source_system, external_id)


def test_person_pair_has_one_canonical_order_for_either_input_order() -> None:
    lower = UUID(int=1)
    higher = UUID(int=2)

    assert PersonPair.between(lower, higher) == PersonPair.between(higher, lower)
    assert PersonPair.between(higher, lower).person_a_id == lower


def test_person_pair_rejects_self_relationship() -> None:
    person_id = UUID(int=1)

    with pytest.raises(ValueError, match="same person"):
        PersonPair.between(person_id, person_id)


@pytest.mark.parametrize("value", [-0.01, 1.01, inf, nan])
def test_confidence_rejects_values_outside_the_closed_unit_interval(value: float) -> None:
    with pytest.raises(ValueError, match="between 0 and 1"):
        Confidence(value)


@pytest.mark.parametrize("value", [0, 0.5, 1])
def test_confidence_accepts_the_closed_unit_interval(value: float) -> None:
    assert Confidence(value).value == float(value)
