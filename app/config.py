import os
from typing import List, Optional

from dotenv import load_dotenv
from pydantic import BaseModel, Field


def _env_bool(name: str, default: bool) -> bool:
    val = os.getenv(name)
    if val is None:
        return default
    val_l = val.strip().lower()
    if val_l in {"1", "true", "yes", "on"}:
        return True
    if val_l in {"0", "false", "no", "off"}:
        return False
    return default


def _env_int(name: str, default: int) -> int:
    val = os.getenv(name)
    try:
        return int(val) if val is not None else default
    except Exception:
        return default


def _env_list(name: str, default: List[str]) -> List[str]:
    val = os.getenv(name)
    if not val:
        return default
    return [item.strip() for item in val.split(",") if item.strip()]


class GoogleConfig(BaseModel):
    api_key: str = Field(default_factory=lambda: os.getenv("GOOGLE_API_KEY", ""))
    cx: str = Field(default_factory=lambda: os.getenv("GOOGLE_CX", ""))
    search_num_default: int = Field(default_factory=lambda: _env_int("GOOGLE_SEARCH_NUM_DEFAULT", 10))
    timeout_seconds: int = Field(default_factory=lambda: _env_int("GOOGLE_TIMEOUT_SECONDS", 15))


class BrowserConfig(BaseModel):
    headless: bool = Field(default_factory=lambda: _env_bool("BROWSER_HEADLESS", True))
    timeout_seconds: int = Field(default_factory=lambda: _env_int("BROWSER_TIMEOUT_SECONDS", 35))
    locale: str = Field(default_factory=lambda: os.getenv("BROWSER_LOCALE", "en-US"))
    timezone_id: str = Field(default_factory=lambda: os.getenv("BROWSER_TIMEZONE_ID", "UTC"))
    max_scrolls: int = Field(default_factory=lambda: _env_int("BROWSER_MAX_SCROLLS", 8))
    scroll_pause_ms: int = Field(default_factory=lambda: _env_int("BROWSER_SCROLL_PAUSE_MS", 400))
    user_agent: Optional[str] = Field(default_factory=lambda: os.getenv("BROWSER_USER_AGENT"))
    proxy: Optional[str] = Field(default_factory=lambda: os.getenv("HTTP_PROXY") or os.getenv("HTTPS_PROXY") or os.getenv("BROWSER_PROXY"))


class ServerConfig(BaseModel):
    log_level: str = Field(default_factory=lambda: os.getenv("LOG_LEVEL", "INFO"))
    log_file: str = Field(default_factory=lambda: os.getenv("LOG_FILE", "logs/app.log"))
    cors_origins: List[str] = Field(default_factory=lambda: _env_list("CORS_ORIGINS", ["*"]))


class RateLimitConfig(BaseModel):
    page_tool_limit: int = Field(default_factory=lambda: _env_int("PAGE_TOOL_LIMIT", 20))
    session_ttl_seconds: int = Field(default_factory=lambda: _env_int("SESSION_TTL_SECONDS", 3600))


class Config(BaseModel):
    google: GoogleConfig
    browser: BrowserConfig = BrowserConfig()
    server: ServerConfig = ServerConfig()
    rate_limit: RateLimitConfig = RateLimitConfig()


def load_config() -> Config:
    # Load .env automatically if present; ENV_FILE can override path
    env_file = os.getenv("ENV_FILE", ".env")
    if os.path.isfile(env_file):
        load_dotenv(env_file)

    google_cfg = GoogleConfig()
    browser_cfg = BrowserConfig()
    server_cfg = ServerConfig()
    rl_cfg = RateLimitConfig()

    return Config(google=google_cfg, browser=browser_cfg, server=server_cfg, rate_limit=rl_cfg)


