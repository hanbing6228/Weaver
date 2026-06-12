# Weaver.AI Core Engine

Python 3.10+ backend + parallel-universe storyboard UI for bi-directional temporal DAG compilation and structural stress Monte Carlo simulation.

## Quick start

### Backend

```bash
cd weaver-ai
python -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
pytest
python -m weaver.api
```

API: `http://127.0.0.1:8787/health`

### Storyboard UI (web)


```bash
cd client
npm install
npm run dev
```

Open `http://127.0.0.1:5173` — Vite proxies `/api` to the engine on port 8787.

### Production (single server)

```bash
cd client && npm install && npm run build
cd .. && python -m weaver.api
```

Open `http://127.0.0.1:8787/` for the storyboard UI.

Optional LLM captions (falls back to engine templates if unset or call fails):

- **Google Gemini (recommended):** `GEMINI_API_KEY` or `GOOGLE_API_KEY` from [Google AI Studio](https://aistudio.google.com/apikey)
- **Anthropic:** `WEAVER_ANTHROPIC_API_KEY` or `ANTHROPIC_API_KEY`
- **Provider override:** `WEAVER_LLM_PROVIDER=google` or `anthropic` when both keys are set
- **Model override:** `GEMINI_MODEL=gemini-2.0-flash` (comma-separated fallbacks)

### iOS app (Capacitor)

Native shell lives in the monorepo sibling folder `../weaver-ios/`:

```bash
cd ../weaver-ios
npm install
cp config.example.js config.local.js   # WEAVER_API → Vercel URL
npm run ios                              # Xcode
```

See `weaver-ios/IOS-BUILD.md` for App Store steps.

## Vercel

Repository: https://github.com/hanbing6228/Weaver

```bash
vercel link    # connect to hanbing6228/Weaver
vercel --prod  # production deploy
```

The Vite client is served as static assets; FastAPI runs as a Python serverless function at `api/index.py`.
