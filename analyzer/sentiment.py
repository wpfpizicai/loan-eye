# analyzer/sentiment.py
import logging
from typing import Literal
from transformers import pipeline
from config import settings

logger = logging.getLogger(__name__)

SentimentLabel = Literal["positive", "negative", "neutral"]

# 模型标签映射（jd 模型输出 LABEL_0=negative, LABEL_1=positive）
_LABEL_MAP = {"LABEL_0": "negative", "LABEL_1": "positive"}


class SentimentAnalyzer:
    _instance = None  # 单例，避免重复加载模型

    def __init__(self):
        logger.info(f"[Sentiment] Loading model: {settings.sentiment_model}")
        self._pipe = pipeline(
            "text-classification",
            model=settings.sentiment_model,
            device=-1,
            truncation=True,
            max_length=512,
        )

    @classmethod
    def get_instance(cls) -> "SentimentAnalyzer":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def predict(self, text: str) -> tuple[SentimentLabel, float]:
        """返回 (label, score)。空文本返回 neutral。"""
        if not text or not text.strip():
            return "neutral", 1.0
        result = self._pipe(text[:512])[0]
        raw_label = result["label"]
        score = float(result["score"])
        label = _LABEL_MAP.get(raw_label, "neutral")
        if score < 0.6:
            return "neutral", score
        return label, score

    def predict_batch(self, texts: list[str]) -> list[tuple[SentimentLabel, float]]:
        """批量预测"""
        if not texts:
            return []
        results = self._pipe([t[:512] for t in texts], batch_size=32)
        output = []
        for r in results:
            label = _LABEL_MAP.get(r["label"], "neutral")
            score = float(r["score"])
            if score < 0.6:
                output.append(("neutral", score))
            else:
                output.append((label, score))
        return output
