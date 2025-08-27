from typing import List, Literal, Optional

from pydantic import BaseModel, Field, HttpUrl


class GoogleSearchRequest(BaseModel):
    query: str = Field(..., description="User query to search on Google via Programmable Search Engine.")
    num: int = Field(10, ge=1, le=10, description="Number of results to return (1-10).")
    language: Optional[str] = Field(None, description="Optional language restriction (e.g., 'lang_en').")
    region: Optional[str] = Field(None, description="Optional region/country code for geolocation bias (e.g., 'us').")


class SearchResult(BaseModel):
    position: int
    title: str
    link: HttpUrl
    display_link: Optional[str] = None
    snippet: Optional[str] = None
    favicon: Optional[str] = None


class GoogleSearchResponse(BaseModel):
    source: Literal["google_cse"] = "google_cse"
    query: str
    num: int
    results: List[SearchResult]


class OpenPageRequest(BaseModel):
    url: HttpUrl = Field(..., description="The URL to open and extract content from.")
    session_id: Optional[str] = Field(
        None,
        description=(
            "Optional client/session identifier to enforce per-session usage limits. "
            "If omitted, the server will derive a best-effort ID from request headers/IP."
        ),
    )
    screenshot: bool = Field(False, description="Whether to capture a base64-encoded screenshot of the full page.")
    wait_until: Literal["load", "domcontentloaded", "networkidle", "commit"] = Field(
        "networkidle", description="Wait condition before extracting page content."
    )
    timeout_ms: int = Field(35000, description="Navigation timeout in milliseconds.")
    max_scrolls: Optional[int] = Field(None, description="Override configured max scroll attempts for lazy-loaded content.")
    scroll_pause_ms: Optional[int] = Field(None, description="Pause between scroll steps in milliseconds.")
    user_agent: Optional[str] = Field(None, description="Custom User-Agent string. Defaults to a modern desktop UA.")
    locale: Optional[str] = Field(None, description="Locale/language (e.g., 'en-US').")
    timezone_id: Optional[str] = Field(None, description="IANA timezone (e.g., 'America/New_York').")


class LinkItem(BaseModel):
    href: HttpUrl
    text: Optional[str] = None


class OpenPageResponse(BaseModel):
    url: HttpUrl
    final_url: Optional[HttpUrl]
    status: Optional[int]
    title: Optional[str]
    html: Optional[str]
    text: Optional[str]
    links: List[LinkItem] = Field(default_factory=list)
    screenshot_base64: Optional[str] = None
    timing_ms: Optional[int] = None


