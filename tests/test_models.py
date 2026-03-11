# tests/test_models.py
import pytest
from models.competitor import Competitor, CompetitorCategory
from models.note import Note
from models.comment import Comment, SentimentLabel
from models.analysis import AnalysisResult

def test_competitor_defaults():
    c = Competitor(name="微粒贷", keywords=["微粒贷"], category=CompetitorCategory.core)
    assert c.is_active is True
    assert c.id is not None

def test_note_engagement():
    n = Note(note_id="abc", keyword="微粒贷", likes=10, comments=5, collects=3, shares=2)
    assert n.engagement == 20

def test_comment_sentiment_nullable():
    c = Comment(comment_id="c1", note_id="abc", content="不错")
    assert c.sentiment_label is None
