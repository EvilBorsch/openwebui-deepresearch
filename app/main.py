import logging
from typing import Dict

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from starlette.responses import JSONResponse

from .config import load_config
from .google_search import google_search
from .logging_utils import setup_logging
from .models import GoogleSearchRequest, GoogleSearchResponse, OpenPageRequest, OpenPageResponse
from .page_fetcher import fetch_page
from .middleware import RequestLoggingMiddleware
from .rate_limit import SessionCounter


config = load_config()
setup_logging(config.server.log_level, config.server.log_file)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Open WebUI Remote Tools",
    version="1.0.0",
    description=(
        "Two production-ready tools for LLM agents: a Google Programmable Search Engine (PSE) search tool and a "
        "headless-browser web page fetcher, exposed via a simple, secure OpenAPI server."
    ),
    contact={"name": "Remote Tools", "url": "https://github.com/open-webui/openapi-servers"},
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=config.server.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(RequestLoggingMiddleware, logger=logging.getLogger("request"))


# In-memory per-session usage counter for the page open tool
_session_counter = SessionCounter(ttl_seconds=config.rate_limit.session_ttl_seconds)


@app.get("/", tags=["system"])
async def root() -> Dict[str, str]:
    return {
        "name": "Open WebUI Remote Tools",
        "version": "1.0.0",
        "health": "ok",
    }


@app.get("/healthz", tags=["system"])  # Health probe
async def healthz() -> Dict[str, str]:
    return {"status": "ok"}


@app.post(
    "/tools/google-search",
    response_model=GoogleSearchResponse,
    tags=["tools"],
    summary="Google Programmable Search Engine (PSE)",
    description=(
        "Use this tool to retrieve up-to-date information from the public internet via Google Programmable Search Engine.\n\n"
        "When to use:\n"
        "- Prefer this tool whenever user intent implies a need to 'find' fresh/unknown facts online (e.g., contains 'find', 'поищи', 'найди', 'lookup', 'search').\n"
        "- Use it for topics likely to change or be time-sensitive (news, releases, prices, events, stats).\n"
        "- Do NOT call it for self-contained questions solvable with your current knowledge.\n\n"
        "What it returns: Top results with titles, URLs, and snippets. Combine results sensibly, cross-check if needed, and cite sources in your answer."
    ),
)
async def tool_google_search(req: GoogleSearchRequest) -> GoogleSearchResponse:
    if not config.google.api_key or not config.google.cx:
        logger.error("Google API key or CX missing")
        raise HTTPException(status_code=500, detail="Google search is not configured. Set GOOGLE_API_KEY and GOOGLE_CX.")
    return await google_search(req, config)


@app.post(
    "/tools/open-page",
    response_model=OpenPageResponse,
    tags=["tools"],
    summary="Fetch page content for continued research",
    description=(
        "Fetch the content of a web page (HTML, plain text, and links) to continue researching a user's request. Optionally capture a screenshot.\n\n"
        "Usage for the model:\n"
        "- Call when you need primary page content to proceed after search results or to verify details.\n"
        "- You may call this tool multiple times in a session to follow links or gather details; keep total calls under 20 per session.\n"
        "- Do not call if you already have enough information to answer confidently.\n"
        "- Prefer reusing previously fetched content instead of re-fetching the same page.\n"
        "- Combine extracted content to produce a high-quality answer and cite sources when appropriate."
    ),
)
async def tool_open_page(req: OpenPageRequest, request: Request) -> OpenPageResponse:
    # Derive a session id if not provided: header -> provided -> IP+UA
    header_sid = request.headers.get("x-session-id")
    forwarded_for = request.headers.get("x-forwarded-for")
    client_ip = None
    if forwarded_for:
        client_ip = forwarded_for.split(",")[0].strip()
    elif request.client:
        client_ip = request.client.host
    user_agent = request.headers.get("user-agent", "-")
    session_id = req.session_id or header_sid or f"{client_ip or 'unknown'}|{user_agent[:40]}"

    current = _session_counter.increment_and_get(session_id)
    if current > config.rate_limit.page_tool_limit:
        logger.warning("Session %s exceeded open-page limit (%s)", session_id, config.rate_limit.page_tool_limit)
        raise HTTPException(status_code=429, detail="Session exceeded allowed open-page calls. Please reduce tool usage.")

    try:
        data = await fetch_page(
            target_url=str(req.url),
            config=config,
            wait_until=req.wait_until,
            timeout_ms=req.timeout_ms,
            want_screenshot=req.screenshot,
            max_scrolls=req.max_scrolls,
            scroll_pause_ms=req.scroll_pause_ms,
            user_agent=req.user_agent,
            locale=req.locale,
            timezone_id=req.timezone_id,
        )
        return OpenPageResponse(
            url=req.url,
            final_url=data.get("final_url"),
            status=data.get("status"),
            title=data.get("title"),
            html=data.get("html"),
            text=data.get("text"),
            links=data.get("links"),
            screenshot_base64=data.get("screenshot_base64"),
            timing_ms=data.get("timing_ms"),
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("open-page failed: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


@app.exception_handler(Exception)
async def unhandled_exception_handler(_, exc: Exception):  # pragma: no cover
    logger.exception("Unhandled error: %s", exc)
    return JSONResponse(status_code=500, content={"detail": "Internal Server Error"})


