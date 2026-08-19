# Architecture — AI Youth Innovation Competition 2026

## System Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    CLIENT (Browser)                         │
│                                                             │
│  React + Vite SPA          ───►  REST API (JSON + JWT)      │
│  Tailwind CSS                                               │
│                                                             │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                  BACKEND (FastAPI)                          │
│                                                             │
│  ┌──────────────┐  ┌───────────────┐  ┌──────────────────┐ │
│  │  Auth Router │  │  Admin Router │  │  Judges Router   │ │
│  │  /auth       │  │  /admin       │  │  /judge          │ │
│  │              │  │  /admin/users │  │  /judge/my       │ │
│  │  Login       │  │  /admin/teams │  │  /judges/submi...│ │
│  │  Password    │  │  /admin/comps │  │  /judge/score    │ │
│  │  Reset       │  │  /audit_logs  │  │                  │ │
│  └──────────────┘  └───────────────┘  └──────────────────┘ │
│                                                             │
│  ┌──────────────┐  ┌───────────────┐  ┌──────────────────┐ │
│  │ Teams Router │  │Submissions    │  │ Deliverables     │ │
│  │  /teams      │  │  Router       │  │  Router          │ │
│  │  /submissions│  │  /submissions │  │  /deliverables   │ │
│  │              │  │  /files       │  │                  │ │
│  └──────────────┘  │  /download    │  └──────────────────┘ │
│                     └───────────────┘                       │
│                                                             │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │                    Services                             │ │
│  │                                                         │ │
│  │  ├── SQLAlchemy ORM (SQLite / PostgreSQL)               │ │
│  │  ├── JWT (PyJWT) — access tokens (stateless)           │ │
│  │  ├── Bcrypt — password hashing                         │ │
│  │  ├── Alembic — DB migrations                           │ │
│  │  └── File Storage — local filesystem (uploads/)        │ │
│  └─────────────────────────────────────────────────────────┘ │
│                                                             │
└──────────────┬──────────────────────────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────────────────────────┐
│           DATABASE (SQLite / PostgreSQL)                    │
│                                                             │
│  Tables:                                                    │
│  - users (id, email, password_hash, role, created_at)      │
│  - teams (id, name, competition_id, created_at)             │
│  - team_members (id, team_id, user_id, is_leader)            │
│  - competitions (id, name, category, created_at)            │
│  - deliverables (id, competition_id, name, category)        │
│  - submissions (id, deliverable_id, team_id, version, status)│
│  - submission_files (id, submission_id, filename, version,  │
│    submitted_at, file_size, checksum)                        │
│  - judges (id, user_id)                                      │
│  - judge_assignments (id, judge_id, team_id, competition_id) │
│  - evaluations (id, judge_id, team_id, competition_id)      │
│  - evaluation_scores (id, evaluation_id, criterion_id,      │
│    score, comment)                                           │
│  - evaluation_criteria (id, name, weight)                    │
│  - audit_logs (id, user_id, action, entity_type, ...)      │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│           FILE STORAGE                                      │
│                                                             │
│  backend/app/uploads/                                       │
│  ├── comp_1/                                                │
│  │   └── team_N/                                            │
│  │       └── deliverable_X/                                 │
│  │           └── <uuid>.<ext>                               │
│  └── comp_2/                                                │
│      └── team_N/                                            │
│          └── deliverable_Y/                                 │
│              └── <uuid>.<ext>                               │
└─────────────────────────────────────────────────────────────┘
```

## Components

### Backend (`backend/`)

| Component | Path | Description |
|-----------|------|-------------|
| FastAPI Server | `app/main.py` | Entry point, CORS config, route registration |
| Database | `app/database.py` | SQLAlchemy engine, session management |
| Models | `app/models.py` | SQLAlchemy ORM models — User, Team, Submission, etc. |
| Security | `app/security.py` | Password hashing, JWT token creation/verification |
| Auth Router | `app/routers/auth.py` | Login, password change/reset, token refresh |
| Admin Router | `app/routers/admin.py` | User management (admin-only) |
| Judges Router | `app/routers/judges.py` | Score submission, submission listing, assignment management |
| Teams Router | `app/routers/teams.py` | Team CRUD, team member management |
| Submissions Router | `app/routers/submissions.py` | File upload, download, version management |
| Deliverables Router | `app/routers/deliverables.py` | Deliverable CRUD, competition submission listing |
| Competitions Router | `app/routers/competitions.py` | Competition CRUD (admin-only) |
| Alembic Migrations | `alembic/versions/` | Schema migration scripts |

### Frontend (`frontend/`)

| Component | Path | Description |
|-----------|------|-------------|
| Vite Config | `vite.config.js` | Dev server proxy with `Authorization` header forwarding |
| Main App | `src/App.jsx` | React app with role-based routing |
| Routes | `src/App.jsx` | Protected routes for admin/judge/team views |
| Auth Context | `src/context/AuthContext.jsx` | JWT token storage, login/logout, role checks |
| API Client | `src/api/client.js` | Axios instance with JWT interceptor |

| API Module | Path | Functions |
|------------|------|-----------|
| Auth API | `src/api/auth.js` | `login()`, `changePassword()`, `resetPassword()` |
| Admin API | `src/api/admin.js` | User CRUD, password reset |
| Judges API | `src/api/judges.js` | `getJudgeSubmissions()`, `getJudgeAllSubmissions()`, `submitScore()` |
| Teams API | `src/api/teams.js` | Team info, submissions, file upload/download |
| Deliverables API | `src/api/deliverables.js` | List deliverables, download files |
| Competitions API | `src/api/competitions.js` | List competitions |

### Pages (Frontend)

| Page | Path | Role | Description |
|------|------|------|-------------|
| Login | `src/pages/Login.jsx` | Public | Login form |
| Dashboard | `src/pages/Dashboard.jsx` | Admin/Team | Role-based landing page |
| Judge Dashboard | `src/pages/JudgeDashboard.jsx` | Judge | Scoreable submissions table |
| Competition Teams | `src/pages/CompetitionTeams.jsx` | Admin/Judge | View teams in a competition |
| Team Detail | `src/pages/TeamDetail.jsx` | Judge/Admin | Submission file listing & download |
| Team Uploads | `src/pages/TeamUploads.jsx` | Team | Upload/replace files, download own files |
| Admin Users | `src/pages/admin/Users.jsx` | Admin | User list with password reset |
| Admin Teams | `src/pages/admin/Teams.jsx` | Admin | Team management |
| Admin Competitions | `src/pages/admin/Competitions.jsx` | Admin | Competition management |
| Admin Judge Management | `src/pages/admin/JudgeManagement.jsx` | Admin | Judge assignment management |
| Audit Logs | `src/pages/admin/AuditLogs.jsx` | Admin | Audit trail |

## API Endpoints

### Auth (`/api/v1/auth/`)
| Method | Endpoint | Role | Description |
|--------|----------|------|-------------|
| POST | `/auth/login` | Public | Returns JWT access token |
| POST | `/auth/change-password` | Auth | Change own password |
| POST | `/auth/reset-password` | Admin | Reset another user's password |

### Admin (`/api/v1/admin/`)
| Method | Endpoint | Role | Description |
|--------|----------|------|-------------|
| GET | `/admin/users` | Admin | List all users |
| POST | `/admin/users` | Admin | Create user |
| POST | `/admin/users/{id}/reset-password` | Admin | Reset user password |
| DELETE | `/admin/users/{id}` | Admin | Delete user |
| GET | `/admin/teams` | Admin | List all teams |
| POST | `/admin/teams` | Admin | Create team |

### Judges (`/api/v1/judge/` or `/api/v1/`)
| Method | Endpoint | Role | Description |
|--------|----------|------|-------------|
| GET | `/judge/my-submissions` | Judge | List judge's assigned submissions |
| POST | `/judge/score` | Judge | Submit/update evaluation score |
| GET | `/judge/submissions` | Judge | (All submissions view) |
| POST | `/judges/{user_id}` | Admin | Create judge profile |

### Teams (`/api/v1/teams/`)
| Method | Endpoint | Role | Description |
|--------|----------|------|-------------|
| GET | `/teams/mine` | Team | Get own team info |
| GET | `/teams/mine/submissions` | Team | List own submissions |

### Submissions (`/api/v1/deliverables/`)
| Method | Endpoint | Role | Description |
|--------|----------|------|-------------|
| GET | `/deliverables/categories` | Auth | List deliverable categories |
| GET | `/deliverables/submissions/{id}/files` | Auth | List submission files |
| POST | `/deliverables/submissions/{id}/files` | Team | Upload/replace file |
| GET | `/deliverables/submissions/{id}/files/{fid}/download` | Judge/Team | Download file |

## Authentication & Security

- **JWT tokens**: Stateless, stored in `localStorage` (frontend)
- **Password hashing**: Bcrypt via `passlib`
- **Role enforcement**: `require_role("ROLE")` dependency in FastAPI
- **CORS**: Configured in `main.py` for frontend origin
- **Proxy**: Vite dev server proxies `/api` to `127.0.0.1:8022` with `Authorization` forwarding

## File Handling

- **Upload**: Multipart form data → unique filename (UUID hash) → local filesystem
- **Download**: JWT authentication → role check → file stream with `Content-Disposition`
- **Versioning**: Each replacement auto-increments file version number
- **Timestamps**: `submitted_at` set on upload, `uploaded_at` auto-generated

## Environment Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `POSTGRES_URL` | `sqlite:///./test.db` | Database connection string |
| `JWT_SECRET` | *(random)* | Secret key for JWT signing |
| `OPENAI_API_KEY` | *(empty)* | OpenAI API key (future AI features) |
| `NEXT_PUBLIC_API_BASE_URL` | `http://localhost:8000` | Frontend API base URL |
