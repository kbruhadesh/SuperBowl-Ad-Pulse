# SuperBowl Ad Pulse 🏈⚡

**Real-time AI-powered ad generation from live sports moments**

Transform game highlights into instant marketing opportunities. This system uses Google Gemini for video understanding and Groq for rapid ad copy generation — with explainable scoring and honest metrics.

---

## 🎯 What It Does

1. **Upload** a game video
2. **Gemini** analyzes 5-second segments for significant events
3. **Scoring Engine** evaluates each event (0-10 score)
4. **Decision Layer** determines if an ad should be generated
5. **Groq** generates contextual ad copy
6. **Database** stores everything for analysis

---

## 🏗️ Architecture

```
backend/
├── api/
│   ├── routes.py      # FastAPI endpoints (orchestration only)
│   └── schemas.py     # Pydantic request/response models
├── core/
│   ├── scoring.py     # Event scoring engine (NO AI)
│   └── decision.py    # Ad decision layer (NO AI)
├── services/
│   ├── gemini.py      # Gemini video analysis
│   └── groq.py        # Groq ad generation
├── db/
│   ├── database.py    # SQLite + SQLAlchemy setup
│   └── models.py      # ORM models (events, ads, metrics)
└── main.py            # FastAPI app entry point

frontend/
└── app-react/         # React + Vite dashboard

scripts/
└── reset_db.py        # Database reset utility
```

---

## 🔑 Key Design Principles

### ✅ What We Do

| Principle | Implementation |
|-----------|----------------|
| **Separation of Concerns** | Gemini observes, Scoring evaluates, Decision decides, Groq creates |
| **Explainable AI** | Every score and decision has a documented reason |
| **Database-First** | SQLite replaces JSON files; single source of truth |
| **Honest Metrics** | Real latency, confidence, and discard rates displayed |
| **Deterministic Scoring** | Pure Python, no LLM, unit-testable |

### ❌ What We Avoid

| Anti-Pattern | Why |
|--------------|-----|
| No local multimodal models | Complexity without value |
| No background daemons | Keep it simple |
| No fake "live" | Honest UI only |
| No JSON as storage | Use a real database |
| No premature scaling | Solve real problems first |

---

## 🚀 Quick Start

### Prerequisites

- Python 3.9+
- Node.js 20+
- API Keys: `GOOGLE_API_KEY` and `GROQ_API_KEY`

### 1. Clone & Setup

```bash
git clone https://github.com/KoushikBruPillai/SuperBowl-Ad-Pulse.git
cd SuperBowl-Ad-Pulse

# Create virtual environment
python -m venv .venv
.venv\Scripts\activate  # Windows
# source .venv/bin/activate  # macOS/Linux

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
cp .env.example .env
# Edit .env with your API keys:
# GOOGLE_API_KEY=your_gemini_key
# GROQ_API_KEY=your_groq_key
```

### 3. Start Backend

```bash
# From project root
python -m uvicorn backend.main:app --reload --port 8000
```

### 4. Start Frontend

```bash
cd frontend/app-react
npm install
npm run dev
```

Open http://localhost:5173

---

## 📊 Evaluation Metrics (Phase 10)

The system tracks and displays these metrics in real-time:

| Metric | Description | Target |
|--------|-------------|--------|
| **Avg Gemini Latency** | Time for video segment analysis | < 3000ms |
| **Avg Groq Latency** | Time for ad generation | < 500ms |
| **Discard Rate** | % segments with no ad | 30-60% |
| **Ads per Match** | Total ads generated | 10-30 |

Access via: `GET /api/metrics`

---

## 🧠 Scoring Engine

The scoring engine is **pure Python** with **no AI**. It's deterministic and defensible.

### Scoring Rules

| Condition | Score Modifier |
|-----------|----------------|
| Goal/Touchdown | +4 |
| High Intensity | +2 |
| Loud Crowd | +2 |
| Medium Intensity | +1 |
| Low Confidence (< 0.5) | −3 |
| Unknown Event Type | −2 |

**Final Score: 0-10** (clamped)

### Decision Thresholds

| Score Range | Decision |
|-------------|----------|
| < 4 | Ignore (no ad) |
| 4 – 6.9 | Soft ad |
| ≥ 7 | Aggressive ad |

---

## 📡 API Endpoints

| Method | Endpoint | Purpose |
|--------|----------|---------|
| `POST` | `/api/upload-video` | Upload video to Gemini |
| `POST` | `/api/analyze-segment` | Full pipeline for one segment |
| `GET` | `/api/events` | Read events from database |
| `GET` | `/api/ads` | Read ads from database |
| `GET` | `/api/metrics` | Get pipeline metrics |
| `POST` | `/api/reset` | Clear database |
| `GET` | `/api/health` | Health check |

---

## 🗄️ Database Schema

### `events` Table

| Column | Type | Purpose |
|--------|------|---------|
| id | INTEGER | Primary key |
| start_sec | INTEGER | Segment start |
| end_sec | INTEGER | Segment end |
| event_type | TEXT | Normalized type |
| intensity | TEXT | low/medium/high |
| summary | TEXT | Gemini description |
| confidence | FLOAT | Gemini confidence |
| score | FLOAT | Computed score |
| generate_ad | BOOLEAN | Decision output |
| urgency | TEXT | ignore/soft/aggressive |
| gemini_latency_ms | INTEGER | Latency tracking |
| created_at | TIMESTAMP | Audit |

### `ads` Table

| Column | Type | Purpose |
|--------|------|---------|
| id | INTEGER | Primary key |
| event_id | INTEGER | Foreign key |
| ad_copy | TEXT | Generated ad |
| promo_suggestion | TEXT | Promotion idea |
| social_hashtags | TEXT | JSON array |
| urgency | TEXT | soft/aggressive |
| groq_latency_ms | INTEGER | Latency tracking |
| created_at | TIMESTAMP | Audit |

---

## 🧪 Testing

### Run Scoring Tests

```bash
python backend/core/scoring.py
```

### Run Decision Tests

```bash
python backend/core/decision.py
```

---

## 📁 File Structure

```
SuperBowl-Ad-Pulse/
├── backend/               # Python FastAPI backend
│   ├── api/               # Routes and schemas
│   ├── core/              # Scoring and decision logic
│   ├── services/          # Gemini and Groq integrations
│   ├── db/                # Database models and config
│   └── main.py            # Application entry point
├── frontend/              # React frontend
│   └── app-react/         # Vite + React dashboard
├── scripts/               # Utility scripts
│   └── reset_db.py        # Database reset
├── requirements.txt       # Python dependencies
├── superbowl_pulse.db     # SQLite database (generated)
└── README.md              # This file
```

---

## 🔒 Environment Variables

| Variable | Required | Purpose |
|----------|----------|---------|
| `GOOGLE_API_KEY` | Yes | Gemini API access |
| `GROQ_API_KEY` | Yes | Groq API access |
| `VITE_API_URL` | No | Override backend URL |

---

## 🚧 What's NOT Included

Per project requirements, these are explicitly excluded:

- ❌ Local multimodal models
- ❌ Background daemons
- ❌ Fake "live" indicators
- ❌ JSON file storage
- ❌ Premature scaling features
- ❌ Mistral 7B (unless justified for offline fallback)

---

## 📄 License

MIT License — Build on it, learn from it, ship it.

---

## 🙏 Credits

- **Google Gemini** — Video understanding
- **Groq** — Fast LLM inference
- **FastAPI** — Backend framework
- **React + Vite** — Frontend
- **SQLAlchemy** — ORM

---

*Built with intention. Every decision is explainable.*
