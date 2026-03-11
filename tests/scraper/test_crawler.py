# tests/scraper/test_crawler.py
import pytest
from unittest.mock import AsyncMock, patch
from datetime import datetime
from scraper.crawler import XhsCrawler, NoteData, CommentData


@pytest.fixture
def crawler():
    return XhsCrawler(cookie="test_cookie", delay_range=(0, 0))


@pytest.mark.asyncio
async def test_search_notes_returns_note_data(crawler):
    """search_notes 返回 NoteData 列表"""
    mock_notes = [
        NoteData(
            note_id="note1", title="微粒贷真实体验", content="额度5万，年化18%",
            author="user1", publish_time=datetime(2026, 3, 10),
            likes=100, comments=50, collects=30, shares=10, url="https://xhs.com/1"
        )
    ]
    with patch.object(crawler, "search_notes", new=AsyncMock(return_value=mock_notes)):
        result = await crawler.search_notes("微粒贷", max_count=10)
    assert len(result) == 1
    assert result[0].note_id == "note1"


@pytest.mark.asyncio
async def test_get_comments_returns_comment_data(crawler):
    """get_comments 返回 CommentData 列表"""
    mock_comments = [
        CommentData(
            comment_id="c1", note_id="note1", content="下款很快",
            author="user2", likes=5, publish_time=datetime(2026, 3, 10)
        )
    ]
    with patch.object(crawler, "get_comments", new=AsyncMock(return_value=mock_comments)):
        result = await crawler.get_comments("note1")
    assert result[0].comment_id == "c1"
