# AI Youth Innovation Competition 2026 Platform

A full-stack competition management system where teams submit AI project deliverables, judges score them, and admins oversee the entire workflow.

## Quick Start

### Prerequisites
- Python 3.11+
- Node.js 18+
- [Git](https://git-scm.com/) (optional, for version control)

---

## Backend Setup

```bash
cd backend

# 1. Install dependencies
pip install -r requirements.txt

# 2. Create .env file
echo "POSTGRES_URL=sqlite:///./test.db" > .env

# 3. Run database migrations
alembic upgrade head

# 4. Seed the database with 55 teams, 5 judges, and 1 admin
python setup_55_teamams.py

# 5. Start the server
uvicorn app.main:app --host 127.0.0.1 --port 8022
```

API docs: `http://127.0.0.1:8022/docs`

---

## Frontend Setup

```bash
cd frontend

# 1. Install dependencies
npm install

# 2. Start the dev server
npm run dev
```

Frontend: `http://localhost:3000`

The Vite dev server proxies `/api` to `http://127.0.0.1:8022` automatically.

---

## Default Accounts

| Role       | Email                  | Password   |
|------------|------------------------|------------|
| **Admin**  | `admin@sti.edu.mm`     | `admin123` |
| **Judge**  | `judge1@sti.edu.mm`    | `judge123` |
|            | `judge2@sti.edu.mm`    | `judge123` |
|            | `judge3@sti.edu.mm`    | `judge123` |
|            | `judge4@sti.edu.mm`    | `judge123` |
|            | `judge5@sti.edu.mm`    | `judge123` |
| **Team**   | `team1@sti.edu.mm`     | `team123`  |
|            | `team2@sti.edu.mm`     | `team123`  |
|            | ...                    | `team123`  |
|            | `team55@sti.edu.mm`    | `team123`  |

> Run the test script to verify everything works:
> ```bash
> cd backend && python test_full_flow.py
> ```

---

## Architecture

```
┌──────────────────┐         HTTP/JSON          ┌──────────────────┐
│   Frontend       │         (REST API)         │   Backend        │
│  React + Vite   │ ◄─────────────────────────► │  FastAPI         │
│  Tailwind CSS   │         JWT Auth           │  SQLAlchemy      │
│  (port 3000)    │                            │  (port 8022)     │
└──────────────────┘                            └────────┬─────────┘
                                                          │
                                                 ┌────────▼─────────┐
                                                 │  SQLite DB       │
                                                 │  test.db         │
                                                 └────────┬─────────┘
                                                          │
                                                 ┌────────▼─────────┐
                                                 │  File Storage    │
                                                 │  uploads/        │
                                                 └──────────────────┘
```

### Key Files

| Area | Path |
|------|------|
| Backend entry point | `backend/app/main.py` |
| DB config & session | `backend/app/database.py` |
| ORM models | `backend/app/models.py` |
| Auth & JWT | `backend/app/routers/auth.py` |
| Admin routes | `backend/app/routers/admin.py` |
| Judge routes | `backend/app/routers/judges.py` |
| Team routes | `backend/app/routers/teams.py` |
| Submission routes | `backend/app/routers/submissions.py` |
| Deliverable routes | `backend/app/routers/competitions.py` |
| Frontend app & routing | `frontend/src/App.jsx` |
| API client | `frontend/src/api/client.js` |
| Auth context | `frontend/src/context/AuthContext.jsx` |
| Judge dashboard | `frontend/src/pages/JudgeDashboard.jsx` |
| Team uploads | `frontend/src/pages/TeamUploads.jsx` |
| Admin users | `frontend/src/pages/admin/Users.jsx` |

---

## Application Flow

### 1. Login
- All users enter their email + password on the login page (`http://localhost:3000/login`)
- A JWT access token is returned and stored in `localStorage`
- The token is sent as `Authorization: Bearer <token>` on all API requests

### 2. Admin Flow
- Admin logs in → Dashboard shows competitions, teams, judges overview
- Admin can manage users (create, reset passwords, delete)
- Admin can create/update/delete competitions and deliverables
- Admin can assign judges to teams

### 3. Team Flow
- Team leader logs in → sees "My Uploads" in the navbar
- Navigates to `/uploads` to view their submissions
- Uploads files for each deliverable (auto-versioned on replacement)
- Can download their own previously uploaded files

### 4. Judge Flow
- Judge logs in → navigates to `/judge-dashboard`
- Views a table of assigned teams with columns for:
  - Team name, school, category
  - Submission status (version, submitted date)
  - Download links for submitted files
  - Score input (number box, submits on blur)
- Can filter by competition (all / comp 1 / comp 2 / comp 3)

### 5. File Handling
- **Upload**: Team uploads file → backend saves with UUID filename → returns metadata (version, submitted_at)
- **Replace**: Same file ID, version auto-increments → previous version is overwritten
- **Download**: Judge/Team requests file → backend verifies JWT + role → streams file with `Content-Disposition`

### 6. Evaluation
- Judge enters a score (0-100) per team in the dashboard table
- Score is saved to the `evaluation_scores` table via POST `/judge/score`
- Scores appear inline in the dashboard table

---

## Database Schema

See `docs/architecture.md` for the full entity relationship diagram.

Key tables: `users`, `teams`, `team_members`, `competitions`, `deliverables`, `submissions`, `submission_files`, `judges`, `judge_assignments`, `evaluations`, `evaluation_scores`, `audit_logs`.

---

## Development

### Running the test script
```bash
cd backend
python test_full_flow.py
```
This tests: team login → file upload → judge login → judge sees submission → file download.

### Seeding fresh data
```bash
cd backend
python setup_55_teams.py
```
Wipes and re-seeds the database with 55 teams, 5 judges, 1 admin, and 3 competitions.

### Docker (optional)
```bash
docker-compose up --build
```

---

## Documentation

- [Process Flow](docs/process_flow.md) — Detailed workflow diagrams for all roles
- [Architecture](docs/architecture.md) — System architecture, API endpoints, and component reference

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | React 18, Vite 5, Tailwind CSS 3, React Router 6 |
| Backend | FastAPI 0.11, SQLAlchemy 2.0, PyJWT, Bcrypt |
| Database | SQLite (dev) / PostgreSQL (production) |
| Auth | JWT access tokens, OAuth2 password flow |
| API | REST (JSON) |
| File Storage | Local filesystem (`backend/app/uploads/`) |
| Migrations | Alembic |
