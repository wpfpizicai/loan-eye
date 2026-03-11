# tests/analyzer/test_sentiment.py
import pytest
from unittest.mock import patch, MagicMock
from analyzer.sentiment import SentimentAnalyzer


@pytest.fixture
def analyzer():
    with patch("analyzer.sentiment.pipeline") as mock_pipeline:
        mock_pipe = MagicMock()
        mock_pipeline.return_value = mock_pipe
        inst = SentimentAnalyzer()
        inst._pipe = mock_pipe
        return inst


def test_predict_positive(analyzer):
    analyzer._pipe.return_value = [{"label": "LABEL_1", "score": 0.92}]
    label, score = analyzer.predict("下款很快，额度高")
    assert label == "positive"
    assert score == pytest.approx(0.92)


def test_predict_negative(analyzer):
    analyzer._pipe.return_value = [{"label": "LABEL_0", "score": 0.88}]
    label, score = analyzer.predict("利率太高了，坑人")
    assert label == "negative"


def test_predict_empty_text_returns_neutral(analyzer):
    label, score = analyzer.predict("")
    assert label == "neutral"


def test_predict_low_confidence_returns_neutral(analyzer):
    analyzer._pipe.return_value = [{"label": "LABEL_1", "score": 0.55}]
    label, score = analyzer.predict("还行吧")
    assert label == "neutral"


def test_predict_batch(analyzer):
    analyzer._pipe.return_value = [
        {"label": "LABEL_1", "score": 0.9},
        {"label": "LABEL_0", "score": 0.85},
    ]
    results = analyzer.predict_batch(["很好", "很差"])
    assert results[0][0] == "positive"
    assert results[1][0] == "negative"
