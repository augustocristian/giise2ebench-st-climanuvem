import asyncio

from app.infrastructure.ollama_client import OllamaClient
from app.infrastructure.config import reset_settings_cache


def test_extract_predictions_accepts_string_predictions():
    client = OllamaClient()

    predictions = client._extract_predictions({"predictions": ["cumulus"]})

    assert predictions == [{"label": "cumulus", "confidence": 0.0}]


def test_extract_predictions_accepts_single_prediction_object():
    client = OllamaClient()

    predictions = client._extract_predictions(
        {"predictions": {"label": "cirrus", "confidence": "0.8"}}
    )

    assert predictions == [{"label": "cirrus", "confidence": 0.8}]


def test_extract_predictions_ignores_invalid_items():
    client = OllamaClient()

    predictions = client._extract_predictions(
        {
            "predictions": [
                {"label": "cumulus", "confidence": 2},
                {"label": ""},
                123,
                {"confidence": 0.4},
            ]
        }
    )

    assert predictions == [{"label": "cumulus", "confidence": 1.0}]


def test_extract_predictions_rejects_invalid_predictions_payload():
    client = OllamaClient()

    predictions = client._extract_predictions({"predictions": 123})

    assert predictions == []


def test_clean_and_parse_json_accepts_clean_json():
    client = OllamaClient()

    result = client._clean_and_parse_json('{"predictions": [{"label": "cirrus"}]}')

    assert result == {"predictions": [{"label": "cirrus"}]}


def test_clean_and_parse_json_extracts_json_fence():
    client = OllamaClient()

    result = client._clean_and_parse_json(
        '```json\n{"predictions": [{"label": "cumulus"}]}\n```'
    )

    assert result == {"predictions": [{"label": "cumulus"}]}


def test_clean_and_parse_json_extracts_json_from_prose():
    client = OllamaClient()

    result = client._clean_and_parse_json(
        'Here is the result: {"predictions": [{"label": "stratus"}]} Thanks.'
    )

    assert result == {"predictions": [{"label": "stratus"}]}


def test_clean_and_parse_json_returns_empty_predictions_for_invalid_json():
    client = OllamaClient()

    result = client._clean_and_parse_json("not json")

    assert result == {"predictions": []}


def test_render_classifier_prompt_contains_expected_classes():
    client = OllamaClient()

    prompt = client._render_prompt("classifier_simple.j2")

    assert "cirrus" in prompt
    assert "cumulonimbus" in prompt
    assert "no_cloud" in prompt


def test_render_explainer_prompt_inserts_labels():
    client = OllamaClient()

    prompt = client._render_prompt("explainer.j2", labels_str="cirrus, cumulus")

    assert "cirrus, cumulus" in prompt
    assert "{{ labels_str }}" not in prompt


def test_ollama_client_uses_configured_model(monkeypatch):
    monkeypatch.setenv("OLLAMA_MODEL", "test-model:latest")
    reset_settings_cache()

    assert OllamaClient().model == "test-model:latest"

    monkeypatch.delenv("OLLAMA_MODEL", raising=False)
    reset_settings_cache()


class FakeOllamaResponse:
    def raise_for_status(self):
        return None

    def json(self):
        return {"response": '{"predictions": [{"label": "cirrus", "confidence": 0.7}]}'}


class FakeAsyncClient:
    last_payload = None
    last_url = None

    def __init__(self, timeout):
        self.timeout = timeout

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    async def post(self, url, json):
        await asyncio.sleep(0)
        FakeAsyncClient.last_url = url
        FakeAsyncClient.last_payload = json
        return FakeOllamaResponse()


async def test_analyze_image_sends_rendered_prompt_and_extracts_predictions(monkeypatch):
    monkeypatch.setenv("OLLAMA_URL", "http://ollama.test/api/generate")
    monkeypatch.setenv("OLLAMA_MODEL", "test-model")
    reset_settings_cache()

    import app.infrastructure.ollama_client as ollama_module

    monkeypatch.setattr(ollama_module.httpx, "AsyncClient", FakeAsyncClient)

    predictions = await OllamaClient().analyze_image("base64-image")

    assert predictions == [{"label": "cirrus", "confidence": 0.7}]
    assert FakeAsyncClient.last_url == "http://ollama.test/api/generate"
    assert FakeAsyncClient.last_payload["model"] == "test-model"
    assert FakeAsyncClient.last_payload["images"] == ["base64-image"]
    assert "cirrus" in FakeAsyncClient.last_payload["prompt"]
    assert "{{" not in FakeAsyncClient.last_payload["prompt"]
