# SuperBowl-Ad-Pulse Repository Documentation

## 1️⃣ Repository Inventory

### Root Directory Files

| Name | Type | Description |
|------|------|-------------|
| `.DS_Store` | File | macOS system file for folder metadata |
| `.env.example` | File | Template file for environment variables with API key placeholders |
| `.gitignore` | File | Git ignore rules for API keys, videos, virtual environments, and cache files |
| `README.md` | File | Project documentation with setup instructions, API overview, and usage |
| `Untitled` | File | Empty/minimal file (58 bytes) |
| `ad_generator.py` | File | Python module for generating advertisement copy using Groq API |
| `ad_results.json` | File | JSON output file containing generated advertisements |
| `api.py` | File | FastAPI backend application with REST endpoints |
| `gui_understanding.py` | File | Streamlit GUI for match event analysis |
| `live_streaming.py` | File | Gemini Live API implementation for real-time audio/video analysis |
| `requirements.txt` | File | Python package dependencies |
| `result.mp4` | File | Demo video file (~10MB) |
| `results.json` | File | JSON output file containing analyzed video segments |
| `run-api.sh` | File | Shell script to start the FastAPI backend |
| `understanding.py` | File | Gemini video analysis module for segment-by-segment processing |

### Directories

| Name | Type | Description |
|------|------|-------------|
| `.git` | Directory | Git version control data |
| `.github` | Directory | GitHub Actions workflow configurations |
| `.venv` | Directory | Python virtual environment |
| `app-react` | Directory | React frontend application |

### `.github/workflows/` Contents

| Name | Type | Description |
|------|------|-------------|
| `deploy-gh-pages-branch.yml` | File | GitHub Actions workflow to deploy to gh-pages branch |
| `deploy-pages.yml` | File | GitHub Actions workflow to deploy to GitHub Pages |

### `app-react/` Contents

| Name | Type | Description |
|------|------|-------------|
| `.gitignore` | File | Git ignore rules for node_modules and build output |
| `README.md` | File | Vite React project documentation |
| `eslint.config.js` | File | ESLint configuration for React/JSX |
| `index.html` | File | HTML entry point for the React application |
| `package-lock.json` | File | npm dependency lock file |
| `package.json` | File | npm package configuration with dependencies and scripts |
| `vite.config.js` | File | Vite build configuration |
| `public/` | Directory | Static assets directory (contains `vite.svg`) |
| `src/` | Directory | React source code |

### `app-react/src/` Contents

| Name | Type | Description |
|------|------|-------------|
| `App.css` | File | Main application styles (dark theme, responsive grid) |
| `App.jsx` | File | Main React component with video player and ad display |
| `index.css` | File | Global CSS styles and CSS variables |
| `main.jsx` | File | React entry point that renders App component |
| `assets/` | Directory | Static assets (contains `react.svg`) |
| `utils/` | Directory | Utility functions |

### `app-react/src/utils/` Contents

| Name | Type | Description |
|------|------|-------------|
| `parseCaptions.js` | File | Utility for parsing caption/timestamp text into structured data |

---

## 2️⃣ Code Module Breakdown

### `api.py`

**Purpose:** FastAPI backend that provides REST endpoints for video upload, segment analysis, and ad generation.

**Imports:** `json`, `shutil`, `threading`, `pathlib.Path`, `typing.Optional`, `fastapi`, `pydantic.BaseModel`, `starlette.responses.StreamingResponse`, local modules (`understanding`, `ad_generator`)

**Functions & Classes:**

| Name | Type | Description |
|------|------|-------------|
| `upload_video_endpoint()` | Async function | POST `/api/upload-video` - Accepts video file, saves locally, uploads to Gemini |
| `upload_status()` | Function | GET `/api/upload-status` - Returns current upload state and video URI |
| `LiveSegmentRequest` | Class | Pydantic model for segment analysis requests |
| `live_segment()` | Function | POST `/api/live-segment` - Analyzes one 5-second segment with Gemini, generates ad with Groq |
| `_append_to_json()` | Function | Thread-safe helper to append items to JSON array files |
| `reset()` | Function | POST `/api/reset` - Clears results.json and ad_results.json |
| `get_events()` | Function | GET `/api/events` - Returns analyzed events from results.json |
| `get_ad_results()` | Function | GET `/api/ad-results` - Returns generated ads from ad_results.json |
| `analyze()` | Function | POST `/api/analyze` - Streams Gemini analysis for video segment |
| `generate_single_ad()` | Function | POST `/api/generate-ad` - Generates ad for single event |
| `health()` | Function | GET `/api/health` - Health check endpoint |

---

### `understanding.py`

**Purpose:** Gemini video understanding module for detecting significant match events in video segments.

**Key Functions:**

| Name | Inputs | Output |
|------|--------|--------|
| `_gemini_api_key()` | None | API key string |
| `build_prompt()` | start_time, end_time | Prompt string |
| `analyze_video()` | video_uri, start_time, end_time | Analysis text string |
| `analyze_video_stream()` | video_uri, start_time, end_time | Generator yielding text chunks |
| `get_video_duration()` | video_path | Duration in seconds |
| `upload_video()` | video_path | Gemini file URI |
| `analyze_full_video()` | video_path, interval, output_json | None (writes to file) |

**Model Used:** `models/gemini-2.5-flash`

---

### `ad_generator.py`

**Purpose:** Generates advertisement copy from game events using Groq API with Llama 3.3 70B model.

**Key Functions:**

| Name | Purpose |
|------|---------|
| `_build_event_prompt()` | Constructs user prompt for Groq |
| `generate_ad()` | Makes Groq API call for ad generation |
| `generate_ad_stream()` | Streams Groq ad generation |
| `process_all_events()` | Processes all events, saves to JSON |

**Model Used:** `llama-3.3-70b-versatile`

---

### `live_streaming.py`

**Purpose:** Live audio/video streaming analysis using Gemini Live API for real-time event detection and speech-to-text.

**Key Functions:**

| Name | Purpose |
|------|---------|
| `run_live_session()` | Async function for audio-based Live API session |
| `run_live_session_video()` | Async function for video frame-based Live API session |
| `audio_from_video_file()` | Async generator extracting audio from video via ffmpeg |
| `video_frames_from_file()` | Async generator yielding JPEG frames from video file |

**Model Used:** `gemini-2.5-flash-native-audio-preview-12-2025`

---

### `gui_understanding.py`

**Purpose:** Streamlit GUI for match event analysis with video URL input.

**Behavior:** Form with video URL, start/end time inputs; calls `analyze_video()` or `analyze_video_stream()` on submit.

---

## 3️⃣ Frontend (React + Vite)

### Component: `App.jsx`

**Purpose:** Main dashboard component for video upload, playback, event display, and ad feed.

**State Variables:** `objectUrl`, `currentTime`, `businessName`, `businessType`, `videoUri`, `uploading`, `uploadError`, `events`, `ads`, `analyzingSegment`, `copiedIdx`

**Rendered Elements:**
- Top Bar: Brand title, business config inputs, live indicator
- Left Column: Video player, video info bar, events list
- Right Column: Key Moments table, Live Ad Feed with copy buttons

**API Communication:** Uses `fetch()` to call backend at `http://localhost:8000` (configurable via `VITE_API_URL`)

### Utility: `parseCaptions.js`

**Exports:** `parseCaptions()`, `getCaptionAtTime()`, `formatTime()`

---

## 4️⃣ Backend / API Flow

### Endpoints

| Method | Endpoint | Parameters | Response |
|--------|----------|------------|----------|
| POST | `/api/upload-video` | Form: `file` | `{ video_uri, status }` |
| GET | `/api/upload-status` | None | `{ video_uri, uploading, ready }` |
| POST | `/api/live-segment` | JSON: `start_sec`, `end_sec`, `business_name?`, `business_type?` | `{ event, ad }` |
| POST | `/api/reset` | None | `{ status: "cleared" }` |
| GET | `/api/events` | None | JSON array |
| GET | `/api/ad-results` | None | JSON array |
| POST | `/api/analyze` | JSON: `video_url`, `start_time`, `end_time` | Streaming text |
| POST | `/api/generate-ad` | JSON: `event`, `business_name?`, `business_type?` | Ad JSON object |
| GET | `/api/health` | None | `{ status: "ok" }` |

### External APIs

- **Google Gemini API** - Video analysis (model: `gemini-2.5-flash`)
- **Groq API** - Ad generation (model: `llama-3.3-70b-versatile`)

### Files Written/Read

- **Written:** `uploaded_video.mp4`, `results.json`, `ad_results.json`
- **Read:** `results.json`, `ad_results.json`, `.env`

---

## 5️⃣ Data & Output Files

### `results.json`

| Key | Type | Description |
|-----|------|-------------|
| `start_sec` | int | Segment start time in seconds |
| `end_sec` | int | Segment end time in seconds |
| `window` | string | Formatted time range |
| `analysis` | string | Gemini's analysis text |

### `ad_results.json`

| Key | Type | Description |
|-----|------|-------------|
| `is_significant` | boolean | Whether event warranted an ad |
| `event_type` | string | Category (touchdown, tackle, etc.) |
| `ad_copy` | string | Generated advertisement text |
| `promo_suggestion` | string | Specific promotion idea |
| `social_hashtags` | array | List of suggested hashtags |
| `urgency` | string | high, medium, or low |
| `source_event` | object | Original event object |

---

## 6️⃣ System Requirements & Execution Dependencies

### Hardware Requirements

#### Minimum Requirements

| Component | Specification |
|-----------|---------------|
| **CPU** | Dual-core 2.0 GHz+ |
| **RAM** | 8 GB DDR4 |
| **Storage** | 100 GB SSD |
| **GPU** | Not required (AI is cloud-based) |
| **Network** | Stable broadband |

#### Recommended Requirements

| Component | Specification |
|-----------|---------------|
| **CPU** | Quad-core 2.5 GHz+ |
| **RAM** | 16 GB DDR4 |
| **Storage** | 256 GB NVMe SSD |
| **GPU** | Integrated GPU (2GB VRAM) |
| **Network** | 10+ Mbps stable |

### Software Requirements

| Software | Version |
|----------|---------|
| **Python** | 3.9+ |
| **Node.js** | 20+ |
| **FFmpeg** | Latest |
| **OS** | Windows/macOS/Linux |

### Python Packages (requirements.txt)

| Package | Version |
|---------|---------|
| streamlit | >=1.28.0 |
| google-genai | >=1.0.0 |
| fastapi | >=0.100.0 |
| uvicorn[standard] | >=0.22.0 |
| python-dotenv | >=1.0.0 |
| opencv-python | >=4.8.0 |
| sounddevice | >=0.4.6 |
| numpy | >=1.24.0 |
| groq | >=1.0.0 |

### JavaScript Packages (package.json)

| Package | Version |
|---------|---------|
| react | ^19.2.0 |
| react-dom | ^19.2.0 |
| vite | ^7.2.4 |

### Environment Variables

| Variable | Purpose |
|----------|---------|
| `GOOGLE_API_KEY` | Gemini API authentication |
| `GEMINI_API_KEY` | Alternative Gemini key |
| `GROQ_API_KEY` | Groq API authentication |
| `VITE_API_URL` | Override backend API URL |

---

## 7️⃣ Cross-Component Relationships

### Integration Flow

```
Frontend (React)
    ↓ HTTP POST /api/upload-video
    ↓ HTTP POST /api/live-segment
Backend (FastAPI - api.py)
    ├── understanding.py → Gemini API
    └── ad_generator.py → Groq API
    ↓ Writes
results.json, ad_results.json
```

### Startup Order

1. Backend API (port 8000)
2. Frontend dev server (port 5173)
3. Environment variables configured before backend start

### Component Status

| Component | Status |
|-----------|--------|
| api.py ↔ understanding.py | Integrated |
| api.py ↔ ad_generator.py | Integrated |
| Frontend ↔ Backend | Integrated |
| gui_understanding.py | Independent (Streamlit) |
| live_streaming.py | Independent (CLI tool) |

---

*Generated: 2026-02-09*
