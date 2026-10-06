"""WS Origin allowlist, message-size limit, and hint API rate-limit tests."""

import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.main import app  # noqa: E402


@pytest.fixture
def client():
    return TestClient(app)


class TestWebSocketOrigin:
    def test_disallowed_origin_is_rejected(self, client):
        from starlette.websockets import WebSocketDisconnect

        with pytest.raises(WebSocketDisconnect) as exc:
            with client.websocket_connect(
                "/ws/code-analysis?session_token=x",
                headers={"origin": "http://evil.example.com"},
            ):
                pass
        assert exc.value.code == 1008

    def test_allowed_origin_connects(self, client):
        with client.websocket_connect(
            "/ws/code-analysis?session_token=x",
            headers={"origin": "http://localhost:5173"},
        ) as ws:
            info = ws.receive_json()
            assert info["type"] == "session_info"


class TestWebSocketSizeLimit:
    def test_oversize_message_is_rejected(self, client, monkeypatch):
        monkeypatch.setenv("WS_MAX_MESSAGE_SIZE", "2048")
        from app.config import get_settings

        get_settings.cache_clear()
        try:
            with client.websocket_connect(
                "/ws/code-analysis?session_token=big",
                headers={"origin": "http://localhost:5173"},
            ) as ws:
                ws.receive_json()  # session_info
                ws.send_json(
                    {
                        "type": "code_update",
                        "sequence": 1,
                        "language": "python",
                        "code": "x = 1\n" * 2000,  # ~12 KB
                    }
                )
                msg = ws.receive_json()
                assert msg["type"] == "error"
                assert msg["code"] == "MESSAGE_TOO_LARGE"
        finally:
            get_settings.cache_clear()

    def test_normal_message_still_analysed(self, client):
        with client.websocket_connect(
            "/ws/code-analysis?session_token=ok",
            headers={"origin": "http://localhost:5173"},
        ) as ws:
            ws.receive_json()
            ws.send_json(
                {
                    "type": "code_update",
                    "sequence": 1,
                    "language": "python",
                    "code": "def f(:\n    pass\n",
                }
            )
            msg = ws.receive_json()
            assert msg["type"] == "analysis_result"


class TestHintRateLimit:
    def test_rate_limit_returns_429_when_exhausted(self, client, monkeypatch):
        from app.core import limits

        monkeypatch.setattr(limits, "hint_rate_limiter", limits.RateLimiter(capacity=1, refill_per_second=0.0))
        # Rebind the imported name used by the endpoint module.
        import app.api.hints as hints_module

        monkeypatch.setattr(hints_module, "hint_rate_limiter", limits.hint_rate_limiter)

        body = {"issue_id": "some-id", "level": 1, "confirmed": False}
        first = client.post("/api/v1/hints/ratelimit-test", json=body)
        second = client.post("/api/v1/hints/ratelimit-test", json=body)
        # First is allowed through the limiter (then 404s on the unknown issue);
        # the second must be blocked by the limiter.
        assert first.status_code in (404, 200)
        assert second.status_code == 429
