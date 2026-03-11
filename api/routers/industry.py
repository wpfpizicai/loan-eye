# api/routers/industry.py
from datetime import date, timedelta
from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from models import get_db, Competitor, CompetitorCategory, AnalysisResult, Note

router = APIRouter()


@router.get("/volume")
async def get_industry_volume(
    days: int = Query(default=30, ge=7, le=90),
    db: AsyncSession = Depends(get_db),
):
    """行业关键词每日声量趋势（堆叠面积图，格式匹配前端 TrendData[]）"""
    industry_result = await db.execute(
        select(Competitor).where(
            Competitor.is_active == True,
            Competitor.category == CompetitorCategory.industry
        )
    )
    industry_comps = industry_result.scalars().all()

    end_date = date.today()
    start_date = end_date - timedelta(days=days)

    all_dates: set[str] = set()
    keyword_data: dict[str, dict[str, int]] = {}

    for comp in industry_comps:
        ar_result = await db.execute(
            select(AnalysisResult.date, AnalysisResult.note_count)
            .where(
                AnalysisResult.competitor_id == comp.id,
                AnalysisResult.date >= start_date,
            ).order_by(AnalysisResult.date)
        )
        records = ar_result.fetchall()
        # 行业词组统一用竞品名（"行业词"）作为 key
        kw = comp.name
        keyword_data[kw] = {}
        for r in records:
            date_str = r.date.strftime("%m-%d")
            all_dates.add(date_str)
            keyword_data[kw][date_str] = r.note_count

    sorted_dates = sorted(all_dates)
    trend_data = []
    for d in sorted_dates:
        row: dict = {"date": d}
        for kw in keyword_data:
            row[kw] = keyword_data[kw].get(d, 0)
        trend_data.append(row)

    return {"data": trend_data}


@router.get("/hot-notes")
async def get_industry_hot_notes(
    limit: int = Query(default=20, ge=1, le=50),
    days: int = Query(default=7, ge=1, le=30),
    db: AsyncSession = Depends(get_db),
):
    """行业热门笔记 Top N"""
    industry_result = await db.execute(
        select(Competitor.id).where(
            Competitor.is_active == True,
            Competitor.category == CompetitorCategory.industry
        )
    )
    industry_ids = [row[0] for row in industry_result.fetchall()]

    cutoff = date.today() - timedelta(days=days)
    notes_result = await db.execute(
        select(Note).where(
            Note.competitor_id.in_(industry_ids),
            func.date(Note.scraped_at) >= cutoff,
        ).order_by(
            (Note.likes + Note.comments + Note.collects + Note.shares).desc()
        ).limit(limit)
    )
    notes = notes_result.scalars().all()

    return {
        "data": [
            {
                "id": n.note_id,
                "title": n.title,
                "keyword": n.keyword,
                "engagement": n.engagement,
                "interactions": f"{n.engagement / 10000:.1f}w" if n.engagement >= 10000 else str(n.engagement),
                "url": n.url,
                "publish_time": n.publish_time.strftime("%Y-%m-%d") if n.publish_time else "",
            }
            for n in notes
        ]
    }


@router.get("/competitor-share")
async def get_competitor_share(
    days: int = Query(default=30, ge=7, le=90),
    db: AsyncSession = Depends(get_db),
):
    """各竞品在行业总声量中的占比（饼图数据）"""
    from api.routers.overview import COMPETITOR_COLORS
    end_date = date.today()
    start_date = end_date - timedelta(days=days)

    competitors_result = await db.execute(
        select(Competitor).where(
            Competitor.is_active == True,
            Competitor.category == CompetitorCategory.core
        )
    )
    competitors = competitors_result.scalars().all()

    share_data = []
    for comp in competitors:
        ar_result = await db.execute(
            select(func.sum(AnalysisResult.note_count)).where(
                AnalysisResult.competitor_id == comp.id,
                AnalysisResult.date >= start_date,
            )
        )
        total = ar_result.scalar() or 0
        share_data.append({
            "name": comp.name,
            "value": total,
            "color": COMPETITOR_COLORS.get(comp.name, "#888888"),
        })

    return {"data": share_data}
