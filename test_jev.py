import pytest

from data_hunter import Record
from jev import JEV_MODEL, JevError, boolean_probability, evaluate, jev_filter


def test_evaluate_requires_key(monkeypatch):
    monkeypatch.delenv("AI_GATEWAY_API_KEY", raising=False)
    monkeypatch.setattr("jev._load_dotenv", lambda: None)
    with pytest.raises(JevError):
        evaluate("x", {})


def test_evaluate_builds_request():
    seen = {}

    def fake(url, headers, payload):
        seen.update(url=url, headers=headers, payload=payload)
        return {"answers": {"q": 0.9}}

    evaluate("state", {"q": {"type": "boolean", "instructions": "?"}},
             api_key="k", transport=fake)
    assert seen["url"].endswith("/v1/evaluate")
    assert seen["headers"]["Authorization"] == "Bearer k"
    assert seen["payload"]["model"] == JEV_MODEL
    assert seen["payload"]["state"] == "state"


def test_boolean_probability_shapes():
    assert boolean_probability({"answers": {"q": 0.7}}, "q") == 0.7
    assert boolean_probability({"results": {"q": {"probability": 0.3}}}, "q") == 0.3
    assert boolean_probability({"q": {"value": 1}}, "q") == 1.0
    assert boolean_probability({}, "q") is None


def test_jev_filter_thresholds():
    probs = {"Keep": 0.95, "Drop": 0.05, "Maybe": 0.5}

    def fake(url, headers, payload):
        name = next(n for n in probs if n in payload["state"])
        return {"answers": {"keep": probs[name]}}

    recs = [Record("s", n) for n in probs]
    kept, uncertain = jev_filter(recs, "Is this a real product?",
                                 api_key="k", transport=fake)
    assert [r.name for r in kept] == ["Keep"]
    assert [r.name for r in uncertain] == ["Maybe"]


def test_load_dotenv(tmp_path, monkeypatch):
    from jev import _load_dotenv
    monkeypatch.delenv("AI_GATEWAY_API_KEY", raising=False)
    env = tmp_path / ".env"
    env.write_text('# comment\nAI_GATEWAY_API_KEY="abc"\n')
    _load_dotenv(str(env))
    import os
    assert os.environ["AI_GATEWAY_API_KEY"] == "abc"
