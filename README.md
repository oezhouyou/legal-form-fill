# Legal Form Fill

Automated document extraction and form population system. Upload a passport and/or G-28 form, extract structured data using Claude's vision API, and automatically fill a web form using Playwright browser automation.

## Architecture

```
┌─────────────┐     ┌──────────────┐     ┌─────────────────┐
│  React UI   │────>│  FastAPI     │────>│  Claude Vision  │
│  (Vite/TS)  │<────│  Backend     │<────│  (Extraction)   │
└─────────────┘     └──────┬───────┘     └─────────────────┘
                           │
                    ┌──────▼───────┐     ┌─────────────────┐
                    │  Playwright  │────>│  Target Form    │
                    │  (Headless)  │     │  (GitHub Pages) │
                    └──────────────┘     └─────────────────┘
```

**Tech Stack:** FastAPI · Claude API (Opus) · Playwright · React 19 · TypeScript · Tailwind CSS v4

## Quick Start (Docker)

### Prerequisites

- Docker & Docker Compose
- An [Anthropic API key](https://console.anthropic.com/)

### Run

```bash
git clone <repo-url>
cd legal-form-fill
cp .env.example .env
# Edit .env and add your ANTHROPIC_API_KEY

docker compose up --build
```

Open **http://localhost:3000** in your browser.

The backend includes a health check — Docker Compose will wait for it to pass before starting the frontend. You can verify readiness at any time:

```bash
curl http://localhost:3000/api/health
# {"status":"ok","checks":{"anthropic_api_key":"configured","upload_directory":"writable"}}
```

## Local Development (without Docker)

### Prerequisites

- Python 3.11+
- Node.js 18+
- An [Anthropic API key](https://console.anthropic.com/)

### 1. Clone & Configure

```bash
git clone <repo-url>
cd legal-form-fill
cp .env.example backend/.env
# Edit backend/.env and add your ANTHROPIC_API_KEY
```

### 2. Backend Setup

```bash
cd backend
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
playwright install chromium
```

### 3. Frontend Setup

```bash
cd frontend
npm install
```

### 4. Run

In two terminals:

```bash
# Terminal 1 — Backend (from backend/)
uvicorn main:app --reload --port 8000

# Terminal 2 — Frontend (from frontend/)
npm run dev
```

Open **http://localhost:5173** in your browser. The Vite dev server proxies `/api` and `/ws` requests to the backend automatically.

## Testing

The backend includes a comprehensive test suite (63 tests) covering schemas, services, and API endpoints. All tests run fully offline — no API key or external services required.

```bash
cd backend
pip install -r requirements.txt   # includes pytest, pytest-asyncio, httpx
pytest -v
```

```
tests/test_schemas.py            16 passed   Pydantic model validation & constraints
tests/test_document_processor.py 10 passed   PDF rendering, image resize, doc detection
tests/test_claude_extractor.py   14 passed   JSON parsing, helpers, mocked extraction
tests/test_form_filler.py         7 passed   Field resolver, constructor defaults
tests/test_upload_router.py       3 passed   Upload endpoint (success, reject, detect)
tests/test_extract_router.py      3 passed   Extraction endpoint (mock, warning, error)
tests/test_form_fill_router.py    3 passed   Fill endpoint, screenshot retrieval
tests/test_health.py              2 passed   Health check (ok, degraded)
```

## Workflow

1. **Upload** — Drag and drop a passport image and/or G-28 PDF
2. **Review** — Verify and edit the AI-extracted data in collapsible sections
3. **Fill** — Watch Playwright fill the form field-by-field in real time, then view the screenshot

## Features

- **AI-Powered Extraction** — Claude's vision model reads passports (any country) and G-28 forms, extracting structured data including names, dates, addresses, and legal identifiers
- **Editable Review** — All extracted fields can be corrected before form population
- **Real-Time Progress** — WebSocket streaming shows each field being filled live with a progress ring
- **Robust Handling** — Tolerates varied document formats, missing fields, non-US addresses, and handwritten entries
- **Screenshot Capture** — Full-page screenshot of the filled form for verification
- **Production-Ready Backend** — Structured logging, global error handlers, health checks, input validation, and OpenAPI documentation

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/upload` | Upload a document (PDF, JPG, PNG). Returns file ID and preview thumbnail. |
| `POST` | `/api/extract` | Extract structured data from uploaded documents via Claude vision. |
| `POST` | `/api/fill-form` | Launch Playwright to auto-fill the target form. Returns screenshot UUID. |
| `GET` | `/api/screenshots/{id}` | Download a form-fill screenshot (PNG). |
| `GET` | `/api/health` | Service health check with dependency validation. |
| `WS` | `/ws/progress` | Real-time field-by-field progress events during form filling. |

Interactive API documentation is available at `http://localhost:8000/docs` when running the backend directly.

## Configuration

All settings are configurable via environment variables or a `.env` file. See [.env.example](.env.example) for the full list.

| Variable | Default | Description |
|----------|---------|-------------|
| `ANTHROPIC_API_KEY` | *(required)* | Anthropic API key for Claude vision |
| `CLAUDE_MODEL` | `claude-opus-4-6` | Claude model ID for extraction |
| `CLAUDE_MAX_TOKENS` | `4096` | Max response tokens for Claude API |
| `TARGET_FORM_URL` | `https://mendrika-alma.github.io/form-submission/` | URL of the form to auto-fill |
| `CORS_ORIGINS` | `localhost:5173,3000` | Allowed CORS origins |
| `MAX_FILE_SIZE_MB` | `20` | Maximum upload file size |
| `PLAYWRIGHT_TIMEOUT_MS` | `30000` | Playwright page-load timeout |
| `LOG_LEVEL` | `INFO` | Python logging level |

## Project Structure

```
legal-form-fill/
├── docker-compose.yml
├── .env.example
├── .gitignore
│
├── backend/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── pytest.ini
│   ├── main.py                    # FastAPI app, lifespan, error handlers
│   ├── config.py                  # Pydantic Settings (env-driven)
│   ├── models/
│   │   └── schemas.py             # Pydantic data models (9 classes)
│   ├── routers/
│   │   ├── upload.py              # Document upload endpoint
│   │   ├── extract.py             # Claude extraction endpoint
│   │   └── form_fill.py           # Playwright fill + WebSocket progress
│   ├── services/
│   │   ├── document_processor.py  # PDF→image (PyMuPDF), previews
│   │   ├── claude_extractor.py    # Claude vision API integration
│   │   └── form_filler.py         # Playwright automation engine
│   └── tests/
│       ├── conftest.py            # Shared fixtures
│       ├── test_schemas.py
│       ├── test_document_processor.py
│       ├── test_claude_extractor.py
│       ├── test_form_filler.py
│       ├── test_upload_router.py
│       ├── test_extract_router.py
│       ├── test_form_fill_router.py
│       └── test_health.py
│
├── frontend/
│   ├── Dockerfile
│   ├── nginx.conf                 # Reverse proxy (API + WebSocket)
│   ├── package.json
│   ├── vite.config.ts
│   └── src/
│       ├── App.tsx                # 3-step wizard flow
│       ├── api.ts                 # API client + WebSocket helper
│       ├── types.ts               # TypeScript interfaces
│       └── components/
│           ├── FileUpload.tsx     # Drag-and-drop upload zones
│           ├── ExtractedData.tsx  # Editable data review form
│           ├── ProgressView.tsx   # Real-time fill progress
│           └── StepIndicator.tsx  # Wizard step navigation
│
└── example/
    ├── Example_G-28.pdf           # Sample G-28 form (4 pages)
    └── Form A-28_ Legal Documentation.html
```

## Docker Details

The application runs as two containers behind an nginx reverse proxy:

- **Backend** — Python 3.12, FastAPI, runs as non-root `appuser`, includes Chromium for Playwright
- **Frontend** — Multi-stage build (Node 20 → nginx:alpine), serves static files and proxies API/WebSocket traffic

Both containers include:
- `restart: unless-stopped` for automatic recovery
- Health checks for dependency-aware startup ordering
- Log rotation (10 MB max, 3 files)

```bash
# Rebuild after code changes
docker compose up -d --build

# View backend logs
docker logs -f legal-form-fill-backend

# Check container health
docker compose ps
```

## Example Documents

The `example/` folder contains:
- `Example_G-28.pdf` — A sample filled G-28 form (4 pages)
- `Form A-28_ Legal Documentation.html` — Saved copy of the target form for reference
