import asyncio

import pytest

from core.alert_manager import Alert, AlertManager, UserDecision


def make_alert():
    return Alert(
        alert_id="test-id",
        alert_type="injection",
        threat_level="DANGER",
        original_task="Summarize PDF",
        malicious_content="IGNORE INSTRUCTIONS",
        explanation="Test explanation",
    )


def test_cli_block(monkeypatch):
    mgr = AlertManager(mode="cli")
    monkeypatch.setattr("builtins.input", lambda _: "b")
    decision = mgr._cli_decision(make_alert())
    assert decision == UserDecision.BLOCK


def test_cli_allow(monkeypatch):
    mgr = AlertManager(mode="cli")
    monkeypatch.setattr("builtins.input", lambda _: "a")
    decision = mgr._cli_decision(make_alert())
    assert decision == UserDecision.ALLOW_ONCE


def test_cli_report(monkeypatch):
    mgr = AlertManager(mode="cli")
    monkeypatch.setattr("builtins.input", lambda _: "r")
    decision = mgr._cli_decision(make_alert())
    assert decision == UserDecision.REPORT


@pytest.mark.asyncio
async def test_api_mode_decision():
    mgr = AlertManager(mode="api")
    alert = make_alert()

    async def submit_after_delay():
        await asyncio.sleep(0.1)
        mgr.submit_decision(UserDecision.BLOCK)

    task = asyncio.create_task(submit_after_delay())
    decision = await mgr.wait_for_decision(alert, timeout=5.0)
    await task
    assert decision == UserDecision.BLOCK


@pytest.mark.asyncio
async def test_api_mode_timeout_autoblocks():
    mgr = AlertManager(mode="api")
    decision = await mgr.wait_for_decision(make_alert(), timeout=0.1)
    assert decision == UserDecision.BLOCK


def test_cli_invalid_input_then_valid(monkeypatch):
    mgr = AlertManager(mode="cli")
    responses = iter(["x", "z", "b"])
    monkeypatch.setattr("builtins.input", lambda _: next(responses))
    decision = mgr._cli_decision(make_alert())
    assert decision == UserDecision.BLOCK
