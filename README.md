# Legal Form Fill

Automated document extraction and form population system. Upload a passport and/or G-28 form, extract structured data using Claude's vision API, and automatically fill a web form using Playwright browser automation.

## Architecture

```
┌─────────────┐     ┌──────────────┐     ┌─────────────────┐
│  React UI   │────▶│  FastAPI      │────▶│  Claude Vision   │
│  (Vite/TS)  │◀────│  Backend      │◀────│  (Extraction)    │
└─────────────┘     └──────┬───────┘     └─────────────────┘
                           │
                    ┌──────▼───────┐     ┌─────────────────┐
                    │  Playwright   │────▶│  Target Form     │
                    │  (Headless)   │     │  (GitHub Pages)  │
                    └──────────────┘     └─────────────────┘
```

**Tech Stack:** FastAPI, Claude API (Sonnet), Playwright, React, TypeScript, Tailwind CSS

## Quick Start

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

Open **http://localhost:5173** in your browser.

## Workflow

1. **Upload** — Drag and drop a passport image and/or G-28 PDF
2. **Review** — Verify and edit the AI-extracted data
3. **Fill** — Watch Playwright fill the form in real-time, then view the screenshot

## Features

- **AI-Powered Extraction** — Claude's vision model reads passports (any country) and G-28 forms, extracting structured data including names, dates, addresses, and legal identifiers
- **Editable Review** — All extracted fields can be corrected before form submission
- **Real-Time Progress** — WebSocket streaming shows each field being filled live
- **Robust Handling** — Tolerates varied document formats, missing fields, and handwritten entries
- **Screenshot Capture** — Full-page screenshot of the filled form for verification

## Project Structure

```
backend/
  main.py                    # FastAPI app entry point
  config.py                  # Environment settings
  models/schemas.py          # Pydantic data models
  routers/
    upload.py                # File upload endpoint
    extract.py               # Claude extraction endpoint
    form_fill.py             # Playwright fill + WebSocket progress
  services/
    document_processor.py    # PDF→image conversion (PyMuPDF)
    claude_extractor.py      # Claude vision API integration
    form_filler.py           # Playwright automation engine

frontend/
  src/
    App.tsx                  # 3-step wizard flow
    api.ts                   # API client
    types.ts                 # TypeScript interfaces
    components/
      FileUpload.tsx         # Drag-and-drop upload zones
      ExtractedData.tsx      # Editable data review form
      ProgressView.tsx       # Real-time fill progress
      StepIndicator.tsx      # Wizard step navigation
```

## Example Documents

The `example/` folder contains:
- `Example_G-28.pdf` — A sample filled G-28 form (4 pages)
- `Form A-28_ Legal Documentation.html` — Saved copy of the target form for reference
