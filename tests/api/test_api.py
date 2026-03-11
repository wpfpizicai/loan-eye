# tests/api/test_api.py
import pytest
from httpx import AsyncClient, ASGITransport
from unittest.mock import AsyncMock, MagicMock, patch
from api.main import app


@pytest.mark.asyncio
async def test_health():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def _mock_db_with_competitors(competitor_names=None):
    """Helper: 创建返回竞品列表的 mock db"""
    if competitor_names is None:
        competitor_names = ["微粒贷"]

    mock_db = AsyncMock()

    def make_comp(name):
        from models.competitor import CompetitorCategory
        c = MagicMock()
        c.id = f"id_{name}"
        c.name = name
        c.category = CompetitorCategory.core
        c.is_active = True
        return c

    comps = [make_comp(n) for n in competitor_names]
    comp_result = MagicMock()
    comp_result.scalars.return_value.all.return_value = comps
    ar_result = MagicMock()
    ar_result.scalars.return_value.all.return_value = []
    mock_db.execute = AsyncMock(side_effect=[comp_result, ar_result] * 10)
    return mock_db


@pytest.mark.asyncio
async def test_overview_summary_returns_data():
    mock_db = _mock_db_with_competitors(["微粒贷", "放心借"])

    async def override_get_db():
        yield mock_db

    app.dependency_overrides[__import__('models', fromlist=['get_db']).get_db] = override_get_db
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.get("/api/overview/summary?days=7")
        assert resp.status_code == 200
        body = resp.json()
        assert "data" in body
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_competitor_list_returns_data():
    from models import get_db

    mock_db = AsyncMock()
    mock_comp = MagicMock()
    mock_comp.id = "c1"
    mock_comp.name = "微粒贷"
    result = MagicMock()
    result.scalars.return_value.all.return_value = [mock_comp]
    mock_db.execute = AsyncMock(return_value=result)

    async def override_get_db():
        yield mock_db

    app.dependency_overrides[get_db] = override_get_db
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.get("/api/competitor/list")
        assert resp.status_code == 200
        body = resp.json()
        assert len(body["data"]) == 1
        assert body["data"][0]["name"] == "微粒贷"
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_competitor_detail_404():
    from models import get_db

    mock_db = AsyncMock()
    result = MagicMock()
    result.scalar_one_or_none.return_value = None
    mock_db.execute = AsyncMock(return_value=result)

    async def override_get_db():
        yield mock_db

    app.dependency_overrides[get_db] = override_get_db
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.get("/api/competitor/nonexistent/detail")
        assert resp.status_code == 404
    finally:
        app.dependency_overrides.clear()
