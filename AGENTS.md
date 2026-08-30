# AI Youth Innovation 2026 — Engineering Instructions

## Mission
Maintain and improve the AI Youth Innovation 2026 platform. Prioritize correctness, security, reproducibility, clear documentation, and production readiness.

## Required workflow for every task

Before editing files:

1. Inspect the repository structure and identify the actual files, scripts, frameworks, and configuration sources.
2. Do not assume that a filename, command, environment variable, endpoint, or documentation link exists. Verify it first.
3. Give a concise implementation plan containing:
   - the problem identified;
   - files likely to change;
   - compatibility or security risks;
   - the tests or verification commands to run.
4. Ask for clarification only when an ambiguity could cause data loss, security problems, or an incompatible architectural change.

While implementing:

- Make the smallest coherent change that satisfies the requirement.
- Preserve existing behavior unless the requirement explicitly calls for a behavior change.
- Keep development and production configuration clearly separated.
- Never expose, copy, or commit real secrets, tokens, private keys, or production credentials.
- Treat all credentials currently in documentation as demo-only until verified otherwise.
- Update documentation and example configuration whenever code or environment variables change.
- Prefer explicit error handling and actionable error messages.
- Do not claim that a test passed unless you actually ran it and observed the result.

## README and repository consistency

- Determine whether the repository contains `setup_55_teamams.py` or `setup_55_teams.py`.
- Use only the verified filename consistently throughout the README and scripts.
- Verify the existence and paths of `test_full_flow.py`, `docs/architecture.md`, and all process-flow documentation before referencing them.
- Correct broken commands, links, and file paths.

## Database configuration

- Do not use a variable named `POSTGRES_URL` for a SQLite URL.
- Prefer `DATABASE_URL` as the cross-environment variable.
- Document development configuration explicitly as SQLite using `sqlite:///./test.db` when that is the actual implementation.
- Document production configuration explicitly as PostgreSQL using a PostgreSQL connection URL.
- Add or update `.env.example` with safe placeholders and comments.
- Never put real passwords or tokens in `.env.example`.
- Check whether migrations support both development and production databases before documenting the commands.

## Authentication and security documentation

The README must clearly identify default admin, judge, and team credentials as development/demo credentials only and state that they must be changed or disabled before deployment.

Document, based on the actual implementation:

- JWT secret-key generation and storage;
- token expiration;
- password hashing;
- CORS allowed origins;
- HTTPS requirements;
- upload type, size, and content validation;
- authorization for downloading or accessing submitted files;
- protection of `.env`, database files, logs, and uploaded files.

If the implementation does not provide a security control, say so explicitly and add a TODO or implementation task rather than pretending it exists.

## Testing requirements

Document and, where feasible, implement tests for:

- authentication;
- admin workflows;
- team uploads;
- judge assignment;
- scoring and evaluation (including HEAD_JUDGE correction workflow);
- authorized and unauthorized file downloads;
- invalid or unauthorized requests (including role-based access: JUDGE vs HEAD_JUDGE vs ADMIN);
- database migrations;
- evaluation status transitions (OPEN → SUBMITTED → LOCKED → FINALIZED, and reopen path);
- audit log completeness (every correction stores old_value, new_value, reason, actor_role).

If tests exist in `tests/`, document the exact command to run them. Run the principal test command and report:

- the exact command;
- the number of passed, failed, and skipped tests;
- important warnings or known limitations.

Current test commands:
- `cd backend && python test_full_flow.py` — team upload + judge download end-to-end
- `cd backend && python test_judge_auth_scenarios.py` — 18-scenario HEAD_JUDGE authorization suite (20/20 passing)

## Production deployment requirements

Add a README section covering:

- PostgreSQL configuration;
- production environment variables;
- secure JWT configuration;
- database migrations;
- frontend production build;
- backend deployment;
- reverse proxy and HTTPS;
- CORS configuration;
- persistent storage for uploads;
- database and file backups;
- logging and monitoring;
- disabling or replacing demo accounts.

Clearly explain the difference between `npm run dev` and the production frontend build. Use the actual package scripts from the repository; do not invent commands.

## Response format after implementation

Do not provide hidden chain-of-thought or private internal reasoning. Instead, report a concise engineering summary with these headings:

1. **Result** — what was completed.
2. **Files changed** — each path and its purpose.
3. **Key decisions** — brief reasons for important implementation choices.
4. **Verification** — exact commands run and their observed results.
5. **Remaining risks or TODOs** — items that still require human review.
