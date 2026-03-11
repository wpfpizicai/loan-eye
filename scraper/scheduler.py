# scraper/scheduler.py
import logging
from datetime import datetime
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from models import AsyncSessionLocal, Competitor, Note, Comment
from scraper.crawler import XhsCrawler, NoteData, CommentData
from config import settings

logger = logging.getLogger(__name__)


class ScrapeScheduler:
    def __init__(self):
        self.crawler = XhsCrawler(
            cookie=settings.xhs_cookie,
            delay_range=(2.0, 5.0)
        )

    async def run_daily_scrape(self):
        """每日全量抓取入口"""
        logger.info(f"[Scheduler] Daily scrape started at {datetime.utcnow()}")
        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(Competitor).where(Competitor.is_active == True)
            )
            competitors = result.scalars().all()

        for competitor in competitors:
            for keyword in competitor.keywords:
                try:
                    await self._scrape_keyword(competitor.id, keyword)
                except Exception as e:
                    logger.error(f"[Scheduler] Failed on keyword={keyword}: {e}")

        logger.info("[Scheduler] Daily scrape completed")

    async def _scrape_keyword(self, competitor_id: str, keyword: str):
        logger.info(f"[Scheduler] Scraping keyword={keyword}")
        notes = await self.crawler.search_notes(
            keyword,
            max_count=settings.scrape_max_notes_per_keyword,
            days=7
        )
        async with AsyncSessionLocal() as db:
            for note_data in notes:
                await self._upsert_note(db, competitor_id, keyword, note_data)
            await db.commit()

        for note_data in notes:
            try:
                comments = await self.crawler.get_comments(
                    note_data.note_id,
                    max_count=settings.scrape_comments_per_note
                )
                async with AsyncSessionLocal() as db:
                    for comment_data in comments:
                        await self._upsert_comment(db, comment_data)
                    await db.commit()
            except Exception as e:
                logger.error(f"[Scheduler] Failed getting comments for {note_data.note_id}: {e}")

    async def _upsert_note(self, db, competitor_id: str, keyword: str, data: NoteData):
        stmt = pg_insert(Note).values(
            note_id=data.note_id,
            competitor_id=competitor_id,
            keyword=keyword,
            title=data.title,
            content=data.content,
            author=data.author,
            publish_time=data.publish_time,
            likes=data.likes,
            comments=data.comments,
            collects=data.collects,
            shares=data.shares,
            url=data.url,
        ).on_conflict_do_update(
            index_elements=["note_id"],
            set_={"likes": data.likes, "comments": data.comments,
                  "collects": data.collects, "shares": data.shares}
        )
        await db.execute(stmt)

    async def _upsert_comment(self, db, data: CommentData):
        stmt = pg_insert(Comment).values(
            comment_id=data.comment_id,
            note_id=data.note_id,
            content=data.content,
            author=data.author,
            likes=data.likes,
            publish_time=data.publish_time,
        ).on_conflict_do_nothing(index_elements=["comment_id"])
        await db.execute(stmt)
