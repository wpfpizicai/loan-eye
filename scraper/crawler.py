# scraper/crawler.py
import asyncio
import logging
import sys
import types
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

# ── MediaCrawler 路径 ────────────────────────────────────────────────────────
_MC_PATH = Path(__file__).parent.parent / "third_party" / "MediaCrawler"
if str(_MC_PATH) not in sys.path:
    sys.path.insert(0, str(_MC_PATH))

# ── 修复 1：给 config 模块补齐 MediaCrawler 所需的常量 ────────────────────────
# 我们的 config.py 是 Pydantic Settings，MediaCrawler 的 config 是一堆常量。
# 在这里把 MC 需要的常量直接附加到 sys.modules['config'] 上，避免两套 config 冲突。
import config as _app_config  # noqa: E402  – 先拿到我们自己的 config 对象

_MC_DEFAULTS = {
    "ENABLE_GET_SUB_COMMENTS": False,
    "ENABLE_GET_COMMENTS": True,
    "CRAWLER_MAX_NOTES_COUNT": 50,
    "CRAWLER_MAX_COMMENTS_COUNT_SINGLENOTES": 100,
    "MAX_CONCURRENCY_NUM": 1,
    "HEADLESS": True,
    "ENABLE_CDP_MODE": False,
    "CDP_HEADLESS": True,
    "ENABLE_IP_PROXY": False,
    "IP_PROXY_POOL_COUNT": 0,
    "CACHE_TYPE_REDIS": "memory",   # 用内存缓存，不依赖 Redis
    "CACHE_TYPE_MEMORY": "memory",
    "LOGIN_TYPE": "cookie",
    "COOKIES": "",
    "CRAWLER_TYPE": "search",
    "SAVE_DATA_OPTION": "db",
    "SAVE_LOGIN_STATE": False,
    "START_PAGE": 1,
    "SORT_TYPE": "",
    "CRAWLER_MAX_SLEEP_SEC": 2,
    "ENABLE_GET_MEIDAS": False,
    "ENABLE_GET_WORDCLOUD": False,
}
for _k, _v in _MC_DEFAULTS.items():
    if not hasattr(_app_config, _k):
        setattr(_app_config, _k, _v)

# ── 修复 2：预注册 media_platform.xhs 包，跳过 __init__.py ────────────────────
# __init__.py 会 import core.py → proxy_ip_pool.py，触发大量不需要的依赖。
# 预注册一个空包，让 Python 认为包已加载，后续只按需加载具体子模块。
def _pre_register(pkg_name: str, pkg_path: Path):
    if pkg_name not in sys.modules:
        mod = types.ModuleType(pkg_name)
        mod.__path__ = [str(pkg_path)]
        mod.__package__ = pkg_name
        sys.modules[pkg_name] = mod

_pre_register("media_platform", _MC_PATH / "media_platform")
_pre_register("media_platform.xhs", _MC_PATH / "media_platform" / "xhs")


# ── 数据结构 ─────────────────────────────────────────────────────────────────

@dataclass
class NoteData:
    note_id: str
    title: str
    content: str
    author: str
    publish_time: datetime | None
    likes: int
    comments: int
    collects: int
    shares: int
    url: str
    xsec_token: str = ""


@dataclass
class CommentData:
    comment_id: str
    note_id: str
    content: str
    author: str
    likes: int
    publish_time: datetime | None


# ── 工具函数 ──────────────────────────────────────────────────────────────────

def _parse_int(value) -> int:
    try:
        return int(value or 0)
    except (ValueError, TypeError):
        return 0


def _parse_time(ts) -> Optional[datetime]:
    try:
        return datetime.fromtimestamp(int(ts) / 1000, tz=timezone.utc)
    except (ValueError, TypeError):
        return None


def _note_from_raw(raw: dict) -> NoteData:
    user = raw.get("user", {})
    interact = raw.get("interact_info", {})
    note_id = raw.get("note_id", "")
    return NoteData(
        note_id=note_id,
        title=raw.get("title") or raw.get("desc", "")[:255],
        content=raw.get("desc", ""),
        author=user.get("nickname", ""),
        publish_time=_parse_time(raw.get("time")),
        likes=_parse_int(interact.get("liked_count")),
        comments=_parse_int(interact.get("comment_count")),
        collects=_parse_int(interact.get("collected_count")),
        shares=_parse_int(interact.get("share_count")),
        xsec_token=raw.get("xsec_token", ""),
        url=f"https://www.xiaohongshu.com/explore/{note_id}?xsec_token={raw.get('xsec_token', '')}&xsec_source=pc_search",
    )


def _comment_from_raw(note_id: str, raw: dict) -> CommentData:
    user = raw.get("user_info", {})
    return CommentData(
        comment_id=raw.get("id", ""),
        note_id=note_id,
        content=raw.get("content", ""),
        author=user.get("nickname", ""),
        likes=_parse_int(raw.get("like_count")),
        publish_time=_parse_time(raw.get("create_time")),
    )


# ── 爬虫主类 ──────────────────────────────────────────────────────────────────

class XhsCrawler:
    """小红书爬虫，封装 MediaCrawler"""

    def __init__(self, cookie: str, delay_range: tuple[float, float] = (2.0, 5.0)):
        self.cookie = cookie
        self.delay_range = delay_range
        self._playwright = None
        self._browser = None
        self._context = None
        self._page = None
        self._client = None

    async def _ensure_client(self):
        """懒初始化：启动 Playwright 并创建 XiaoHongShuClient"""
        if self._client is not None:
            return

        from playwright.async_api import async_playwright
        from media_platform.xhs.client import XiaoHongShuClient
        from tools.crawler_util import convert_cookies, convert_str_cookie_to_dict

        stealth_js = _MC_PATH / "libs" / "stealth.min.js"

        self._playwright = await async_playwright().start()
        self._browser = await self._playwright.chromium.launch(headless=True)
        self._context = await self._browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/137.0.0.0 Safari/537.36"
            )
        )

        if stealth_js.exists():
            await self._context.add_init_script(path=str(stealth_js))

        cookie_dict = convert_str_cookie_to_dict(self.cookie)
        await self._context.add_cookies([
            {"name": k, "value": v, "domain": ".xiaohongshu.com", "path": "/"}
            for k, v in cookie_dict.items()
        ])

        self._page = await self._context.new_page()
        await self._page.goto(
            "https://www.xiaohongshu.com", wait_until="domcontentloaded"
        )

        cookie_str, full_cookie_dict = convert_cookies(
            await self._context.cookies()
        )

        # 初始化代理池（可选）
        proxy_ip_pool = None
        if settings.wandou_app_key:
            from proxy.proxy_ip_pool import ProxyIpPool
            from proxy.providers.wandou_http_proxy import WanDouHttpProxy
            provider = WanDouHttpProxy(app_key=settings.wandou_app_key)
            proxy_ip_pool = ProxyIpPool(
                ip_pool_count=settings.ip_proxy_pool_count,
                enable_validate_ip=False,
                ip_provider=provider,
            )
            await proxy_ip_pool.load_proxies()
            logger.info(f"[XhsCrawler] Proxy pool loaded with {len(proxy_ip_pool.proxy_list)} IPs")

        self._client = XiaoHongShuClient(
            headers={
                "accept": "application/json, text/plain, */*",
                "accept-language": "zh-CN,zh;q=0.9",
                "content-type": "application/json;charset=UTF-8",
                "origin": "https://www.xiaohongshu.com",
                "referer": "https://www.xiaohongshu.com/",
                "user-agent": (
                    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/137.0.0.0 Safari/537.36"
                ),
                "Cookie": cookie_str,
            },
            playwright_page=self._page,
            cookie_dict=full_cookie_dict,
            proxy_ip_pool=proxy_ip_pool,
        )
        logger.info("[XhsCrawler] Client initialized")

    async def search_notes(
        self, keyword: str, max_count: int = 50, days: int = 7
    ) -> list[NoteData]:
        """搜索关键词，返回笔记列表（最多 max_count 条）"""
        from media_platform.xhs.field import SearchSortType
        from media_platform.xhs.help import get_search_id

        await self._ensure_client()

        results: list[NoteData] = []
        page = 1
        page_size = 20
        search_id = get_search_id()

        while len(results) < max_count:
            logger.info(f"[XhsCrawler] Searching '{keyword}' page={page}")
            resp = await self._client.get_note_by_keyword(
                keyword=keyword,
                search_id=search_id,
                page=page,
                page_size=page_size,
                sort=SearchSortType.GENERAL,
            )
            if not resp:
                break

            items = [
                item for item in resp.get("items", [])
                if item.get("model_type") not in ("rec_query", "hot_query")
            ]
            if not items:
                break

            for item in items:
                if len(results) >= max_count:
                    break
                note_id = item.get("id")
                xsec_token = item.get("xsec_token", "")
                xsec_source = item.get("xsec_source", "pc_search")

                detail = await self._client.get_note_by_id(
                    note_id=note_id,
                    xsec_source=xsec_source,
                    xsec_token=xsec_token,
                )
                if detail:
                    detail["xsec_token"] = xsec_token
                    results.append(_note_from_raw(detail))

                await asyncio.sleep(1.5)

            if not resp.get("has_more", False):
                break
            page += 1
            await asyncio.sleep(2.0)

        logger.info(f"[XhsCrawler] Found {len(results)} notes for '{keyword}'")
        return results

    async def get_comments(
        self, note_id: str, xsec_token: str = "", max_count: int = 100
    ) -> list[CommentData]:
        """获取笔记评论，rate-limit 时等待后重试一次"""
        await self._ensure_client()

        for attempt in range(3):
            try:
                raw_comments = await self._client.get_note_all_comments(
                    note_id=note_id,
                    xsec_token=xsec_token,
                    crawl_interval=3.0,
                    max_count=max_count,
                )
                return [_comment_from_raw(note_id, c) for c in raw_comments]
            except Exception as e:
                if "Rate limited" in str(e) or "300013" in str(e) or "访问频繁" in str(e):
                    wait = 60 * (attempt + 1)
                    logger.warning(f"[XhsCrawler] Rate limited on {note_id}, waiting {wait}s (attempt {attempt+1}/3)")
                    await asyncio.sleep(wait)
                else:
                    raise
        raise Exception(f"Rate limited after 3 attempts for note {note_id}")

    async def close(self):
        """释放浏览器资源"""
        if self._page:
            await self._page.close()
        if self._context:
            await self._context.close()
        if self._browser:
            await self._browser.close()
        if self._playwright:
            await self._playwright.stop()
        self._client = None
        logger.info("[XhsCrawler] Browser closed")
