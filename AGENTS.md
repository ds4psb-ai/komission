# Repository Guidelines

## Project Structure & Module Organization
- `backend/` houses the FastAPI service. Core modules live in `backend/app/` with routers in `backend/app/routers`, data access in `backend/app/repositories`, schemas in `backend/app/schemas`, and shared services in `backend/app/services`.
- `backend/tests/` contains pytest suites; seed helpers live in `backend/scripts/`.
- `frontend/` is a Next.js 16 app. UI code is under `frontend/src/` with `app/` routes, `components/`, `hooks/`, and `lib/`. Static assets are in `frontend/public/`.
- `docker-compose.yml` starts local dependencies (Postgres, Neo4j, Redis). Architecture and ops docs live at the repo root (`*.md`).

## Build, Test, and Development Commands
- `docker-compose up -d`: start local infra services.
- Backend dev server:
  - `cd backend`
  - `python3.9 -m venv venv && source venv/bin/activate`
  - `pip install -r requirements.txt`
  - `uvicorn app.main:app --reload --port 8000`
- Frontend dev server:
  - `cd frontend`
  - `bun install`
  - `bun run dev`
- Frontend build/start: `bun run build` then `bun run start`
- Frontend linting: `bun run lint`
- Backend tests: `cd backend && pytest`
- Optional seed scripts: `python backend/scripts/seed_data.py`

## Coding Style & Naming Conventions
- Python: 4-space indentation, type hints where practical, and keep FastAPI endpoints in `backend/app/routers`. Prefer async patterns for DB and external calls.
- TypeScript/React: 2-space indentation, semicolons, double quotes, and PascalCase component names (e.g., `OutlierCard.tsx`). Hooks should be `useSomething`.
- Tailwind CSS is the primary styling mechanism; keep utility classes organized and avoid ad-hoc inline styles unless necessary.

## Testing Guidelines
- Pytest + pytest-asyncio are configured. Tests follow `test_*.py` naming in `backend/tests/`.
- Add or update tests for new API endpoints, repository logic, or service behavior.
- No frontend test runner is configured; document manual UI verification in PR notes.

## Commit & Pull Request Guidelines
- Follow conventional prefixes seen in history: `feat:`, `fix:`, `docs:`, `style:`, `refactor:`.
- PRs should include a short summary, testing performed (commands + results), and screenshots for UI changes.
- Call out any new env vars or infra changes (Postgres/Redis/Neo4j) in the PR description.

## Security & Configuration Notes
- Backend config is driven by environment variables in `backend/app/config.py` and `.env`. Do not commit secrets (API keys, JWT secrets).
- Ensure local services are running via `docker-compose` before exercising API routes.
