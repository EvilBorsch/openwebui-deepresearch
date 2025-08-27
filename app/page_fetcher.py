import asyncio
import base64
import logging
import time
from contextlib import asynccontextmanager
from typing import Any, Dict, List, Optional

from playwright.async_api import Browser, BrowserContext, Page, async_playwright
from playwright_stealth import stealth_async

from .config import Config

logger = logging.getLogger(__name__)


@asynccontextmanager
async def _launch_browser(config: Config) -> Browser:
    args = [
        "--no-sandbox",
        "--disable-setuid-sandbox",
        "--disable-dev-shm-usage",
        "--disable-blink-features=AutomationControlled",
        "--disable-gpu",
        "--no-first-run",
        "--no-default-browser-check",
        "--disable-features=site-per-process",
    ]
    proxy_settings = {"server": config.browser.proxy} if config.browser.proxy else None
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=config.browser.headless, args=args, proxy=proxy_settings)
        try:
            yield browser
        finally:
            await browser.close()


async def _new_context(browser: Browser, config: Config, *, user_agent: Optional[str], locale: Optional[str], timezone_id: Optional[str]) -> BrowserContext:
    context = await browser.new_context(
        user_agent=user_agent or config.browser.user_agent
        or "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        locale=locale or config.browser.locale,
        timezone_id=timezone_id or config.browser.timezone_id,
        viewport={"width": 1366, "height": 768},
    )
    return context


async def _auto_scroll(page: Page, *, max_scrolls: int, pause_ms: int) -> None:
    # Attempt to scroll and trigger lazy loading.
    last_height = 0
    for i in range(max_scrolls):
        await page.evaluate("window.scrollTo(0, document.body.scrollHeight);")
        await page.wait_for_timeout(pause_ms)
        new_height = await page.evaluate("document.body.scrollHeight")
        if new_height == last_height:
            break
        last_height = new_height


async def fetch_page(
    *,
    target_url: str,
    config: Config,
    wait_until: str,
    timeout_ms: int,
    want_screenshot: bool,
    max_scrolls: Optional[int],
    scroll_pause_ms: Optional[int],
    user_agent: Optional[str],
    locale: Optional[str],
    timezone_id: Optional[str],
) -> Dict[str, Any]:
    started = time.time()
    async with _launch_browser(config) as browser:
        context = await _new_context(browser, config, user_agent=user_agent, locale=locale, timezone_id=timezone_id)
        try:
            page = await context.new_page()
            await stealth_async(page)
            logger.debug("Navigating to %s", target_url)
            resp = await page.goto(target_url, wait_until=wait_until, timeout=timeout_ms)
            status = resp.status if resp else None
            final_url = page.url

            await _auto_scroll(
                page,
                max_scrolls=max_scrolls if max_scrolls is not None else config.browser.max_scrolls,
                pause_ms=scroll_pause_ms if scroll_pause_ms is not None else config.browser.scroll_pause_ms,
            )

            title = await page.title()
            try:
                html = await page.inner_html("body")
            except Exception:
                html = await page.content()
            try:
                text = await page.inner_text("body")
            except Exception:
                text = None

            links_js = """
                () => Array.from(document.querySelectorAll('a[href]')).map(a => ({
                  href: new URL(a.getAttribute('href'), location.href).href,
                  text: (a.textContent || '').trim()
                }))
            """
            links = await page.evaluate(links_js)
            # Deduplicate by href while preserving order
            seen = set()
            unique_links: List[Dict[str, str]] = []
            for item in links:
                href = item.get("href")
                if href and href not in seen:
                    seen.add(href)
                    unique_links.append({"href": href, "text": item.get("text")})

            screenshot_b64: Optional[str] = None
            if want_screenshot:
                try:
                    shot = await page.screenshot(full_page=True)
                    screenshot_b64 = base64.b64encode(shot).decode("ascii")
                except Exception:
                    screenshot_b64 = None

            return {
                "status": status,
                "final_url": final_url,
                "title": title,
                "html": html,
                "text": text,
                "links": unique_links,
                "screenshot_base64": screenshot_b64,
                "timing_ms": int((time.time() - started) * 1000),
            }
        finally:
            await context.close()


