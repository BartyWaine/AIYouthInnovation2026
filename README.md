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
SEED_DEV=1 python setup_55_teams.py

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

| Role          | Email                  | Password   | Count |
|---------------|------------------------|------------|-------|
| **Admin**     | `admin@sti.edu.mm`     | `admin123` | 1     |
| **Head Judge** | `judge1@sti.edu.mm`   | `judge123` | 1     |
| **Judge**      | `judge2@sti.edu.mm`   | `judge123` | 4     |
|               | `judge3@sti.edu.mm`    | `judge123` |       |
|               | `judge4@sti.edu.mm`   | `judge123` |       |
|               | `judge5@sti.edu.mm`    | `judge123` |       |
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

The codebase uses `DATABASE_URL` as the cross-environment database variable (in `backend/app/database.py`). For backward compatibility only, a legacy `POSTGRES_URL` value is still accepted as a fallback if `DATABASE_URL` is unset. New deployments should set `DATABASE_URL`.

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
- Score input accepts points tailored to each specific criterion's maximum limit (0 to max), rather than a flat 1–10 scale

### 5. Head Judge Flow
- Head Judge logs in → sees "Head Judge" link in navbar → navigates to `/head-judge-dashboard`
- Selects a competition to view a score matrix: all teams × all judges with per-criterion scores
- Status badges show OPEN / SUBMITTED / LOCKED / FINALIZED per evaluation
- Actions available per evaluation:
  - **Lock** — prevents ordinary judges from editing scores
  - **Finalize** — locks the evaluation permanently
  - **Reopen** (requires reason) — unlocks a finalized evaluation for corrections
- **Correct** — Head Judge can edit any judge's score; requires a correction reason; creates an audit log entry with old/new value
- **Audit Trail** — per-evaluation history of all actions (who did what, when, with reason)
- ADMIN has full access to all Head Judge features

### 6. Evaluation

- Judge enters a score per team per criterion in the dashboard
- Each criterion has its own maximum point value; scores must be between 0 and that criterion's maximum
- Score submits automatically on blur (onBlur event)
- Scores appear inline in the dashboard table

#### Evaluation Rubric

| Criterion | Max Points | Description |
|-----------|-----------|-------------|
| **Innovation** | 30 | Originality and creativity of the AI solution |
| **Feasibility** | 25 | Technical practicality and implementation viability |
| **Presentation** | 25 | Clarity, delivery, and quality of the demonstration |
| **Impact** | 20 | Potential real-world benefit and scalability |
| **Total** | **100** | Sum of all criterion scores |

#### Evaluation Lifecycle (Head Judge / Admin controls)

| Status | Description |
|--------|-------------|
| OPEN | Scores can be added/edited by the assigned judge |
| SUBMITTED | Judge has submitted; editing still allowed by Head Judge |
| LOCKED | No more score edits by ordinary judges; Head Judge can still correct |
| FINALIZED | Evaluation is locked; only Head Judge or Admin can reopen with reason |

Valid transitions: OPEN → SUBMITTED, LOCKED; SUBMITTED → OPEN, LOCKED; LOCKED → FINALIZED, OPEN; FINALIZED → OPEN (requires reason).

#### Score Corrections

When a judge locks/finalizes an evaluation, the Head Judge can still correct any mark via `/judges/evaluations/{id}/scores/correct` (PATCH). Corrections require a mandatory reason and are recorded with old/new values, corrector ID, and timestamp.

#### Audit Trail

Every evaluation action (create, score, lock, finalize, correct, reopen) is recorded in `audit_logs` with: actor role, old/new value, timestamp, and reason.

### 7. File Handling

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

### Integration tests

```bash
cd backend
python test_full_flow.py        # Team upload + judge download end-to-end test
python test_judge_auth_scenarios.py  # 18-scenario HEAD_JUDGE/authorization test suite
```

Both scripts exercise the live API against running servers. Run with backend at `http://127.0.0.1:8022`.

### Seeding

```bash
cd backend
SEED_DEV=1 python setup_55_teams.py
```

Wipes and re-seeds the database with 55 teams, 5 judges (judge1=HEAD_JUDGE), 1 admin, and 3 competitions. Requires `SEED_DEV=1` environment variable as a safety guard.

### TODO

Add a `tests/` suite (pytest) covering authentication, admin workflows, uploads, judge assignment, scoring, download authorization, unauthorized access, and migrations. Document the exact command (`pytest tests/`) once added.

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
ENVIRONMENT=production
RATE_LIMIT_STORAGE=redis://redis:6379
OPENAI_API_KEY=  # optional
```

**Rate limiting**: The application uses `slowapi` for rate limiting.

- In development or single-process deployments, `RATE_LIMIT_STORAGE` can remain unset (defaults to `memory://`).
- **Before scaling beyond one worker or deploying to Kubernetes**, you must provision Redis and set `RATE_LIMIT_STORAGE=redis://redis:6379` (or your Redis URL). Without Redis, each worker will enforce limits independently, which can allow rate-limit bypass and inconsistent throttling.

**Startup validation**: At startup, the application checks whether `RATE_LIMIT_STORAGE=memory://` is used together with multiple workers. In production, this configuration is rejected with a `RuntimeError` to prevent silent misconfiguration. In development, a warning is logged but the application continues.

**Per-endpoint tuning**: You can tune limits per endpoint with these optional environment variables:

```env
RATE_LIMIT_LOGIN=5/minute
RATE_LIMIT_CHANGE_PASSWORD=5/minute
RATE_LIMIT_RESET_PASSWORD=5/minute
RATE_LIMIT_UPLOAD=10/minute
RATE_LIMIT_CORRECT_SCORE=5/minute
RATE_LIMIT_EVAL_STATUS=5/minute
RATE_LIMIT_CREATE_DELIVERABLE=5/minute
```

Omit any variable to use the default limit (`RATE_LIMIT_DEFAULT`, which defaults to `5/minute`). Values can be `<number>`, `<number>/minute`, or `<number>/hour`.

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

Follow this order exactly. Do not scale workers before shared Redis is confirmed.

#### a. Provision Redis or start the internal Redis service

For Docker Compose deployments, Redis is already defined in `docker-compose.yml`. Start it with:

```bash
docker compose up -d redis
```

For other environments, provision a Redis instance reachable from the backend. Ensure it is not exposed publicly. Example using Docker:

```bash
docker run -d \
  --name redis \
  --restart always \
  -p 127.0.0.1:6379:6379 \
  redis:7-alpine \
  redis-server --save "" --appendonly no
```

- `127.0.0.1:6379` binds to localhost only; do not expose Redis to the public internet.
- `--save "" --appendonly no` disables persistence for rate-limit data.

#### b. Set `RATE_LIMIT_STORAGE` to the shared Redis URL

Set `RATE_LIMIT_STORAGE` in your `.env` to the Redis URL the backend can reach. Use placeholders only; never put real passwords or tokens in shared configuration files.

```env
# docker-compose (service name is redis):
RATE_LIMIT_STORAGE=redis://redis:6379/0

# Kubernetes (use a Service name or managed Redis hostname):
# RATE_LIMIT_STORAGE=redis://redis.default.svc.cluster.local:6379/0

# Native / systemd (local or managed):
# RATE_LIMIT_STORAGE=redis://127.0.0.1:6379/0
```

If your Redis requires authentication, use a secret-safe placeholder and inject the real value through your deployment system:

```env
# Placeholder only — replace with your secrets manager reference:
RATE_LIMIT_STORAGE=redis://:${REDIS_PASSWORD}@redis:6379/0
```

#### c. Set the production environment variables securely

```bash
cd backend
pip install -r requirements.txt
alembic upgrade head
```

Ensure `ENVIRONMENT=production` and `RATE_LIMIT_STORAGE` are set in the backend environment. Keep `WEB_CONCURRENCY=1` until step `e` succeeds.

#### d. Start the backend with one worker

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Do not pass `--workers` greater than 1 yet.

#### e. Verify that startup succeeds and rate-limit storage is Redis

- If the backend logs a `RuntimeError` about `memory://` with multiple workers, fix `RATE_LIMIT_STORAGE` before continuing.
- If the backend starts cleanly, look for the startup log line:
  - `Rate-limit storage configured: shared Redis` — confirms shared storage is active.
- If the log shows `in-memory (single-worker only)`, Redis is not configured correctly.

Only proceed to step `f` after the startup log confirms shared Redis.

#### f. Increase the worker count only after shared Redis is confirmed

```bash
# Example: 4 workers with shared Redis
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

Or update your deployment process to use the approved worker count.

#### g. Restart or redeploy the backend using the approved deployment process

Use your standard deployment pipeline to roll out the new worker count. Do not change worker counts ad-hoc.

### 5a. Redis for Rate Limiting (Production)

The backend uses `slowapi` for rate limiting. Rate-limit counters are stored in Redis so they are shared across all workers. **Before scaling beyond one worker, you must provision Redis and set `RATE_LIMIT_STORAGE`.**

If `RATE_LIMIT_STORAGE` is left as `memory://` and the application is started with multiple workers in production, it will fail at startup with a clear configuration error. In development, a warning is logged instead.

#### Docker

```bash
docker run -d \
  --name redis \
  --restart always \
  -p 127.0.0.1:6379:6379 \
  redis:7-alpine \
  redis-server --save "" --appendonly no
```

- `--restart always` ensures Redis starts on boot.
- `127.0.0.1:6379` binds to localhost only; adjust if remote access is required.
- `--save "" --appendonly no` disables persistence for rate-limit data (ephemeral).

#### docker-compose

Add to your `docker-compose.yml`:

```yaml
services:
  redis:
    image: redis:7-alpine
    restart: always
    ports:
      - "127.0.0.1:6379:6379"
    command: redis-server --save "" --appendonly no
    volumes:
      - redis_data:/data
volumes:
  redis_data:
```

Then set in `.env`:

```env
RATE_LIMIT_STORAGE=redis://redis:6379
```

#### Native / systemd (no containers)

Install Redis and enable it:

```bash
# Ubuntu/Debian
sudo apt-get install redis-server
sudo systemctl enable --now redis

# Verify
redis-cli ping
# Expected: PONG
```

Set in `.env`:

```env
RATE_LIMIT_STORAGE=redis://127.0.0.1:6379
```

#### Kubernetes

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: redis
spec:
  replicas: 1
  selector:
    matchLabels:
      app: redis
  template:
    metadata:
      labels:
        app: redis
    spec:
      containers:
        - name: redis
          image: redis:7-alpine
          args: ["redis-server", "--save", "", "--appendonly", "no"]
          ports:
            - containerPort: 6379
          resources:
            requests:
              cpu: 50m
              memory: 64Mi
            limits:
              cpu: 200m
              memory: 128Mi
---
apiVersion: v1
kind: Service
metadata:
  name: redis
spec:
  ports:
    - port: 6379
      targetPort: 6379
  selector:
    app: redis
```

Set in your backend deployment environment:

```env
RATE_LIMIT_STORAGE=redis://redis.default.svc.cluster.local:6379
```

#### Monitoring

Verify Redis is reachable from the backend:

```bash
redis-cli -h <redis-host> ping
```

Monitor with:

```bash
redis-cli info stats
# Look for: total_connections_received, total_commands_processed
```

If using Prometheus, add the [Redis exporter](https://github.com/oliver006/redis_exporter) to monitor memory, connections, and command latency.

#### 429 Monitoring and Alerting

Every rate-limit response emits one structured log event. The event name is `rate_limit_exceeded`.

Example log output:

```json
{
  "event": "rate_limit_exceeded",
  "method": "POST",
  "path": "/auth/login",
  "status": 429,
  "rate_limit": "5 per 1 minute",
  "request_id": "optional-correlation-id",
  "timestamp": "2026-09-07T14:00:00+00:00"
}
```

**Count 429 events**:

```bash
# grep / journalctl / log aggregation filter:
grep '"event":"rate_limit_exceeded"' app.log | wc -l
```

**Group by route**:

```bash
grep '"event":"rate_limit_exceeded"' app.log \
  | grep -o '"path":"[^"]*"' \
  | sort | uniq -c | sort -rn
```

**Group by rate-limit category**:

```bash
grep '"event":"rate_limit_exceeded"' app.log \
  | grep -o '"rate_limit":"[^"]*"' \
  | sort | uniq -c | sort -rn
```

**Recommended alerting**:

- **Warning**: 429 rate exceeds 2× the normal baseline for a 5-minute window. This may indicate a burst of legitimate traffic or a misconfigured client.
- **Critical**: 429 rate exceeds 5× the normal baseline, or a single endpoint accounts for >80% of 429s. This likely indicates abuse or a credential-stuffing attack.

**Distinguishing abusive traffic from legitimate users**:

- Look at the `path` field: a single endpoint with a spike is likely abuse; widespread 429s across many endpoints may indicate a load spike.
- Correlate `request_id` with your application logs to trace the originating user or service.
- If using a reverse proxy, check `X-Forwarded-For` in your access logs to identify the client IP.
- Block or challenge IPs that generate sustained 429s rather than raising global limits.

**Do not** disable rate limiting merely because 429s increase. 429s are expected behavior under load and are a signal to investigate, not to remove protection.

### Rate-Limit Tuning

Current default and endpoint-specific limits:

| Endpoint | Environment variable | Default | Purpose |
|----------|---------------------|---------|---------|
| Global default | `RATE_LIMIT_DEFAULT` | `5/minute` | Fallback for any endpoint without an explicit limit |
| Login | `RATE_LIMIT_LOGIN` | `5/minute` | Prevent credential stuffing |
| Change password | `RATE_LIMIT_CHANGE_PASSWORD` | `5/minute` | Prevent password-change abuse |
| Reset password | `RATE_LIMIT_RESET_PASSWORD` | `5/minute` | Prevent password-reset abuse |
| File upload | `RATE_LIMIT_UPLOAD` | `10/minute` | Allow batch uploads while limiting abuse |
| Score correction | `RATE_LIMIT_CORRECT_SCORE` | `5/minute` | Limit head-judge correction rate |
| Evaluation status | `RATE_LIMIT_EVAL_STATUS` | `5/minute` | Limit evaluation state changes |
| Deliverable creation | `RATE_LIMIT_CREATE_DELIVERABLE` | `5/minute` | Limit admin deliverable creation |

**When to tune**:

- Change only the relevant `RATE_LIMIT_*` variable for the affected endpoint.
- Restart or reload the backend service after changing any `RATE_LIMIT_*` value.
- Monitor 429 rates after the change to confirm the new limit is appropriate.
- Confirm that abusive traffic is still limited after raising a limit.
- Record the reason for every production tuning change in your change-management system.

**Do not** change limits preemptively. Adjust only after reviewing actual traffic patterns and 429 logs.

### Rate-Limit Monitoring and Tuning Runbook

#### 429 JSON Schema

Every rate-limit response emits exactly one structured JSON log event.

```json
{
  "event": "rate_limit_exceeded",
  "method": "POST",
  "path": "/auth/login",
  "status": 429,
  "rate_limit": "5 per 1 minute",
  "request_id": "req-abc-123",
  "timestamp": "2026-09-07T16:00:00+00:00"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `event` | string | yes | Always `rate_limit_exceeded` |
| `method` | string | yes | HTTP method, e.g. `POST` |
| `path` | string | yes | Normalized route template, e.g. `/auth/login` |
| `status` | integer | yes | Always `429` |
| `rate_limit` | string | yes | Human-readable limit, e.g. `5 per 1 minute` |
| `request_id` | string | yes | Correlation ID from `X-Request-ID` or `X-Correlation-ID`; `"-"` if absent |
| `timestamp` | string | yes | ISO-8601 UTC timestamp |

**What is never logged**:
- Authorization headers
- JWTs or API keys
- Passwords
- Redis passwords or complete credential-bearing URLs
- Unnecessary email addresses or personal data
- Sensitive query-string values

#### Log Analysis CLI Commands

This project does not include a separate metrics system. Use the existing structured logs to monitor 429s.

**Count total 429 events**:

```bash
grep '"event":"rate_limit_exceeded"' app.log | wc -l
```

Or with `jq` if logs are JSON-per-line:

```bash
jq -r 'select(.event=="rate_limit_exceeded") | .event' app.log | wc -l
```

**Group by normalized route**:

```bash
grep '"event":"rate_limit_exceeded"' app.log \
  | grep -o '"path":"[^"]*"' \
  | sort | uniq -c | sort -rn
```

Or with `jq`:

```bash
jq -r 'select(.event=="rate_limit_exceeded") | .path' app.log | sort | uniq -c | sort -rn
```

**Group by safe rate-limit category** (`rate_limit` field)**:

```bash
grep '"event":"rate_limit_exceeded"' app.log \
  | grep -o '"rate_limit":"[^"]*"' \
  | sort | uniq -c | sort -rn
```

Or with `jq`:

```bash
jq -r 'select(.event=="rate_limit_exceeded") | .rate_limit' app.log | sort | uniq -c | sort -rn
```

**Compare 429 volume over time** (hourly buckets):

```bash
grep '"event":"rate_limit_exceeded"' app.log \
  | awk -F'"timestamp":"' '{print $2}' \
  | awk -F'"' '{print $1}' \
  | cut -d'T' -f2 \
  | cut -d':' -f1 \
  | sort | uniq -c
```

Or with `jq`:

```bash
jq -r 'select(.event=="rate_limit_exceeded") | .timestamp' app.log \
  | cut -d'T' -f2 | cut -d':' -f1 | sort | uniq -c
```

**Identify the top throttled route**:

```bash
grep '"event":"rate_limit_exceeded"' app.log \
  | grep -o '"path":"[^"]*"' \
  | sort | uniq -c | sort -rn | head -n 5
```

Or with `jq`:

```bash
jq -r 'select(.event=="rate_limit_exceeded") | .path' app.log \
  | sort | uniq -c | sort -rn | head -n 5
```

If one endpoint accounts for a disproportionate share of 429s, focus investigation there rather than changing global limits.

#### Investigation process before tuning

Do not tune `RATE_LIMIT_*` values without evidence. Follow this process:

1. **Review the time window and baseline**
   - Determine whether the 429 spike is sustained or a short burst.
   - Compare against the normal baseline for the same time of day/week.

2. **Identify the affected endpoint and limiter**
   - Use the `path` field to identify the endpoint.
   - Use the `rate_limit` field to identify which limit was hit.

3. **Check whether requests come from abusive, automated, or legitimate traffic**
   - A single IP or a small set of IPs generating many 429s suggests abuse.
   - Widespread 429s across many IPs may indicate a legitimate load spike or misconfigured client.
   - Correlate `request_id` with application logs to trace users or services.

4. **Check whether failures are concentrated in one user flow or deployment instance**
   - One endpoint spike: likely abuse or a misconfigured client.
   - Many endpoints affected: likely a deployment-wide load issue.

5. **Confirm that shared `RATE_LIMIT_STORAGE` is working when multiple workers are used**
   - Verify startup log shows `Rate-limit storage configured: shared Redis`.
   - If the log shows `in-memory (single-worker only)`, fix storage before tuning limits.

6. **Determine whether the issue is a real product-traffic pattern or an attack**
   - Legitimate traffic: consider a small, temporary increase for the affected endpoint only.
   - Attack: keep or tighten limits; do not raise them.

7. **Record the evidence and proposed change**
   - Document the endpoint, current limit, observed 429 rate, traffic pattern, and proposed new limit.
   - Do not make changes without this record.

#### Safe tuning protocols

If the investigation concludes that a limit increase is justified:

- Change **only** the affected `RATE_LIMIT_*` variable. Do not raise all limits globally.
- Do not remove the limit. Keep some ceiling in place.
- Prefer a small incremental increase, e.g. from `5/minute` to `10/minute`, not `100/minute`.
- Keep strict limits for security-sensitive actions:
  - `RATE_LIMIT_LOGIN`
  - `RATE_LIMIT_CHANGE_PASSWORD`
  - `RATE_LIMIT_RESET_PASSWORD`
- Apply changes through the normal deployment configuration process (environment variables or secrets manager).
- Restart or reload the backend service after changing any `RATE_LIMIT_*` value.
- Monitor 429 rates after the change to confirm the new limit is appropriate.
- Confirm that abusive traffic is still limited after raising a limit.
- Record the reason, old value, new value, date, and approver for every production tuning change.
- Revert the change if abuse increases or protection is weakened unnecessarily.

**Current defaults** (do not change without evidence):

| Endpoint | Environment variable | Default | Purpose |
|----------|---------------------|---------|---------|
| Global default | `RATE_LIMIT_DEFAULT` | `5/minute` | Fallback for any endpoint without an explicit limit |
| Login | `RATE_LIMIT_LOGIN` | `5/minute` | Prevent credential stuffing |
| Change password | `RATE_LIMIT_CHANGE_PASSWORD` | `5/minute` | Prevent password-change abuse |
| Reset password | `RATE_LIMIT_RESET_PASSWORD` | `5/minute` | Prevent password-reset abuse |
| File upload | `RATE_LIMIT_UPLOAD` | `10/minute` | Allow batch uploads while limiting abuse |
| Score correction | `RATE_LIMIT_CORRECT_SCORE` | `5/minute` | Limit head-judge correction rate |
| Evaluation status | `RATE_LIMIT_EVAL_STATUS` | `5/minute` | Limit evaluation state changes |
| Deliverable creation | `RATE_LIMIT_CREATE_DELIVERABLE` | `5/minute` | Limit admin deliverable creation |

**If no real traffic logs or metrics are available, leave the current values unchanged.** Monitoring must occur first.

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
