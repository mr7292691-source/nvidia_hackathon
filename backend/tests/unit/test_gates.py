"""
Direct unit tests for the three decision gates (app/agents/gates/), run
against a real SQLite DB (not mocked) so the actual query logic is
exercised, not just the shape of the functions.
"""
from __future__ import annotations

from datetime import datetime

import pytest

from app.agents.gates.confidence_gate import confidence_gate_check
from app.agents.gates.evidence_verifier import evidence_verifier_check
from app.agents.gates.policy_verifier import policy_verifier_check
from app.agents.tools.evidence_tools import register_event, set_vision_confidence
from app.db.models import InsurerExposureReportRow
from app.db.session import get_session, init_db
from app.evidence.evidence_record import build_event_bundle

WINDOW = (datetime(2026, 6, 14, 6, 0, 0), datetime(2026, 6, 14, 20, 0, 0))
BBOX = {"type": "Polygon", "coordinates": [[[-95.55, 29.60], [-95.30, 29.60],
                                             [-95.30, 29.85], [-95.55, 29.85], [-95.55, 29.60]]]}


@pytest.fixture(autouse=True)
async def _db():
    await init_db()
    yield


async def _make_event() -> str:
    record = await build_event_bundle(event_window=WINDOW, bbox=BBOX)
    await register_event(record)
    return record.event_id


class TestEvidenceVerifier:
    async def test_passes_with_no_event_id(self):
        result = await evidence_verifier_check(event_id=None)
        assert result.passed is False
        assert "event_id" in result.reason

    async def test_passes_for_unknown_event(self):
        result = await evidence_verifier_check(event_id="evt_does_not_exist")
        assert result.passed is False
        assert "No evidence record found" in result.reason

    async def test_passes_for_real_replay_event(self):
        """The Houston replay fixtures corroborate across 5 sources within
        a tight time window of each other -- should pass real scoring."""
        event_id = await _make_event()
        result = await evidence_verifier_check(event_id=event_id)
        assert result.passed is True
        assert result.score == 1.0  # all 5 sources corroborate


class TestConfidenceGate:
    async def test_blocks_when_no_vision_confidence_set(self):
        event_id = await _make_event()
        result = await confidence_gate_check(event_id=event_id)
        assert result.passed is False
        assert "evidence gap" in result.reason.lower()

    async def test_passes_with_high_confidence(self):
        event_id = await _make_event()
        await set_vision_confidence(event_id=event_id, confidence=0.95, lineage_ref="ref1")
        result = await confidence_gate_check(event_id=event_id)
        assert result.passed is True

    async def test_blocks_with_low_confidence(self):
        event_id = await _make_event()
        await set_vision_confidence(event_id=event_id, confidence=0.05, lineage_ref="ref2")
        result = await confidence_gate_check(event_id=event_id)
        assert result.passed is False
        assert "below threshold" in result.reason


class TestPolicyVerifier:
    async def test_passes_with_no_exposure_report_yet(self):
        event_id = await _make_event()
        result = await policy_verifier_check(event_id=event_id, args={})
        assert result.passed is True

    async def test_passes_with_no_asserted_figure(self):
        event_id = await _make_event()
        async with get_session() as session:
            session.add(InsurerExposureReportRow(
                event_id=event_id, policies=[], total_estimated_exposure_usd=10_000.0, approved=False
            ))
            await session.commit()
        result = await policy_verifier_check(event_id=event_id, args={})
        assert result.passed is True

    async def test_blocks_on_large_drift(self):
        event_id = await _make_event()
        async with get_session() as session:
            session.add(InsurerExposureReportRow(
                event_id=event_id, policies=[], total_estimated_exposure_usd=10_000.0, approved=False
            ))
            await session.commit()
        result = await policy_verifier_check(
            event_id=event_id, args={"asserted_total_exposure_usd": 50_000.0}
        )
        assert result.passed is False
        assert "diverges" in result.reason

    async def test_passes_within_drift_tolerance(self):
        event_id = await _make_event()
        async with get_session() as session:
            session.add(InsurerExposureReportRow(
                event_id=event_id, policies=[], total_estimated_exposure_usd=10_000.0, approved=False
            ))
            await session.commit()
        result = await policy_verifier_check(
            event_id=event_id, args={"asserted_total_exposure_usd": 10_500.0}  # 5% drift, within 10%
        )
        assert result.passed is True
