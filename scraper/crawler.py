# scraper/crawler.py
import asyncio
import random
from datetime import datetime
from dataclasses import dataclass


@dataclass
class NoteData:
    note_id: str
    title: str
    content: str
    author: str
    publish_time: datetime | None
    likes: int
    comments: int
    collects: int
    shares: int
    url: str


@dataclass
class CommentData:
    comment_id: str
    note_id: str
    content: str
    author: str
    likes: int
    publish_time: datetime | None


class XhsCrawler:
    """小红书爬虫，封装 MediaCrawler"""

    def __init__(self, cookie: str, delay_range: tuple[float, float] = (2.0, 5.0)):
        self.cookie = cookie
        self.delay_range = delay_range

    async def _delay(self):
        await asyncio.sleep(random.uniform(*self.delay_range))

    async def search_notes(
        self, keyword: str, max_count: int = 50, days: int = 7
    ) -> list[NoteData]:
        """搜索关键词，返回近 N 天的笔记列表"""
        await self._delay()
        # TODO: 接入 MediaCrawler 实际实现
        raise NotImplementedError("接入 MediaCrawler 后实现")

    async def get_comments(
        self, note_id: str, max_count: int = 100
    ) -> list[CommentData]:
        """获取笔记评论"""
        await self._delay()
        raise NotImplementedError("接入 MediaCrawler 后实现")
