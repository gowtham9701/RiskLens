# RiskLens — Deployment

Three supported paths:
1. **Vercel (frontend) + Render (backend) + Neon (Postgres)** — recommended cloud.
2. **Docker Compose** — self-contained local/VM demo.
3. **Manual host** — venv + a process manager behind a reverse proxy.

---

## 1. Vercel + Render + Neon (recommended)

### A. Database (Neon — free tier)
Use an existing Neon database or create one at https://neon.tech. Copy its
connection string (`postgresql://user:pass@host/db?sslmode=require`).

### B. Backend on Render (free tier)
This repo ships a blueprint: [`render.yaml`](../render.yaml).

1. Push the repo to GitHub (see README).
2. Render → **New +** → **Blueprint** → pick the `RiskLens` repo. Render reads
   `render.yaml` and creates the `risklens-backend` web service with:
   - Build: `pip install -e ./analytics && pip install -r backend/requirements.txt`
   - Start: `python -m backend.app.seed --if-empty && uvicorn backend.app.main:app --host 0.0.0.0 --port $PORT`
   - Health check: `/health`
3. Set env vars in the Render dashboard:
   - `DATABASE_URL` = your Neon URL
   - `CORS_ORIGINS` = your Vercel URL (add after step C; can be `*` temporarily)
   - `SECRET_KEY` is auto-generated; `LLM_API_KEY` optional.
4. Deploy. The service seeds the DB **only if empty**, so redeploys never wipe
   user data. Note the public URL, e.g. `https://risklens-backend.onrender.com`.

> Free Render services sleep after inactivity; the first request may take
> ~30–50s to wake. Upgrade the plan to keep it always-on.

### C. Frontend on Vercel (free tier)
1. Vercel → **Add New → Project** → import the `RiskLens` repo.
2. **Set Root Directory = `frontend`** (Vercel auto-detects Next.js there).
   `frontend/vercel.json` pins the framework/build.
3. Add env var **`NEXT_PUBLIC_API_URL`** = your Render backend URL
   (e.g. `https://risklens-backend.onrender.com`).
4. Deploy. Copy the `https://<app>.vercel.app` URL into the backend's
   `CORS_ORIGINS` on Render, then redeploy the backend.

Done — open the Vercel URL and log in with **demo@risklens.sim / demo1234**.

---

## 2. Docker Compose
```bash
cp .env.example .env            # optional: SECRET_KEY, external DATABASE_URL
docker compose up --build
# frontend http://localhost:3000   backend http://localhost:8000/docs
```

## 3. Manual host
### Backend
```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -e ./analytics -r backend/requirements.txt
export DATABASE_URL="postgresql://user:pass@host/db?sslmode=require"
export SECRET_KEY="$(openssl rand -hex 32)"
export CORS_ORIGINS="https://your-frontend-domain"
python -m backend.app.seed --if-empty
uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --workers 2
```
Put TLS-terminating nginx/Caddy in front for HTTPS.

### Frontend
```bash
cd frontend && npm ci
echo "NEXT_PUBLIC_API_URL=https://your-backend-domain" > .env.local
npm run build && npm run start -- -p 3000
```

---

## Open-source / free alternatives

| Layer | Recommended | Also good (open-source friendly / free tiers) |
|-------|-------------|-----------------------------------------------|
| Frontend | **Vercel** | **Netlify**, **Cloudflare Pages** |
| Backend (Python) | **Render** | **Railway**, **Fly.io**, **Koyeb**, **Google Cloud Run**, **Hugging Face Spaces (Docker)** |
| Postgres | **Neon** | **Supabase**, **Railway Postgres**, **Render Postgres** |
| Self-host all | **Docker Compose** | **Coolify** / **Dokku** / **CapRover** (open-source PaaS on your own VPS) |

Notes:
- **Fly.io / Cloud Run** run the provided `backend/Dockerfile` directly and
  avoid cold-start sleeping better than free Render.
- **Railway** can host backend + Postgres together from this repo (same start
  command as Render).
- **Coolify / Dokku / CapRover** give a fully open-source, self-hosted
  Heroku-style deploy using the Dockerfiles in this repo.

## Database schema / migrations
The app ensures tables on startup (`create_all`) and seeds if empty. For
controlled production schema changes, initialise Alembic against
`backend/app/models` (see `backend/migrations/README.md`).

## Health & monitoring
`GET /health` for liveness/readiness probes; structured logs via the `risklens`
logger. See `docs/LIMITATIONS.md` for items to harden before commercial launch.
