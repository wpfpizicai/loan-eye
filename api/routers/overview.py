# api/routers/overview.py
from datetime import date, timedelta
from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from models import get_db, Competitor, CompetitorCategory, AnalysisResult, Note

router = APIRouter()

# 前端颜色映射
COMPETITOR_COLORS = {
    "放心借": "#1a90ff",
    "微粒贷": "#22c55e",
    "百度有钱花": "#f59e0b",
    "美团借钱": "#ef4444",
}


@router.get("/summary")
async def get_overview_summary(
    days: int = Query(default=7, ge=1, le=90),
    db: AsyncSession = Depends(get_db),
):
    """各竞品核心指标汇总"""
    end_date = date.today()
    start_date = end_date - timedelta(days=days)

    competitors_result = await db.execute(
        select(Competitor).where(
            Competitor.is_active == True,
            Competitor.category == CompetitorCategory.core
        )
    )
    competitors = competitors_result.scalars().all()

    result = []
    for comp in competitors:
        ar_result = await db.execute(
            select(AnalysisResult).where(
                AnalysisResult.competitor_id == comp.id,
                AnalysisResult.date >= start_date,
                AnalysisResult.date <= end_date,
            )
        )
        records = ar_result.scalars().all()
        total_notes = sum(r.note_count for r in records)
        total_engagement = sum(r.total_engagement for r in records)
        avg_positive_rate = (
            sum(r.sentiment_positive_rate for r in records) / len(records)
            if records else 0.0
        )
        result.append({
            "id": comp.id,
            "name": comp.name,
            "color": COMPETITOR_COLORS.get(comp.name, "#888888"),
            "note_count": total_notes,
            "total_engagement": total_engagement,
            "sentiment_positive_rate": round(avg_positive_rate, 3),
        })

    return {"data": result, "days": days}


@router.get("/trend")
async def get_engagement_trend(
    days: int = Query(default=30, ge=7, le=90),
    db: AsyncSession = Depends(get_db),
):
    """各竞品每日声量趋势（折线图数据，格式匹配前端 TrendData[]）"""
    end_date = date.today()
    start_date = end_date - timedelta(days=days)

    competitors_result = await db.execute(
        select(Competitor).where(
            Competitor.is_active == True,
            Competitor.category == CompetitorCategory.core
        )
    )
    competitors = competitors_result.scalars().all()

    # 收集所有日期
    all_dates: set[str] = set()
    comp_data: dict[str, dict[str, int]] = {}

    for comp in competitors:
        ar_result = await db.execute(
            select(AnalysisResult.date, AnalysisResult.note_count)
            .where(
                AnalysisResult.competitor_id == comp.id,
                AnalysisResult.date >= start_date,
            ).order_by(AnalysisResult.date)
        )
        records = ar_result.fetchall()
        comp_data[comp.name] = {}
        for r in records:
            date_str = r.date.strftime("%m-%d")
            all_dates.add(date_str)
            comp_data[comp.name][date_str] = r.note_count

    # 转换为前端 TrendData[] 格式：[{date: "03-01", 放心借: 10, 微粒贷: 5, ...}]
    sorted_dates = sorted(all_dates)
    trend_data = []
    for d in sorted_dates:
        row: dict = {"date": d}
        for comp in competitors:
            row[comp.name] = comp_data.get(comp.name, {}).get(d, 0)
        trend_data.append(row)

    return {"data": trend_data}


@router.get("/radar")
async def get_radar_data(
    days: int = Query(default=30, ge=7, le=90),
    db: AsyncSession = Depends(get_db),
):
    """雷达图数据（格式匹配前端 RadarData[]）"""
    end_date = date.today()
    start_date = end_date - timedelta(days=days)

    competitors_result = await db.execute(
        select(Competitor).where(
            Competitor.is_active == True,
            Competitor.category == CompetitorCategory.core
        )
    )
    competitors = competitors_result.scalars().all()

    # 计算各竞品分数（归一化到 0-100）
    scores: dict[str, dict] = {}
    max_notes = 1
    max_engagement = 1

    for comp in competitors:
        ar_result = await db.execute(
            select(AnalysisResult).where(
                AnalysisResult.competitor_id == comp.id,
                AnalysisResult.date >= start_date,
            )
        )
        records = ar_result.scalars().all()
        total_notes = sum(r.note_count for r in records)
        total_engagement = sum(r.total_engagement for r in records)
        avg_positive_rate = (
            sum(r.sentiment_positive_rate for r in records) / len(records)
            if records else 0.0
        )
        scores[comp.name] = {
            "note_count": total_notes,
            "engagement": total_engagement,
            "positive_rate": avg_positive_rate,
        }
        max_notes = max(max_notes, total_notes)
        max_engagement = max(max_engagement, total_engagement)

    # 转换为雷达图格式
    dimensions = [
        {"subject": "声量", "key": lambda s: s["note_count"] / max_notes * 100},
        {"subject": "互动", "key": lambda s: s["engagement"] / max_engagement * 100},
        {"subject": "口碑", "key": lambda s: s["positive_rate"] * 100},
    ]

    radar_data = []
    for dim in dimensions:
        row: dict = {"subject": dim["subject"]}
        for comp in competitors:
            row[comp.name] = round(dim["key"](scores.get(comp.name, {"note_count": 0, "engagement": 0, "positive_rate": 0})), 1)
        radar_data.append(row)

    return {"data": radar_data}


@router.get("/hot-notes")
async def get_hot_notes(
    limit: int = Query(default=5, ge=1, le=20),
    days: int = Query(default=7, ge=1, le=30),
    db: AsyncSession = Depends(get_db),
):
    """爆款笔记 Top N（总览页用）"""
    from models import Note as NoteModel
    cutoff = date.today() - timedelta(days=days)

    competitors_result = await db.execute(
        select(Competitor.id, Competitor.name).where(
            Competitor.is_active == True,
            Competitor.category == CompetitorCategory.core
        )
    )
    comp_map = {row.id: row.name for row in competitors_result.fetchall()}

    notes_result = await db.execute(
        select(NoteModel).where(
            NoteModel.competitor_id.in_(comp_map.keys()),
            NoteModel.is_hot == True,
            func.date(NoteModel.scraped_at) >= cutoff,
        ).order_by(
            (NoteModel.likes + NoteModel.comments + NoteModel.collects + NoteModel.shares).desc()
        ).limit(limit)
    )
    notes = notes_result.scalars().all()

    return {
        "data": [
            {
                "id": n.note_id,
                "title": n.title,
                "competitor": comp_map.get(n.competitor_id, ""),
                "interactions": f"{n.engagement / 10000:.1f}w" if n.engagement >= 10000 else str(n.engagement),
                "sentiment": "positive",  # 热门笔记默认正向
                "time": n.publish_time.strftime("%Y-%m-%d") if n.publish_time else "",
                "url": n.url,
            }
            for n in notes
        ]
    }
