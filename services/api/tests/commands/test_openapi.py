import json
from pathlib import Path

from app.commands.export_openapi import DEFAULT_OUTPUT, canonical_openapi_json


def test_openapi_artifact_is_current_and_scoped_to_nc007() -> None:
    rendered = canonical_openapi_json()
    assert Path(DEFAULT_OUTPUT).read_text() == rendered
    document = json.loads(rendered)

    assert set(document["paths"]) == {
        "/health",
        "/api/v1/me/network",
        "/api/v1/people/{personId}",
        "/api/v1/people/search",
    }
    for path in (
        "/api/v1/me/network",
        "/api/v1/people/{personId}",
        "/api/v1/people/search",
    ):
        operation = document["paths"][path]["get"]
        parameters = operation["parameters"]
        assert any(parameter["name"] == "X-Network-Compass-Persona" for parameter in parameters)
        for error_status in ("401", "422", "500"):
            response_schema = operation["responses"][error_status]["content"]["application/json"][
                "schema"
            ]
            assert response_schema == {"$ref": "#/components/schemas/ErrorResponseSchema"}

    serialized = json.dumps(document)
    for later_path in (
        "/me/recommendations",
        "/interactions",
        "/me/network-ramp",
        "/me/networking-profile",
        "/me/home",
    ):
        assert later_path not in serialized
