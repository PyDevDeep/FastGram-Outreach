# FastGram — Instagram Outreach Automation MVP 🚀

> A self-hosted, safety-first Instagram DM outreach pipeline built with FastAPI and n8n.
> Sends personalized cold DMs, tracks replies, classifies leads, and protects accounts
> through gradient warm-up, proxy rotation, and automatic pause/resume logic.

![Python](https://img.shields.io/badge/Python-3.13-blue?logo=python)
![FastAPI](https://img.shields.io/badge/FastAPI-0.11x-009688?logo=fastapi)
![n8n](https://img.shields.io/badge/n8n-self--hosted-orange?logo=n8n)
![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?logo=docker)
![License](https://img.shields.io/badge/License-[INSERT]-green)
![Build](https://img.shields.io/badge/build-passing-brightgreen)

---

## ⚠️ Disclaimer

This project interacts with Instagram via the unofficial `instagrapi` library.
Use at your own risk. Automated messaging may violate Instagram's Terms of Service.
The authors are not responsible for account bans or other consequences.

---

## ✨ Features

- **Automated DM outreach** — sends batched Instagram direct messages to contacts
  sourced from Google Sheets, respecting configurable daily limits
- **Gradient account warm-up** — automatically ramps daily message limits from 5 to 50
  over a 15-day schedule to reduce ban risk on new accounts
- **Proxy rotation** — integrates with a 4G/mobile proxy provider REST API;
  rotates IP after every 50 messages or 24 hours
- **Human-like delays** — Gaussian-distributed inter-message delays and
  typing-speed simulation to mimic organic behavior
- **Reply tracking & lead classification** — polls Instagram inbox every 30 minutes,
  classifies responses as `Interested` / `Not Interested` / `Unclear`,
  and writes tags back to Google Sheets
- **Auto-pause & auto-resume** — detects `ChallengeRequired` / `LoginRequired` errors,
  pauses outreach for 24 hours, validates session health before resuming
- **Telegram alerts** — instant notifications on account block events and
  new interested leads via n8n webhook workflows
- **API key authentication** — all FastAPI endpoints protected by `X-API-Key` header
- **Encrypted session storage** — Instagram session persisted to an encrypted JSON file
- **Fully containerized** — FastAPI backend and n8n orchestrator run in Docker Compose
  on a shared internal network

---

## 🛠 Tech Stack

| Layer | Technology |
|---|---|
| API Backend | [FastAPI](https://fastapi.tiangolo.com/) + [Uvicorn](https://www.uvicorn.org/) |
| Instagram Library | [instagrapi](https://github.com/subzeroid/instagrapi) |
| Workflow Orchestrator | [n8n](https://n8n.io/) (self-hosted) |
| Data Layer | [Google Sheets](https://developers.google.com/sheets/api) via `gspread` |
| Configuration | [Pydantic Settings](https://docs.pydantic.dev/latest/concepts/pydantic_settings/) |
| Containerization | [Docker](https://www.docker.com/) + [Docker Compose](https://docs.docker.com/compose/) |
| Dependency Management | [Poetry](https://python-poetry.org/) |
| Linting & Formatting | [Ruff](https://docs.astral.sh/ruff/) |
| State Persistence | JSON file (MVP); Redis-compatible for production |
| Proxy | 4G Mobile Proxy with provider REST API rotation |

---

## 📐 Architecture Overview

```
┌─────────────────────────────────────────────────────┐
│                    n8n (port 5679)                   │
│                                                      │
│  ┌─────────────────┐   ┌──────────────────────────┐ │
│  │ Outreach Trigger │   │  Reply Polling (30 min)  │ │
│  │  (cron 10:00)   │   │  → FastAPI check-replies │ │
│  └────────┬────────┘   └──────────────┬───────────┘ │
│           │                           │              │
│  ┌────────▼────────┐   ┌──────────────▼───────────┐ │
│  │  Warmup Trigger  │   │  Telegram Lead Alert     │ │
│  │  (cron 00:01)   │   │  (if interested > 0)     │ │
│  └────────┬────────┘   └──────────────────────────┘ │
│           │                                          │
│  ┌────────▼────────┐                                 │
│  │  Block Alert    │                                 │
│  │  (webhook POST) │                                 │
│  └─────────────────┘                                 │
└──────────────────────┬──────────────────────────────┘
                       │ HTTP (internal network)
┌──────────────────────▼──────────────────────────────┐
│              FastAPI Backend (port 8003)             │
│                                                      │
│  OutreachEngine  │  ReplyTracker  │  WarmupManager  │
│  PauseManager    │  ProxyRotator  │  SheetsClient   │
└──────────────────────────────────────────────────────┘
```

---

## 📦 Installation

### Prerequisites

- Docker & Docker Compose
- A Google Cloud service account with Sheets API enabled (`credentials.json`)
- A 4G/mobile proxy with REST API access
- A Telegram bot token and chat ID for alerts

### 1. Clone the repository

```bash
git clone https://github.com/PyDevDeep/FastGram-Outreach.git
cd fastgram
```

### 2. Create environment file

```bash
cp .env.example .env
```

Edit `.env` with your credentials:

```env
# Instagram
INSTAGRAM_USERNAME=your_username
INSTAGRAM_PASSWORD=your_password

# Security
API_KEY=your_secure_api_key_here
SESSION_ENCRYPTION_KEY=your_32_byte_key

# Google Sheets
GOOGLE_SHEETS_ID=your_spreadsheet_id
GOOGLE_APPLICATION_CREDENTIALS=/app/credentials.json

# Proxy
PROXY_URL=http://user:pass@host:port
PROXY_API_URL=https://api.your-proxy-provider.com
PROXY_API_KEY=your_proxy_api_key

# n8n Webhooks
N8N_WEBHOOK_URL=http://fastgram_n8n:5678/webhook/alert-block

# Limits
DAILY_MESSAGE_LIMIT=20
MIN_DELAY_SECONDS=30
MAX_DELAY_SECONDS=60
```

### 3. Place Google credentials

```bash
cp /path/to/your/credentials.json ./credentials.json
```

### 4. Start services

```bash
docker compose up -d
```

API is available at `http://localhost:8003`. n8n UI is available at `http://localhost:5679`.

---

## ▶️ Usage

### Import n8n Workflows

In the n8n UI, import the four workflows from `n8n/workflows/`:

| File | Purpose |
|---|---|
| `outreach_trigger.json` | Daily cron at 10:00 — starts outreach batch |
| `warmup_trigger.json` | Daily cron at 00:01 — increments warm-up day |
| `reply_polling.json` | Every 30 min — polls replies and alerts on leads |
| `alert_on_block.json` | Webhook — fires Telegram alert on account block |

Set your `YOUR_TELEGRAM_CHAT_ID` in the Telegram Alert nodes.

### API Endpoints

All requests require the header: `X-API-Key: your_secure_api_key_here`

```bash
# Start outreach batch
POST http://localhost:8003/outreach/start
Content-Type: application/json
{"dry_run": false}

# Check for new replies and classify leads
GET http://localhost:8003/tracking/check-replies

# Increment warm-up day counter (also called by n8n cron)
POST http://localhost:8003/outreach/warmup/increment

# Health check
GET http://localhost:8003/health

# Warmup status
GET http://localhost:8003/admin/warmup-status

# Account health check
GET http://localhost:8003/admin/account-health

# Manual resume after pause
POST http://localhost:8003/admin/resume-pause
```

### Google Sheets Structure

The `Contacts` sheet must contain these columns:

| Column | Description |
|---|---|
| `Instagram Username` | Target account handle (without `@`) |
| `Instagram User ID` | Numeric user ID (populated after first contact) |
| `Status` | `Pending` / `Sent` / `Replied` / `Error` |
| `Tag` | `Interested` / `Not Interested` / `Unclear` (set by ReplyTracker) |

### Validate connections before first run

```bash
# Test Instagram authentication
docker compose exec api python scripts/test_instagram.py

# Test Google Sheets access
docker compose exec api python scripts/test_sheets.py
```

---

## 🔥 Warm-up Schedule

| Days | Daily Message Limit |
|---|---|
| 1–3 | 5 |
| 4–6 | 10 |
| 7–9 | 15 |
| 10–12 | 25 |
| 13–14 | 35 |
| 15+ | 50 (warm-up deactivates) |

---

## 💰 Estimated Monthly Cost (MVP)

| Resource | Cost |
|---|---|
| VPS (n8n + FastAPI, e.g. Hetzner CX22) | $5–10 |
| 4G Mobile Proxy (1 slot with rotation) | $30–80 |
| Google Sheets API | Free |
| Domain + SSL (optional) | $0–5 |
| **Total** | **$35–95** |

---

## 🔒 Security Notes

- The `X-API-Key` header is required on all endpoints; unauthorized requests return HTTP 401
- Instagram credentials and session data are never exposed via the API
- `credentials.json` is mounted read-only inside the container
- Pre-commit hooks block accidental commits of private keys (via `detect-private-key`)
- `sessions/session.json` and `.env` are listed in `.gitignore`

---

## 🗺️ Roadmap

- [ ] Phase 1 — PostgreSQL migration (replace Google Sheets)
- [ ] Phase 2 — Sentry integration for error tracking
- [ ] Phase 3 — LLM-based reply classification (replace keyword matching)
- [ ] Phase 4 — Playwright fallback for API-blocked scenarios

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/your-feature`
3. Install pre-commit hooks: `pre-commit install`
4. Make changes and ensure linting passes: `ruff check . && ruff format .`
5. Submit a pull request with a clear description

---

## 📄 License

[INSERT LICENSE TYPE]
