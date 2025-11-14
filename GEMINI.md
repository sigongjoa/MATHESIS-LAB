# GEMINI.md

This file provides guidance to the Gemini AI assistant when working with the MATHESIS LAB repository.

## Project Overview

MATHESIS LAB is an educational platform for creating and managing curriculum maps with AI-assisted features. The project is a monorepo with a Python backend and a React frontend.

**Stack:**
- **Backend:** FastAPI (Python) with SQLAlchemy ORM. The database is currently being migrated from SQLite to PostgreSQL.
- **Frontend:** React 19 + TypeScript + Vite, located in the `MATHESIS-LAB_FRONT` git submodule.
- **AI:** Google Vertex AI (Gemini) is planned but not yet integrated.

## Architecture

- `backend/`: Contains the FastAPI application.
  - `app/api/v1/endpoints/`: API route handlers.
  - `app/core/`: Configuration.
  - `app/db/`: Database session management.
  - `app/models/`: SQLAlchemy models.
  - `app/schemas/`: Pydantic schemas.
  - `app/services/`: Business logic.
- `MATHESIS-LAB_FRONT/`: The React frontend (git submodule).
- `docs/`: Software design and requirements documentation.

## Virtual Environment

**CRITICAL:** All backend commands must be run within the activated virtual environment.

```bash
# Activate the virtual environment
source .venv/bin/activate
```

## Common Commands

### Backend

**Activate virtual environment first:** `source .venv/bin/activate`

- **Run dev server:**
  ```bash
  uvicorn backend.app.main:app --reload
  ```
- **Run tests:**
  ```bash
  # Set PYTHONPATH to the project root
  export PYTHONPATH=$(pwd)
  pytest backend/tests/
  ```

### Frontend

- **Run dev server:**
  ```bash
  cd MATHESIS-LAB_FRONT
  npm install
  npm run dev
  ```
- **Run tests:**
  ```bash
  cd MATHESIS-LAB_FRONT
  npm test
  ```

## Development Conventions

- **TDD:** The project follows Test-Driven Development. A corresponding test file must be created for every new source file.
- **Service Layer:** Business logic is encapsulated in service classes in `backend/app/services/`. API endpoints should be thin wrappers around these services.
- **Database:**
  - The database schema is defined in `docs/sdd_database_design.md`.
  - All primary keys are UUIDs stored as `VARCHAR(36)`.
- **Error Handling:** If the same error occurs repeatedly, stop and ask the user for guidance.
- **Git:** The frontend is a git submodule. Changes in the frontend must be committed within the `MATHESIS-LAB_FRONT` directory first.
