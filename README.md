# SuperBowl Ad Pulse

Upload a video (e.g. game or ad reel), get **live segment-by-segment analysis** with Google Gemini, and **AI-generated ad ideas** from events (Groq). Results stream to the React UI and are written to `results.json` and `ad_results.json`.

## Demo

<video src="https://github.com/leolorence12345/SuperBowl/blob/main/result.mp4" controls width="100%"></video>

## Stack

- **Backend:** FastAPI (Python) — video upload to Gemini, segment analysis, ad generation
- **Frontend:** React + Vite — video player, live events, ad list with copy-to-clipboard

## Setup

### 1. Backend (Python)

```bash
cd /path/to/NFL
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Environment

Copy the example env and add your API keys:

```bash
cp .env.example .env
```

Edit `.env` and set:

- `GOOGLE_API_KEY` — [Google AI Studio](https://aistudio.google.com/apikey) (for Gemini video analysis)
- `GROQ_API_KEY` — [Groq](https://console.groq.com/) (for ad generation)

### 3. Frontend (React)

```bash
cd app-react
npm install
```

## Run

**Terminal 1 — API (port 8000):**

```bash
cd /path/to/NFL
source .venv/bin/activate
uvicorn api:app --reload --port 8000
```

Or use the script:

```bash
./run-api.sh
```

**Terminal 2 — React app (Vite default port, e.g. 5173):**

```bash
cd app-react
npm run dev
```

Open the URL Vite prints (usually `http://localhost:5173`). The app talks to the API at `http://localhost:8000` by default; override with `VITE_API_URL` if needed.

## API overview

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/upload-video` | Upload video file → Gemini; returns `video_uri` |
| GET | `/api/upload-status` | Current upload state and `video_uri` |
| POST | `/api/live-segment` | Analyze a time segment (e.g. 0:00–0:05) and optionally generate ad |
| POST | `/api/reset` | Clear in-memory state and result files |
| GET | `/api/events` | List analyzed events (from `results.json`) |
| GET | `/api/ad-results` | List generated ads (from `ad_results.json`) |
| POST | `/api/analyze` | One-off full-video or segment analysis |
| POST | `/api/generate-ad` | Generate ad for a given event |
| GET | `/api/health` | Health check |

## Output files

- `results.json` — segment analysis results (events, timestamps, captions)
- `ad_results.json` — generated ad copy per event

Both are updated in real time as the video plays and segments are analyzed.

## License

MIT (or your choice).
