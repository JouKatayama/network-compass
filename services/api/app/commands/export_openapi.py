import argparse
import json
from pathlib import Path

from app.main import app

DEFAULT_OUTPUT = Path(__file__).resolve().parents[4] / "packages" / "contracts" / "openapi.json"


def canonical_openapi_json() -> str:
    return json.dumps(app.openapi(), ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Write or verify the canonical FastAPI OpenAPI file."
    )
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--check", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    output: Path = args.output
    rendered = canonical_openapi_json()
    if args.check:
        if not output.exists() or output.read_text() != rendered:
            raise SystemExit(f"OpenAPI artifact is out of date: {output}")
        print(f"OpenAPI artifact is current: {output}")
        return
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(rendered)
    print(f"Wrote OpenAPI artifact: {output}")


if __name__ == "__main__":
    main()
