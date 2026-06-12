from fastapi.testclient import TestClient

from weaver.api.main import app
from weaver.services.llm import parse_json_text


def test_parse_json_text_strips_fences() -> None:
    parsed = parse_json_text('```json\n{"ok": true}\n```')
    assert parsed == {"ok": True}


def test_llm_json_endpoint_unavailable_without_keys() -> None:
    client = TestClient(app)
    response = client.post(
        "/api/v1/llm/json",
        json={"system": "return json", "user": '{"a":1}', "max_tokens": 128},
    )
    assert response.status_code == 503
