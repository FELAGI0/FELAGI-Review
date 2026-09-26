# ReviewHub — Code Review as a Service

Phase 1 foundation of a team code-review platform with an AI reviewer, GitHub integration,
inline discussions and gamification.

## Status

**Phase 1: Foundation — in progress**

- [x] Monorepo structure (`backend/`, `frontend/`, `docker-compose.yml`)
- [x] FastAPI skeleton with health endpoint and JWT auth utilities
- [x] SQLAlchemy models for the full planned database schema
- [x] React + Vite skeleton with routing, TanStack Query and health check
- [x] `/login` and `/dashboard` placeholder pages
- [x] Docker Compose with PostgreSQL 16 + pgvector, Redis, backend and frontend
- [ ] Alembic migrations
- [ ] Full GitHub OAuth flow
- [ ] Persistent user storage and auth against the database

## Local development

### Backend

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\python -m pip install -e . pytest pytest-asyncio pytest-cov ruff
.\.venv\Scripts\python -m pytest
.\.venv\Scripts\python -m ruff check app
.\.venv\Scripts\python -m uvicorn app.main:app --reload
```

### Frontend

```powershell
cd frontend
npm install
npm run dev
```

### Full stack

```powershell
docker compose up --build
```

Copy `.env.example` to `.env` before starting GitHub OAuth integration.

## Tech stack

- Backend: FastAPI, SQLAlchemy 2.0 (async), PostgreSQL 16 + pgvector, Redis
- Frontend: React 18, TypeScript, Vite, TanStack Query, Zustand
- Infrastructure: Docker Compose, GitHub OAuth/App webhooks
