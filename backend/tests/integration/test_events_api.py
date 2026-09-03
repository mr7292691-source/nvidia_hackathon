import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.mark.asyncio
async def test_replay_houston_demo_creates_event():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post("/events/replay/houston-demo")
        assert resp.status_code == 200
        body = resp.json()
        assert body["event_id"].startswith("evt_")
        assert len(body["lineage"]) == 5  # NWS, USGS, HCFCD, TranStar, FEMA


@pytest.mark.asyncio
async def test_health_check():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/health")
        assert resp.status_code == 200
        assert resp.json()["status"] == "ok"
