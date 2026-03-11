# tests/scraper/test_scheduler.py
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime
from scraper.scheduler import ScrapeScheduler
from scraper.crawler import NoteData, CommentData


@pytest.fixture
def scheduler():
    return ScrapeScheduler()


@pytest.mark.asyncio
async def test_run_daily_scrape_calls_each_keyword(scheduler):
    """每个竞品的每个关键词都会触发抓取"""
    mock_competitor = MagicMock()
    mock_competitor.id = "comp1"
    mock_competitor.keywords = ["微粒贷", "微粒贷额度"]

    with patch("scraper.scheduler.AsyncSessionLocal") as mock_session_cls, \
         patch.object(scheduler, "_scrape_keyword", new=AsyncMock()) as mock_scrape:
        mock_session = AsyncMock()
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=False)
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [mock_competitor]
        mock_session.execute = AsyncMock(return_value=mock_result)
        mock_session_cls.return_value = mock_session

        await scheduler.run_daily_scrape()

    assert mock_scrape.call_count == 2
    mock_scrape.assert_any_call("comp1", "微粒贷")
    mock_scrape.assert_any_call("comp1", "微粒贷额度")


@pytest.mark.asyncio
async def test_scrape_keyword_upserts_notes(scheduler):
    """_scrape_keyword 对每篇笔记调用 _upsert_note"""
    mock_notes = [
        NoteData(note_id="n1", title="t1", content="c1", author="a1",
                 publish_time=datetime(2026, 3, 10), likes=10, comments=5,
                 collects=3, shares=1, url="u1")
    ]
    with patch.object(scheduler.crawler, "search_notes", new=AsyncMock(return_value=mock_notes)), \
         patch.object(scheduler.crawler, "get_comments", new=AsyncMock(return_value=[])), \
         patch.object(scheduler, "_upsert_note", new=AsyncMock()) as mock_upsert, \
         patch("scraper.scheduler.AsyncSessionLocal") as mock_session_cls:
        mock_session = AsyncMock()
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=False)
        mock_session_cls.return_value = mock_session

        await scheduler._scrape_keyword("comp1", "微粒贷")

    mock_upsert.assert_called_once()
