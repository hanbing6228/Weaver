# Weaver.AI Core Engine

Python 3.10+ backend + Vite/Three.js desktop client for bi-directional temporal DAG compilation and structural stress Monte Carlo simulation.

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

### WebGL client (development)

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

Open `http://127.0.0.1:8787/` for the bundled Topographic Risk Ribbon UI.

## Vercel

Repository: https://github.com/hanbing6228/Weaver

```bash
vercel link    # connect to hanbing6228/Weaver
vercel --prod  # production deploy
```

The Vite client is served as static assets; FastAPI runs as a Python serverless function at `api/index.py`.
