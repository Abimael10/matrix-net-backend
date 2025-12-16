# Matrix-Net App Backend

FastAPI service for the Matrix-net app with SQLite/PostgreSQL via SQLAlchemy and an event-driven service layer (commands, handlers, message bus).

## Quick start
- Create a virtualenv and install deps: `python -m venv venv && source venv/bin/activate && pip install -r requirements.txt -r dev-requirements.txt`
- Configure `.env` (ENV, DATABASE_URI/DEV_DATABASE_URI/TEST_DATABASE_URI, SECRET_KEY). Defaults in `.env.example`.
- Run locally (dev): `ENV=dev DEV_DATABASE_URI=sqlite:///./local.db DEV_SECRET_KEY=dev-secret uvicorn src.main:app --reload`
- Tests: `pytest`

## Project layout
- `src/main.py` FastAPI app, routers under `src/entrypoints/routers`
- Domain/service layer under `src/domain` and `src/service_layer`
- Persistence adapters in `src/adapters`; DB tables in `src/db.py`
