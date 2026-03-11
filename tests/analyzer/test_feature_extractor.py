# tests/analyzer/test_feature_extractor.py
import pytest
from analyzer.feature_extractor import FeatureExtractor, ProductFeatures


@pytest.fixture
def extractor():
    return FeatureExtractor()


def test_extract_quota(extractor):
    result = extractor.extract("最高5万额度，随时可借")
    assert any("5万" in q for q in result.quota)


def test_extract_rate(extractor):
    result = extractor.extract("年化利率18%，日利率0.05%")
    assert len(result.rate) >= 1
    assert any("18" in r for r in result.rate)


def test_extract_threshold(extractor):
    result = extractor.extract("无需公积金，白户也可申请")
    assert len(result.threshold) >= 1


def test_extract_features(extractor):
    result = extractor.extract("支持随借随还，秒到账，免息30天")
    assert "随借随还" in result.features
    assert "秒到账" in result.features
    assert any("免息" in f for f in result.features)


def test_extract_empty_text(extractor):
    result = extractor.extract("")
    assert result.quota == []
    assert result.features == []


def test_merge_deduplicates(extractor):
    f1 = ProductFeatures(features=["随借随还", "秒到账"])
    f2 = ProductFeatures(features=["随借随还", "免息30天"])
    merged = extractor.merge([f1, f2])
    assert merged.features.count("随借随还") == 1
    assert "免息30天" in merged.features
