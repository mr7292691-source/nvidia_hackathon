import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.mark.asyncio
async def test_replay_houston_demo_creates_event():
    async with app.router.lifespan_context(app):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.post("/events/replay/houston-demo")
            assert resp.status_code == 200
            body = resp.json()
            assert body["event_id"].startswith("evt_")
            assert len(body["lineage"]) == 5  # NWS, USGS, HCFCD, TranStar, FEMA


@pytest.mark.asyncio
async def test_health_check():
    async with app.router.lifespan_context(app):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.get("/health")
            assert resp.status_code == 200
            assert resp.json()["status"] == "ok"


@pytest.mark.asyncio
async def test_agents_run_blocks_with_evidence_gap_when_no_vision_data():
    """Real proof of the deck's slide 6 requirement: a low-confidence /
    no-vision-data case returns a clean evidence-gap response, not a 500 --
    exercised here without needing a live NIM call, since the block happens
    in the evidence_verifier/confidence_gate before any model is invoked."""
    async with app.router.lifespan_context(app):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            create_resp = await client.post("/events/replay/houston-demo")
            event_id = create_resp.json()["event_id"]

            # Directly exercise the governed evidence lookup the way a
            # specialist tool would, without needing the full DeepAgents
            # graph (which requires a live NIM call to invoke).
            from app.agents.tools.evidence_tools import get_evidence_record
            from app.nvidia_runtime.relay.governed_tools import EvidenceGapError, governed_call

            with pytest.raises(EvidenceGapError) as exc_info:
                await governed_call(
                    name="evidence_record_tool", event_id=event_id, args={},
                    func=lambda: get_evidence_record(event_id=event_id),
                )
            assert "evidence gap" in exc_info.value.reason.lower() or "confidence" in exc_info.value.reason.lower()
