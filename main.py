# main.py
import asyncio
import logging
import uvicorn
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from scraper.scheduler import ScrapeScheduler
from analyzer.trend import TrendAnalyzer

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def daily_job():
    """每日任务：先抓取，再分析"""
    scraper = ScrapeScheduler()
    await scraper.run_daily_scrape()

    analyzer = TrendAnalyzer()
    await analyzer.run_daily_analysis()


def start_scheduler():
    scheduler = AsyncIOScheduler()
    scheduler.add_job(
        daily_job,
        trigger=CronTrigger(hour=2, minute=0),
        id="daily_scrape_and_analyze",
        replace_existing=True,
    )
    scheduler.start()
    logger.info("[Scheduler] Started, daily job at 02:00 UTC")
    return scheduler


if __name__ == "__main__":
    start_scheduler()
    uvicorn.run("api.main:app", host="0.0.0.0", port=8000, reload=False)
