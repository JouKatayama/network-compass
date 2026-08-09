from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from datetime import datetime
from itertools import combinations
from typing import Protocol

from app.domain.facts import CanonicalFactSet
from app.domain.interactions import InteractionEvent
from app.domain.relationship_engine import RelationshipEngine
from app.domain.relationships import RelationshipContext, RelationshipProfile
from app.domain.value_objects import PersonPair, normalize_utc


class RelationshipFactReader(Protocol):
    def list_interaction_events(self) -> tuple[InteractionEvent, ...]: ...

    def relationship_contexts(
        self,
        pairs: Iterable[PersonPair],
        *,
        calculated_at: datetime,
    ) -> Mapping[PersonPair, RelationshipContext]: ...


class RelationshipProfileStore(Protocol):
    def clear_all(self) -> None: ...

    def replace_all(self, profiles: Iterable[RelationshipProfile]) -> None: ...

    def count(self) -> int: ...


class FactStore(RelationshipFactReader, Protocol):
    def replace_all(self, facts: CanonicalFactSet) -> None: ...

    def counts(self) -> dict[str, int]: ...


class RelationshipRebuildService:
    def __init__(
        self,
        fact_reader: RelationshipFactReader,
        profile_store: RelationshipProfileStore,
        *,
        engine: RelationshipEngine | None = None,
    ) -> None:
        self._fact_reader = fact_reader
        self._profile_store = profile_store
        self._engine = engine or RelationshipEngine()

    @property
    def model_version(self) -> str:
        return self._engine.config.model_version

    def rebuild(self, *, calculated_at: datetime) -> tuple[RelationshipProfile, ...]:
        calculation_time = normalize_utc(calculated_at, field_name="calculated_at")
        events = self._fact_reader.list_interaction_events()
        pairs = {
            PersonPair.between(first_person_id, second_person_id)
            for event in events
            if event.occurred_at <= calculation_time
            for first_person_id, second_person_id in combinations(event.participant_ids, 2)
        }
        contexts = self._fact_reader.relationship_contexts(
            pairs,
            calculated_at=calculation_time,
        )
        profiles = self._engine.derive_profiles(
            events,
            calculated_at=calculation_time,
            contexts=contexts,
        )
        self._profile_store.replace_all(profiles)
        return profiles


@dataclass(frozen=True, slots=True)
class DemoResetResult:
    dataset_version: str
    seed: int
    calculated_at: datetime
    model_version: str
    source_counts: tuple[tuple[str, int], ...]
    relationship_profile_count: int


class DemoResetService:
    def __init__(
        self,
        fact_store: FactStore,
        profile_store: RelationshipProfileStore,
    ) -> None:
        self._fact_store = fact_store
        self._profile_store = profile_store
        self._rebuild_service = RelationshipRebuildService(fact_store, profile_store)

    def reset(
        self,
        facts: CanonicalFactSet,
        *,
        dataset_version: str,
        seed: int,
        calculated_at: datetime,
    ) -> DemoResetResult:
        calculation_time = normalize_utc(calculated_at, field_name="calculated_at")
        self._profile_store.clear_all()
        self._fact_store.replace_all(facts)
        profiles = self._rebuild_service.rebuild(calculated_at=calculation_time)
        return DemoResetResult(
            dataset_version=dataset_version,
            seed=seed,
            calculated_at=calculation_time,
            model_version=self._rebuild_service.model_version,
            source_counts=tuple(sorted(self._fact_store.counts().items())),
            relationship_profile_count=len(profiles),
        )
