# tests/analyzer/test_trend.py
import pytest
from unittest.mock import patch
from analyzer.trend import _tokenize, _extract_top_words


def test_tokenize_removes_stopwords():
    tokens = _tokenize("这个产品的额度很高")
    assert "的" not in tokens
    assert "很" not in tokens
    assert len(tokens) > 0


def test_extract_top_words_returns_list():
    texts = ["利率太高了坑人", "利率高不划算", "额度低很失望"]
    result = _extract_top_words(texts, top_n=5)
    assert isinstance(result, list)
    for item in result:
        assert "word" in item
        assert "count" in item


def test_extract_top_words_empty():
    result = _extract_top_words([])
    assert result == []
