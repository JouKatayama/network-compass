import json
import re
from dataclasses import fields, is_dataclass
from datetime import UTC, datetime
from enum import Enum
from pathlib import Path
from typing import cast
from uuid import UUID

from app.domain.value_objects import Confidence
from network_compass_synthetic.models import DatasetSummary, SyntheticDataset, ValidationReport


def _camel_case(value: str) -> str:
    head, *tail = value.split("_")
    return head + "".join(part.capitalize() for part in tail)


def to_primitive(value: object) -> object:
    if isinstance(value, Confidence):
        return value.value
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, UUID):
        return str(value)
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, datetime):
        normalized = value.astimezone(UTC).isoformat()
        return normalized.replace("+00:00", "Z")
    if is_dataclass(value) and not isinstance(value, type):
        return {
            _camel_case(field.name): to_primitive(getattr(value, field.name))
            for field in fields(value)
        }
    if isinstance(value, dict):
        return {str(key): to_primitive(item) for key, item in sorted(value.items())}
    if isinstance(value, (tuple, list)):
        return [to_primitive(item) for item in value]
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    raise TypeError(f"cannot serialize value of type {type(value).__name__}")


def canonical_json(value: object, *, pretty: bool = False) -> str:
    primitive = to_primitive(value)
    if pretty:
        return json.dumps(primitive, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    return (
        json.dumps(
            primitive,
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        )
        + "\n"
    )


def write_outputs(
    dataset: SyntheticDataset,
    summary: DatasetSummary,
    report: ValidationReport,
    output_directory: Path,
) -> dict[str, Path]:
    output_directory.mkdir(parents=True, exist_ok=True)
    paths = {
        "dataset": output_directory / "dataset.json",
        "summary": output_directory / "summary.json",
        "validation_report": output_directory / "validation-report.json",
    }
    paths["dataset"].write_text(canonical_json(dataset, pretty=True), encoding="utf-8")
    paths["summary"].write_text(canonical_json(summary, pretty=True), encoding="utf-8")
    paths["validation_report"].write_text(
        canonical_json(report, pretty=True),
        encoding="utf-8",
    )
    return paths


def collect_keys(value: object) -> set[str]:
    primitive = to_primitive(value)
    keys: set[str] = set()

    def visit(item: object) -> None:
        if isinstance(item, dict):
            mapping = cast(dict[str, object], item)
            for key, child in mapping.items():
                keys.add(re.sub(r"[^a-z0-9]", "", key.casefold()))
                visit(child)
        elif isinstance(item, list):
            for child in cast(list[object], item):
                visit(child)

    visit(primitive)
    return keys
