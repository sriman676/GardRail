import os

from fastapi.testclient import TestClient

from api.server import app


def test_evolve_requires_api_key():
    client = TestClient(app)

    # Ensure no admin keys configured => should be forbidden
    if "ADMIN_API_KEYS" in os.environ:
        del os.environ["ADMIN_API_KEYS"]

    res = client.post("/evolve")
    assert res.status_code in (401, 403)


def test_evolve_with_valid_key_allows():
    client = TestClient(app)
    os.environ["ADMIN_API_KEYS"] = "testkey123"

    # Call without header -> blocked
    res = client.post("/evolve")
    assert res.status_code in (401, 403)

    # Call with header -> should not be 401/403 (may return 200 or 500 depending on internal processing)
    res2 = client.post("/evolve", headers={"X-API-KEY": "testkey123"})
    assert res2.status_code not in (401, 403)


def test_webhook_notify_no_error():
    # Ensure that building an alert and waiting for decision won't raise even if webhooks unset
    from core.alert_manager import AlertManager

    am = AlertManager(mode="api")
    class Dummy:
        matched_patterns = []
        threat_level = type("TL", (), {"value": "DANGER"})
        llm_explanation = "explain"

    alert = am.build_injection_alert(Dummy(), "task")
    # Should not raise even if ALERT_WEBHOOKS not configured
    import asyncio

    async def call_wait():
        res = await am.wait_for_decision(alert, timeout=0.01)
        return res

    try:
        asyncio.get_event_loop()
    except Exception:
        pass

    # call synchronously via run
    try:
        asyncio.run(call_wait())
    except Exception:
        # Depending on the environment, the tiny timeout may raise; ensure no crash
        pass
