## Open WebUI Remote Tools Server

Production-ready OpenAPI tool server exposing two tools for Open WebUI agents:

- Google Programmable Search Engine search
- Headless Chromium open web page with stealth anti-bot hardening

This follows the reference model in the upstream docs: [open-webui/openapi-servers](https://github.com/open-webui/openapi-servers).

### Features

- FastAPI server with CORS, health checks, structured logs
- Environment-only config (supports .env files)
- Google Custom Search (PSE) with retries, clean results
- Playwright Chromium with stealth (automation masking, UA/locale/timezone)
- Per-session limit for page fetch tool (default 20)
- Dockerfile and docker-compose for one-command runs

### Endpoints

- POST `/tools/google-search` — Top results via Google CSE
- POST `/tools/open-page` — Open and extract page HTML/text/links (optional screenshot)
- GET `/healthz` — liveness

### Quickstart (Local)

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
# Create a .env file (see variables below)
cat > .env << 'EOF'
GOOGLE_API_KEY=your_api_key
GOOGLE_CX=your_cse_id
LOG_LEVEL=INFO
LOG_FILE=logs/app.log
AUTH_TOKEN=change_me
EOF
python -m playwright install --with-deps chromium
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Open: `http://localhost:8000/docs`

### Quickstart (Docker)

```bash
# Create a .env file with your values (GOOGLE_API_KEY, GOOGLE_CX, AUTH_TOKEN, etc.)
cp .env .env.local || true
# Edit .env or .env.local

docker compose up --build
```

Open: `http://localhost:8000/docs`

### Open WebUI Integration

Point Open WebUI to your server base URL or import OpenAPI schema from `http://YOUR_HOST:8000/openapi.json`. See upstream guide: [open-webui/openapi-servers](https://github.com/open-webui/openapi-servers).

Suggested agent tool guidance:

- Google Search tool:
  "Use the google-search tool to retrieve up-to-date information from the internet via Google Programmable Search Engine. Prefer this tool when the user asks to find something (e.g., 'find', 'поищи', 'найди') or when the topic is time-sensitive (news, releases, events, prices). Do not call it for questions answerable from existing knowledge. Return the top results and cite sources."

- Open Page tool:
  "Use the open-page tool to open a specific URL and extract HTML, text, and links. You may call it multiple times in a session to follow links, but keep total calls below 20. Only call it if earlier steps are insufficient. Combine extracted information to improve answer quality."

### Configuration (env-only)

Key variables (via env or .env):

- GOOGLE_API_KEY — Google Programmable Search Engine API key
- GOOGLE_CX — Google CSE ID
- LOG_LEVEL — default INFO
- LOG_FILE — default logs/app.log
- CORS_ORIGINS — comma-separated list, default "*"
- BROWSER_HEADLESS — true|false, default true
- BROWSER_TIMEOUT_SECONDS — default 35
- BROWSER_LOCALE — default en-US
- BROWSER_TIMEZONE_ID — default UTC
- BROWSER_MAX_SCROLLS — default 8
- BROWSER_SCROLL_PAUSE_MS — default 400
- BROWSER_USER_AGENT — optional
- HTTP_PROXY / HTTPS_PROXY / BROWSER_PROXY — optional
- PAGE_TOOL_LIMIT — default 20
- SESSION_TTL_SECONDS — default 3600
- ENV_FILE — optional .env file path (default .env)
- AUTH_TOKEN — Bearer token required for all API calls

### Authorization

- Set `AUTH_TOKEN` in your `.env`.
- Clients must send header: `Authorization: Bearer <AUTH_TOKEN>`.
- If `AUTH_TOKEN` is unset, the API allows all requests (not recommended for production).

### Example Requests

- Google search:

```bash
curl -s -X POST http://localhost:8000/tools/google-search \
  -H 'Authorization: Bearer YOUR_TOKEN' \
  -H 'Content-Type: application/json' \
  -d '{"query":"latest llama news","num":10}' | jq
```

- Open page:

```bash
curl -s -X POST http://localhost:8000/tools/open-page \
  -H 'Authorization: Bearer YOUR_TOKEN' \
  -H 'Content-Type: application/json' \
  -d '{"url":"https://example.com","screenshot":false}' | jq
```

### Logging

Console and rotating file logs at `logs/app.log`. Requests log start/end with timing; tools log key steps and counts.

### Production Notes

- Run behind HTTPS reverse proxy
- Tune timeouts and concurrency
- Provide least-privilege Google CSE keys

### License

MIT. Upstream reference: [open-webui/openapi-servers](https://github.com/open-webui/openapi-servers).
