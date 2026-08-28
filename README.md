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

# 2. Create .env file (copy from .env.example)
cp ../.env.example .env

# 3. Run database migrations
alembic upgrade head

# 4. Seed the database with 55 teams, 5 judges, and 1 admin
python setup_55_teams.py

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

The Vite dev server proxies `/api` to `http://127.0.0.1:8022` automatically (see `frontend/vite.config.js`). This proxy forwards the `Authorization` header so JWT tokens work in development.

In production, build the frontend with `npm run build` which outputs static files to `dist/`. Use nginx or another reverse proxy to serve these alongside the backend.

---

## ⚠️ Default Accounts (Development / Demo Only)

> **These credentials are for development and testing only.**
> If this system will be used for a live competition, **change all passwords** or **disable these accounts** before deployment.

| Role       | Email                  | Password   | Count |
|------------|------------------------|------------|-------|
| **Admin**  | `admin@sti.edu.mm`     | `admin123` | 1     |
| **Judge**  | `judge1@sti.edu.mm`    | `judge123` | 5     |
|            | `judge2@sti.edu.mm`    | `judge123` |       |
|            | `judge3@sti.edu.mm`    | `judge123` |       |
|            | `judge4@sti.edu.mm`    | `judge123` |       |
|            | `judge5@sti.edu.mm`    | `judge123` |       |
| **Team**   | `team1@sti.edu.mm`     | `team123`  | 55    |
|            | `team2@sti.edu.mm`     | `team123`  |       |
|            | ...                    | `team123`  |       |
|            | `team55@sti.edu.mm`    | `team123`  |       |

Admin can reset any user's password via the API or admin UI. Judges can be created and managed by the admin.

---

## Security

### Authentication & JWT

- **Method**: JWT access tokens (stateless), sent as `Authorization: Bearer <token>` header
- **Signing algorithm**: HS256
- **Secret key**: Read from `JWT_SECRET` environment variable. If unset, defaults to `dev-secret-change-me` (insecure — must be set in production)
- **Token expiration**: 24 hours (`86400` seconds). There is no refresh token in the current implementation; users must re-login after expiry
- **Token storage**: Stored in browser `localStorage` (use HTTPS in production to prevent MITM)
- **Generate a secure secret**:
  ```bash
  python -c "import secrets; print(secrets.token_hex(32))"
  ```

### Password Hashing

- **Algorithm**: PBKDF2-SHA256 with 100,000 iterations and a 16-byte random salt per password
- **Implementation**: `backend/app/security.py`
- Passwords are never stored in plaintext

### CORS

Configured in `backend/app/main.py`:

```python
allow_origins=["http://localhost:3000", "http://localhost:3001", "http://127.0.0.1:3000", "http://127.0.0.1:3001"]
```

- `allow_credentials=True`
- `allow_methods=["*"]`, `allow_headers=["*"]`
- In production, restrict `allow_origins` to the actual frontend domain and use HTTPS

### HTTPS

- The development servers run over HTTP
- **Production**: HTTPS must be enforced via the reverse proxy (nginx) or a cloud load balancer. JWT tokens must never transit over unencrypted HTTP in production

### File Upload Validation

- **Allowed extensions**: `.docx`, `.pdf`, `.pptx`, `.zip`, `.mp4`, `.png`, `.jpg`, `.jpeg`
- **Max file size**: 50 MB per file
- **File storage**: Uploaded files are stored on the local filesystem at `backend/app/uploads/`
- Files are named with UUID hashes (not user-supplied filenames) for security
- SHA-256 checksums are computed for each uploaded file

### File Download Authorization

- Both judges and team members must present a valid JWT
- **Judges**: Must be assigned to the team they are viewing (via `judge_assignments` table)
- **Teams**: Can only download their own team's submissions (verified via `TeamMember` relationship)
- Unauthorized access returns 403 Forbidden

### Secret & Data Protection

- `.env` file is **gitignored** and never committed (see `.gitignore`)
- `.env.example` contains only placeholder values — no real secrets
- Database file (`test.db`) is gitignored
- Upload directory is **not** gitignored — add `backend/app/uploads/` to `.gitignore` if you want to exclude uploaded files from version control

---

## Database Configuration

### Development (SQLite)

The default development database uses SQLite with the `DATABASE_URL` environment variable:

```env
DATABASE_URL=sqlite:///./test.db
```

The database file `test.db` is created in the `backend/` directory.

### Production (PostgreSQL)

In production, use a PostgreSQL URL:

```env
DATABASE_URL=postgresql://user:password@localhost:5432/competition_db
```

### Environment Variable

The codebase uses `DATABASE_URL` as the cross-environment database variable (in `backend/app/database.py`). For backward compatibility, `POSTGRES_URL` is also read as a fallback.

### Migrations

```bash
# Apply migrations
alembic upgrade head

# Create a new migration
alembic revision --autogenerate -m "description"

# Reset database (dev only)
rm backend/test.db && alembic upgrade head && python setup_55_teams.py
```

Migrations support both SQLite (development) and PostgreSQL (production) dialects.

---

## Application Flow

### 1. Login
- All users enter their email + password at `http://localhost:3000/login`
- A JWT access token is returned and stored in `localStorage`
- The token is sent as `Authorization: Bearer <token>` on all API requests

### 2. Admin Flow
- Admin logs in → Dashboard shows competitions, teams, judges overview
- Admin can manage users (create, reset passwords, delete)
- Admin can create/update/delete competitions and deliverables
- Admin can assign judges to teams

### 3. Team Flow
- Team member logs in → sees "My Uploads" in the navbar
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
- Judge enters a score (1-10) per team in the dashboard table
- Score submits automatically on blur (onBlur event)
- Scores appear inline in the dashboard table

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
                                             ┌──────────▼──────────┐
                                             │  SQLite DB (dev)   │
                                             │  PostgreSQL (prod) │
                                             └──────────┬─────────┘
                                                        │
                                             ┌──────────▼──────────┐
                                             │  File Storage        │
                                             │  uploads/            │
                                             └─────────────────────┘
```

### Key Files

| Area | Path |
|------|------|
| Backend entry point | `backend/app/main.py` |
| DB config & session | `backend/app/database.py` |
| ORM models | `backend/app/models.py` |
| Auth & JWT | `backend/app/security.py` |
| Auth router | `backend/app/routers/auth.py` |
| Admin routes | `backend/app/routers/admin.py` |
| Judge routes | `backend/app/routers/judges.py` |
| Team routes | `backend/app/routers/teams.py` |
| Submission routes | `backend/app/routers/submissions.py` |
| Deliverable routes | `backend/app/routers/competitions.py` |
| Frontend app & routing | `frontend/src/App.jsx` |
| API client | `frontend/src/api/client.js` |
| Auth context | `frontend/src/context/AuthContext.jsx` |

---

## Database Schema

See `docs/architecture.md` for the full entity relationship diagram.

Key tables: `users`, `teams`, `team_members`, `competitions`, `deliverables`, `submissions`, `submission_files`, `judges`, `judge_assignments`, `evaluations`, `evaluation_scores`, `audit_logs`.

---

## Testing

### Test Script

```bash
cd backend
python test_full_flow.py
```

Tests: team login → file upload → judge login → judge sees submission → file download.

Run from the `backend/` directory with both backend and frontend servers running.

### Seeding

```bash
cd backend
python setup_55_teams.py
```

Wipes and re-seeds the database with 55 teams, 5 judges, 1 admin, and 3 competitions.

---

## Production Deployment

### 1. PostgreSQL Configuration

```bash
# Create database and user
sudo -u postgres createuser competition -P
sudo -u postgres createdb competition_db -O competition

# Set environment variable
export DATABASE_URL=postgresql://competition:<password>@localhost:5432/competition_db
```

Run migrations:
```bash
alembic upgrade head
```

### 2. Environment Variables

Create a `.env` file in `backend/`:

```env
DATABASE_URL=postgresql://user:password@localhost:5432/competition_db
JWT_SECRET=<generate with: python -c "import secrets; print(secrets.token_hex(32))">
OPENAI_API_KEY=  # optional
```

### 3. Secure JWT Configuration

- Set a strong `JWT_SECRET` (at least 32 random bytes)
- Consider reducing token lifetime from the default 24 hours if security is critical
- Serve tokens only over HTTPS

### 4. Frontend Production Build

```bash
cd frontend
npm run build
```

This creates `dist/` with optimized static assets. Use `npm run preview` to test locally.

### 5. Backend Deployment

```bash
cd backend
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### 6. Reverse Proxy & HTTPS

Use nginx as a reverse proxy:

```nginx
server {
    listen 80;
    server_name competition.sti.edu.mm;
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl http2;
    server_name competition.sti.edu.mm;

    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;

    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location / {
        root /path/to/frontend/dist;
        try_files $uri $uri/ /index.html;
    }
}
```

### 7. CORS Configuration

Update `backend/app/main.py` to restrict CORS to the production domain:

```python
allow_origins=["https://competition.sti.edu.mm"],
```

### 8. Persistent Storage for Uploads

Configure the upload directory for persistence:

```python
# In backend/app/routers/submissions.py
UPLOAD_DIR = "/var/www/uploads"  # Use a persistent, backed-up location
```

Mount a persistent volume or use cloud storage (S3, GCS) for production.

### 9. Backups

```bash
# Database backup (PostgreSQL)
pg_dump competition_db > backup_$(date +%Y%m%d).sql

# File backup (uploads)
tar czf uploads_$(date +%Y%m%d).tar.gz /var/www/uploads

# Automated backup cron
0 2 * * * pg_dump competition_db > /backups/db_$(date +\%Y\%m\%d).sql
```

### 10. Logging & Monitoring

Add to `backend/app/main.py` to enable structured logging:

```python
import logging
logging.basicConfig(level=logging.INFO)
```

Use tools like `journalctl`, Prometheus + Grafana, or a cloud logging service.

### 11. Disabling Demo Accounts

Before going live:
1. Delete or disable the default admin, judge, and team accounts
2. Create real accounts through the registration or admin endpoints
3. Rotate `JWT_SECRET` to a fresh value
4. Rotate all API keys (OpenAI, etc.)

---

## Development

### Difference: `npm run dev` vs `npm run build`

| Command | Purpose | Output | Environment |
|---------|---------|--------|-------------|
| `npm run dev` | Development with hot reload | In-memory bundle on `http://localhost:3000` | Dev (proxy to backend) |
| `npm run build` | Production build | Static files in `frontend/dist/` | Optimized, minified |

- `npm run dev`: Use during development — fast refresh, source maps, dev tooling
- `npm run build`: Use before deploying to production — optimized assets for static serving behind nginx

---

## Documentation

- [Process Flow](docs/process_flow.md) — Detailed workflow diagrams for all roles
- [Architecture](docs/architecture.md) — System architecture, API endpoints, and component reference

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | React 18, Vite 5, Tailwind CSS 3, React Router 6 |
| Backend | FastAPI 0.11, SQLAlchemy 2.0, PyJWT |
| Database | SQLite (dev) / PostgreSQL (production) |
| Password Hashing | PBKDF2-SHA256 (100,000 iterations, 16-byte salt) |
| Auth | JWT access tokens (HS256, 24-hour expiry) |
| API | REST (JSON) |
| File Storage | Local filesystem (`backend/app/uploads/`) |
| Migrations | Alembic |
