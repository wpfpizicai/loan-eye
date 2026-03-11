# scripts/seed.py
import asyncio
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from models import AsyncSessionLocal, Competitor, CompetitorCategory

COMPETITORS = [
    {"name": "放心借", "keywords": ["放心借", "放心借额度", "放心借利率"], "category": CompetitorCategory.core},
    {"name": "微粒贷", "keywords": ["微粒贷", "微粒贷额度", "微粒贷下款"], "category": CompetitorCategory.core},
    {"name": "百度有钱花", "keywords": ["有钱花", "百度有钱花", "度小满"], "category": CompetitorCategory.core},
    {"name": "美团借钱", "keywords": ["美团借钱", "美团月付"], "category": CompetitorCategory.core},
    {"name": "行业词", "keywords": ["现金贷", "小额贷款", "网络借贷", "借钱app", "信用贷款", "消费贷"], "category": CompetitorCategory.industry},
]

async def seed():
    async with AsyncSessionLocal() as db:
        for data in COMPETITORS:
            competitor = Competitor(**data)
            db.add(competitor)
        await db.commit()
        print(f"Seeded {len(COMPETITORS)} competitors")

if __name__ == "__main__":
    asyncio.run(seed())
