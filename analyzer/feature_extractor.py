# analyzer/feature_extractor.py
import re
from dataclasses import dataclass, field


@dataclass
class ProductFeatures:
    quota: list[str] = field(default_factory=list)
    rate: list[str] = field(default_factory=list)
    threshold: list[str] = field(default_factory=list)
    features: list[str] = field(default_factory=list)


_RULES = [
    # 额度
    (r"最高[\d.]+\s*[万千元]", "quota"),
    (r"额度[\d.,]+\s*[-~到至]\s*[\d.,]+\s*[万千元]?", "quota"),
    (r"借[\d.]+\s*[万千元]", "quota"),
    (r"[\d.]+\s*万额度", "quota"),
    # 利率
    (r"日利率[\d.]+%?", "rate"),
    (r"月利率[\d.]+%?", "rate"),
    (r"年化[\d.]+%?", "rate"),
    (r"[\d.]+%\s*年化", "rate"),
    (r"利率[\d.]+%", "rate"),
    # 门槛
    (r"(?:需要|需有|要求)[^\s，。]{2,6}(?:征信|社保|公积金|流水)", "threshold"),
    (r"无需[^\s，。]{2,6}(?:征信|社保|公积金|流水)", "threshold"),
    (r"白户(?:也)?可(?:借|申请)", "threshold"),
    (r"征信(?:有瑕疵|不好|花了)(?:也)?(?:可以|能)", "threshold"),
    # 特色功能
    (r"随借随还", "features"),
    (r"秒到账", "features"),
    (r"免息\d+天", "features"),
    (r"自动续期", "features"),
    (r"先息后本", "features"),
    (r"等额还款", "features"),
    (r"随时提前还款", "features"),
]


class FeatureExtractor:
    def extract(self, text: str) -> ProductFeatures:
        result = ProductFeatures()
        for pattern, field_name in _RULES:
            matches = re.findall(pattern, text, re.IGNORECASE)
            existing = getattr(result, field_name)
            for m in matches:
                m = m.strip()
                if m and m not in existing:
                    existing.append(m)
        return result

    def extract_batch(self, texts: list[str]) -> list[ProductFeatures]:
        return [self.extract(t) for t in texts]

    def merge(self, features_list: list[ProductFeatures]) -> ProductFeatures:
        merged = ProductFeatures()
        seen = {f: set() for f in ["quota", "rate", "threshold", "features"]}
        for f in features_list:
            for field_name in seen:
                for item in getattr(f, field_name):
                    if item not in seen[field_name]:
                        seen[field_name].add(item)
                        getattr(merged, field_name).append(item)
        return merged
