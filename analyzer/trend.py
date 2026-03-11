import logging
from collections import Counter
from datetime import date, datetime, timedelta
import jieba
from sklearn.feature_extraction.text import TfidfVectorizer
from sqlalchemy import select, func
from models import AsyncSessionLocal, Note, Comment, AnalysisResult
from analyzer.sentiment import SentimentAnalyzer
from analyzer.feature_extractor import FeatureExtractor
from config import settings

logger = logging.getLogger(__name__)

_STOPWORDS = {"的", "了", "是", "我", "你", "他", "她", "它", "们", "在", "有",
              "和", "与", "或", "但", "很", "都", "也", "就", "不", "没", "这", "那"}


def _tokenize(text: str) -> list[str]:
    words = jieba.cut(text)
    return [w for w in words if len(w) > 1 and w not in _STOPWORDS]


def _extract_top_words(texts: list[str], top_n: int = 10) -> list[dict]:
    if not texts:
        return []
    tokenized = [" ".join(_tokenize(t)) for t in texts]
    try:
        vectorizer = TfidfVectorizer(max_features=200)
        vectorizer.fit_transform(tokenized)
        scores = zip(vectorizer.get_feature_names_out(),
                     vectorizer.idf_)
        sorted_words = sorted(scores, key=lambda x: x[1])[:top_n]
        all_words = [w for text in tokenized for w in text.split()]
        freq = Counter(all_words)
        return [{"word": w, "count": freq.get(w, 0)} for w, _ in sorted_words]
    except ValueError:
        return []


class TrendAnalyzer:
    def __init__(self):
        self.sentiment = SentimentAnalyzer.get_instance()
        self.extractor = FeatureExtractor()

    async def run_daily_analysis(self, target_date: date | None = None):
        """对指定日期（默认昨天）的数据跑完整分析，写入 analysis_results"""
        if target_date is None:
            target_date = (datetime.utcnow() - timedelta(days=1)).date()

        logger.info(f"[Trend] Running analysis for {target_date}")
        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(Note.competitor_id).distinct()
                .where(Note.scraped_at >= datetime.combine(target_date, datetime.min.time()))
            )
            competitor_ids = [row[0] for row in result.fetchall() if row[0]]

        for competitor_id in competitor_ids:
            await self._analyze_competitor(competitor_id, target_date)

    async def _analyze_competitor(self, competitor_id: str, target_date: date):
        async with AsyncSessionLocal() as db:
            notes_result = await db.execute(
                select(Note).where(
                    Note.competitor_id == competitor_id,
                    func.date(Note.scraped_at) == target_date
                )
            )
            notes = notes_result.scalars().all()
            if not notes:
                return

            note_ids = [n.note_id for n in notes]
            note_count = len(notes)
            total_engagement = sum(n.engagement for n in notes)

            if notes:
                avg_engagement = total_engagement / note_count
                threshold = avg_engagement * settings.hot_note_multiplier
                for note in notes:
                    if note.engagement > threshold:
                        note.is_hot = True
            await db.commit()

            comments_result = await db.execute(
                select(Comment).where(Comment.note_id.in_(note_ids))
            )
            comments = comments_result.scalars().all()

            positive_count = 0
            negative_texts = []
            positive_texts = []

            if comments:
                texts = [c.content for c in comments]
                preds = self.sentiment.predict_batch(texts)
                for comment, (label, score) in zip(comments, preds):
                    comment.sentiment_label = label
                    comment.sentiment_score = score
                    if label == "positive":
                        positive_count += 1
                        positive_texts.append(comment.content)
                    elif label == "negative":
                        negative_texts.append(comment.content)
                await db.commit()

            sentiment_positive_rate = positive_count / len(comments) if comments else 0.0
            top_complaints = _extract_top_words(negative_texts)
            top_praises = _extract_top_words(positive_texts)

            note_contents = [f"{n.title} {n.content}" for n in notes]
            features_list = self.extractor.extract_batch(note_contents)
            merged_features = self.extractor.merge(features_list)

            hot_notes = [
                {"note_id": n.note_id, "title": n.title, "engagement": n.engagement}
                for n in sorted(notes, key=lambda x: x.engagement, reverse=True)
                if n.is_hot
            ][:10]

            existing = await db.execute(
                select(AnalysisResult).where(
                    AnalysisResult.competitor_id == competitor_id,
                    AnalysisResult.date == target_date
                )
            )
            ar = existing.scalar_one_or_none()
            if ar is None:
                ar = AnalysisResult(competitor_id=competitor_id, date=target_date)
                db.add(ar)

            ar.note_count = note_count
            ar.total_engagement = total_engagement
            ar.sentiment_positive_rate = sentiment_positive_rate
            ar.top_complaints = top_complaints
            ar.top_praises = top_praises
            ar.product_features = {
                "quota": merged_features.quota,
                "rate": merged_features.rate,
                "threshold": merged_features.threshold,
                "features": merged_features.features,
            }
            ar.hot_notes = hot_notes
            await db.commit()
            logger.info(f"[Trend] Saved analysis for competitor={competitor_id} date={target_date}")
