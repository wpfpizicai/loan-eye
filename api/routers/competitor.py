# api/routers/competitor.py
from datetime import date, timedelta
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from models import get_db, Competitor, CompetitorCategory, AnalysisResult, Note
from api.routers.overview import COMPETITOR_COLORS

router = APIRouter()


@router.get("/list")
async def list_competitors(db: AsyncSession = Depends(get_db)):
    """返回所有核心竞品列表"""
    result = await db.execute(
        select(Competitor).where(
            Competitor.is_active == True,
            Competitor.category == CompetitorCategory.core
        )
    )
    competitors = result.scalars().all()
    return {
        "data": [
            {"id": c.id, "name": c.name, "color": COMPETITOR_COLORS.get(c.name, "#888888")}
            for c in competitors
        ]
    }


@router.get("/{competitor_id}/detail")
async def get_competitor_detail(
    competitor_id: str,
    days: int = Query(default=30, ge=1, le=90),
    db: AsyncSession = Depends(get_db),
):
    """竞品详情：产品能力 + 情感趋势 + 爆款笔记"""
    comp_result = await db.execute(select(Competitor).where(Competitor.id == competitor_id))
    comp = comp_result.scalar_one_or_none()
    if not comp:
        raise HTTPException(status_code=404, detail="Competitor not found")

    end_date = date.today()
    start_date = end_date - timedelta(days=days)
    ar_result = await db.execute(
        select(AnalysisResult).where(
            AnalysisResult.competitor_id == competitor_id,
            AnalysisResult.date >= start_date,
        ).order_by(AnalysisResult.date)
    )
    records = ar_result.scalars().all()

    latest_features = records[-1].product_features if records else {}

    # 情感趋势时序（格式：[{date, positive_rate}]）
    sentiment_trend = [
        {"date": r.date.strftime("%m-%d"), "positive_rate": round(r.sentiment_positive_rate, 3)}
        for r in records
    ]

    # 投诉/好评热词（最近一条）
    top_complaints = records[-1].top_complaints if records else []
    top_praises = records[-1].top_praises if records else []

    # 爆款笔记 Top10
    hot_notes_result = await db.execute(
        select(Note).where(
            Note.competitor_id == competitor_id,
            Note.is_hot == True,
        ).order_by(
            (Note.likes + Note.comments + Note.collects + Note.shares).desc()
        ).limit(10)
    )
    hot_notes = hot_notes_result.scalars().all()

    return {
        "id": comp.id,
        "name": comp.name,
        "color": COMPETITOR_COLORS.get(comp.name, "#888888"),
        "product_features": latest_features,
        "sentiment_trend": sentiment_trend,
        "top_complaints": top_complaints,
        "top_praises": top_praises,
        "hot_notes": [
            {
                "id": n.note_id,
                "title": n.title,
                "engagement": n.engagement,
                "interactions": f"{n.engagement / 10000:.1f}w" if n.engagement >= 10000 else str(n.engagement),
                "url": n.url,
                "publish_time": n.publish_time.strftime("%Y-%m-%d") if n.publish_time else "",
            }
            for n in hot_notes
        ],
    }
