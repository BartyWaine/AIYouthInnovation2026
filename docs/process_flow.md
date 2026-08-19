# Process Flow — AI Youth Innovation Competition 2026

## Overview

The competition platform follows a role-based workflow: **Admin** sets up the competition, **Teams** submit deliverables, **Judges** evaluate submissions, and **Admins** manage users and view results.

## 1. Admin Workflow

```
┌─────────────────────────────────────────────────────┐
│                    ADMIN FLOW                       │
├─────────────────────────────────────────────────────┤
│                                                     │
│  1. Login (admin@sti.edu.mm / admin123)             │
│     │                                              │
│     └─► Dashboard → View all competitions, teams,  │
│         judges, submissions                          │
│                                                     │
│  2. Manage Competitions                             │
│     │                                              │
│     ├─ Create / Update / Delete competitions        │
│     └─ Each competition has deliverables defined    │
│                                                     │
│  3. Manage Users                                    │
│     │                                              │
│     ├─ Create / Reset / Delete judge accounts       │
│     └─ Reset team member passwords                  │
│                                                     │
│  4. Assign Judges                                   │
│     │                                              │
│     └─ Assign judges to specific teams/competitions │
│                                                     │
│  5. View Audit Logs                                 │
│     │                                              │
│     └─ Track all user actions                       │
│                                                     │
└─────────────────────────────────────────────────────┘
```

## 2. Team Workflow

```
┌─────────────────────────────────────────────────────┐
│                    TEAM FLOW                        │
├─────────────────────────────────────────────────────┤
│                                                     │
│  1. Login (teamN@sti.edu.mm / team123)              │
│     │                                              │
│     └─► Dashboard → View team details & submissions│
│                                                     │
│  2. View Submissions                                │
│     │                                              │
│     └─ List of deliverables with status:            │
│       OPEN → UPLOADED → AI_CHECK → READY → SUBMITTED│
│       LOCKED (judging complete)                    │
│                                                     │
│  3. Upload / Replace Files                          │
│     │                                              │
│     ├─ Select submission                              │
│     ├─ Upload file (PDF, DOCX, PPTX, ZIP, etc.)     │
│     ├─ System auto-increments version               │
│     └─ Sets submitted_at timestamp                  │
│                                                     │
│  4. Download Own Files                              │
│     │                                              │
│     └─ Download previously uploaded files           │
│                                                     │
└─────────────────────────────────────────────────────┘
```

## 3. Judge Workflow

```
┌─────────────────────────────────────────────────────┐
│                    JUDGE FLOW                       │
├─────────────────────────────────────────────────────┤
│                                                     │
│  1. Login (judgeN@sti.edu.mm / judge123)            │
│     │                                              │
│     └─► Judge Dashboard → View assigned submissions │
│                                                     │
│  2. Filter Submissions                              │
│     │                                              │
│     ├─ Filter by competition (comp 1 / 2 / 3)       │
│     └─ Switch between "My Assignments" and "All"    │
│                                                     │
│  3. Review Submissions                              │
│     │                                              │
│     ├─ View team name, category                     │
│     ├─ Download submitted files                     │
│     └─ View existing scores/comments                │
│                                                     │
│  4. Score Submission                                │
│     │                                              │
│     ├─ Enter numeric score (0-100)                  │
│     ├─ Submit score (on blur)                       │
│     └─ Optional comment field                       │
│                                                     │
│  5. View Results                                    │
│     │                                              │
│     └─ Results table with sortable columns          │
│                                                     │
└─────────────────────────────────────────────────────┘
```

## 4. Authentication & Authorization Flow

```
Client
  │
  ├─► POST /api/v1/auth/login
  │     ├─ email + password
  │     └─ Returns JWT access_token
  │
  │    JWT contains: {sub: user_id, role: "ADMIN|JUDGE|TEAM_MEMBER"}
  │
  ├─► Subsequent requests include:
  │     Authorization: Bearer <access_token>
  │
  └─► Server validates token and role on each endpoint:
        - require_role("ADMIN") → admin routes
        - require_role("JUDGE") → judge routes
        - require_role("TEAM_MEMBER") → team routes
```

## 5. File Upload & Download Flow

```
Team uploads file:
  ┌────────┐    multipart/form-data         ┌──────────┐
  │Browser │ ──────────────────────────────► │  Backend │
  │        │   (version, file)              │  FastAPI │
  └────────┘                                └──────────┘
        │                                      │
        │                             1. Generate unique filename
        │                             2. Save to uploads/ dir
        │                             3. Create SubmissionFile record
        │                             4. Set submitted_at = now()
        │                                      │
  ←─────┼──────────────────────────────────────│
        │     200 OK + file metadata          │
        │                                      │

Judge downloads file:
  ┌────────┐    GET + Authorization           ┌──────────┐
  │Browser │ ──────────────────────────────► │  Backend │
  │        │   (submission_id, file_id)      │  FastAPI │
  └────────┘                                └──────────┘
        │                                      │
        │                             1. Verify JWT + JUDGE role
        │                             2. Verify assignment
        │                             3. Stream file from disk
        │                                      │
  ←─────┼──────────────────────────────────────│
        │     200 OK + file (stream)           │
        │     Content-Disposition: attachment  │
        │                                      │
```

## 6. Frontend Routing

```
/                   → Login page
/login              → Login page
/dashboard          → Admin/Team dashboard (role-based)
/judge              → Judge Dashboard
/judge/submissions  → Judge's submission review (filtered view)
/my-uploads         → Team's own uploads & submissions
/admin/users        → Admin user management
/admin/teams        → Admin team management
/admin/competitions → Admin competition management
/admin/judges       → Admin judge management
/admin/audit        → Admin audit logs
```

## 7. Database Entity Relationships

```
User (1) ──► TeamMember (N)
    │              │
    │              └─► Team (N)
    │
    └─► Judge (1) ──► JudgeAssignment (N) ──► Team
                                          │
                                          └─► Competition

Competition ──► Deliverable (N)
                    │
                    └─► Submission (1 per team per deliverable)
                              │
                              └─► SubmissionFile (N)

Evaluation ──► EvaluationScore (N)
(Judge, Team)     (criterion, score)
```

## 8. Scoring Process

```
1. Judge opens JudgeDashboard
2. Selects competition filter (comp 1 / 2 / 3 / all)
3. Views table of assigned teams
4. For each team row:
   a. Enter score (number input, 0-100)
   b. Score submits automatically on blur (onBlur event)
5. Scores visible inline in table
6. View detailed submission page to:
   a. Download team files
   b. Enter detailed evaluation scores per criterion
```
