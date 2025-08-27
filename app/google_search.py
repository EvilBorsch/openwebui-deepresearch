import logging
from typing import List, Optional

import httpx
from tenacity import RetryCallState, retry, stop_after_attempt, wait_exponential

from .config import Config
from .models import GoogleSearchRequest, GoogleSearchResponse, SearchResult

logger = logging.getLogger(__name__)


def _before_sleep(retry_state: RetryCallState) -> None:  # pragma: no cover
    last_exc = retry_state.outcome.exception() if retry_state.outcome else None
    logger.warning(
        "Google CSE request failed (attempt %s): %s",
        retry_state.attempt_number,
        str(last_exc) if last_exc else "unknown error",
    )


@retry(wait=wait_exponential(multiplier=0.5, min=0.5, max=4), stop=stop_after_attempt(3), before_sleep=_before_sleep)
async def _fetch_google_cse(
    *,
    api_key: str,
    cx: str,
    q: str,
    num: int,
    language: Optional[str],
    region: Optional[str],
    timeout_seconds: int,
) -> dict:
    params = {"key": api_key, "cx": cx, "q": q, "num": num, "safe": "off"}
    if language:
        params["lr"] = language
    if region:
        params["gl"] = region

    async with httpx.AsyncClient(timeout=timeout_seconds) as client:
        resp = await client.get("https://www.googleapis.com/customsearch/v1", params=params)
        resp.raise_for_status()
        return resp.json()


def _parse_results(payload: dict, requested_num: int) -> List[SearchResult]:
    items = payload.get("items") or []
    results: List[SearchResult] = []
    for idx, item in enumerate(items[:requested_num], start=1):
        title = item.get("title") or ""
        link = item.get("link") or ""
        display_link = item.get("displayLink")
        snippet = item.get("snippet")
        favicon = None
        if display_link:
            favicon = f"https://www.google.com/s2/favicons?domain={display_link}&sz=64"

        try:
            result = SearchResult(
                position=idx,
                title=title,
                link=link,
                display_link=display_link,
                snippet=snippet,
                favicon=favicon,
            )
            results.append(result)
        except Exception as e:  # pragma: no cover
            logger.debug("Skipping malformed result #%s: %s", idx, e)
    return results


async def google_search(req: GoogleSearchRequest, config: Config) -> GoogleSearchResponse:
    logger.info("[Google Search] query='%s' num=%s", req.query, req.num)
    data = await _fetch_google_cse(
        api_key=config.google.api_key,
        cx=config.google.cx,
        q=req.query,
        num=req.num or config.google.search_num_default,
        language=req.language,
        region=req.region,
        timeout_seconds=config.google.timeout_seconds,
    )
    results = _parse_results(data, req.num or config.google.search_num_default)
    logger.info("[Google Search] returned %s results", len(results))
    return GoogleSearchResponse(query=req.query, num=len(results), results=results)


