import argparse
from pathlib import Path

from network_compass_synthetic.generator import DEFAULT_SEED, generate_dataset
from network_compass_synthetic.models import DatasetFamily
from network_compass_synthetic.serialization import canonical_json, write_outputs
from network_compass_synthetic.validation import summarize_dataset, validate_dataset


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate deterministic Network Compass facts")
    parser.add_argument(
        "--family",
        choices=("demo", "edge_cases"),
        default="demo",
    )
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
    parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    family: DatasetFamily = args.family
    dataset = generate_dataset(family, seed=args.seed)
    report = validate_dataset(dataset)
    summary = summarize_dataset(dataset)
    paths = write_outputs(dataset, summary, report, args.output)
    print(canonical_json({"outputs": paths, "summary": summary}, pretty=True), end="")
    if not report.structural_checks_passed:
        raise SystemExit(1)
