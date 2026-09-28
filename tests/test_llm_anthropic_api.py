"""The CI-only Anthropic API backend, tested offline with a fake client (no real network call).

Verifies call_structured() picks this backend when ANTHROPIC_API_KEY is set, and that the response
gets translated into the exact dict shape _claude_headless produces, since call_structured() reads
both backends through the same keys (structured_output, usage, total_cost_usd, ...).
"""

from types import SimpleNamespace

import pytest

from weekly_report import llm


def fake_response(text='{"ok": true}', input_tokens=1000, output_tokens=200,
                   cache_creation_input_tokens=0, cache_read_input_tokens=0):
    return SimpleNamespace(
        content=[SimpleNamespace(type="text", text=text)],
        usage=SimpleNamespace(input_tokens=input_tokens, output_tokens=output_tokens,
                              cache_creation_input_tokens=cache_creation_input_tokens,
                              cache_read_input_tokens=cache_read_input_tokens),
        model="claude-sonnet-5",
        id="msg_fake_123",
    )


class FakeMessages:
    def __init__(self, response):
        self._response = response

    def create(self, **kwargs):
        self.kwargs = kwargs
        return self._response


class FakeClient:
    def __init__(self, response):
        self.messages = FakeMessages(response)


def test_anthropic_api_translates_response_to_headless_shape(monkeypatch):
    monkeypatch.setattr(llm.anthropic, "Anthropic", lambda: FakeClient(fake_response()))
    out = llm._anthropic_api("system", "user", {"type": "object"}, "claude-sonnet-5")
    assert out["structured_output"] == {"ok": True}
    assert out["usage"]["input_tokens"] == 1000
    assert out["usage"]["output_tokens"] == 200
    assert out["session_id"] == "msg_fake_123"
    assert out["is_error"] is False
    assert out["total_cost_usd"] == pytest.approx((1000 * 2.00 + 200 * 10.00) / 1_000_000)


def test_anthropic_api_prices_cache_write_and_read(monkeypatch):
    response = fake_response(input_tokens=0, output_tokens=0,
                              cache_creation_input_tokens=1000, cache_read_input_tokens=1000)
    monkeypatch.setattr(llm.anthropic, "Anthropic", lambda: FakeClient(response))
    out = llm._anthropic_api("system", "user", {"type": "object"}, "claude-sonnet-5")
    expected = (1000 * 2.00 * 1.25 + 1000 * 2.00 * 0.1) / 1_000_000
    assert out["total_cost_usd"] == pytest.approx(expected)


def test_anthropic_api_raises_llm_error_on_invalid_json(monkeypatch):
    monkeypatch.setattr(llm.anthropic, "Anthropic", lambda: FakeClient(fake_response(text="not json")))
    with pytest.raises(llm.LLMError):
        llm._anthropic_api("system", "user", {"type": "object"}, "claude-sonnet-5")


def test_call_structured_uses_anthropic_api_when_key_is_set(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-fake-for-test")
    monkeypatch.setattr(llm.anthropic, "Anthropic", lambda: FakeClient(fake_response()))
    result = llm.call_structured("system", "user", {"type": "object"}, "claude-sonnet-5", "v2")
    assert result.backend == "anthropic_api"
    assert result.commentary == {"ok": True}


def test_call_structured_uses_claude_headless_when_key_is_unset(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    called = {}

    def fake_headless(system, user, schema, model):
        called["ran"] = True
        return {"structured_output": {"ok": True}, "usage": {}, "modelUsage": {model: None},
                "total_cost_usd": 0.1, "duration_ms": 500, "session_id": "s1"}

    monkeypatch.setattr(llm, "_claude_headless", fake_headless)
    result = llm.call_structured("system", "user", {"type": "object"}, "claude-sonnet-5", "v2")
    assert result.backend == "claude_headless"
    assert called["ran"]
