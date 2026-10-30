# AICTE Institution Complaint Dashboard (MVP)

A runnable full-stack starter implementing centralized complaint intake, rule-based bureau routing,
duplicate detection (Permanent ID + text similarity), SLA monitoring, role-based access, dashboards,
and an audit timeline.

## Stack
- Frontend: Next.js 14, React, Tailwind CSS
- Backend: FastAPI, SQLAlchemy, PostgreSQL (SQLite fallback for local demo)
- Similarity: PostgreSQL-compatible MVP using Python `SequenceMatcher` token similarity.
  For production-scale semantic search, replace this with pgvector/embeddings.
- Authentication: JWT bearer tokens with seeded demo users.

## Run locally

### 1. Backend
```bash
cd backend
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate
pip install -r requirements.txt
copy .env.example .env   # Windows; on macOS/Linux: cp .env.example .env
python seed.py
uvicorn app.main:app --reload
```
API: http://localhost:8000  
Swagger: http://localhost:8000/docs

The default `.env.example` uses SQLite so the project starts without installing PostgreSQL.
To use PostgreSQL, set `DATABASE_URL=postgresql+psycopg://postgres:password@localhost:5432/aicte_complaints`
and create that database first.

### 2. Frontend
In another terminal:
```bash
cd frontend
npm install
copy .env.local.example .env.local
npm run dev
```
Open http://localhost:3000

Demo logins (password for all: `Password@123`):
- `admin@aicte.local` (Admin)
- `officer@aicte.local` (Officer)
- `viewer@aicte.local` (Viewer)

## Implemented workflows
1. File complaint with institution Permanent ID, category, description and optional document URL.
2. Route by category to a configured bureau/cell.
3. Flag active complaints with the same Permanent ID.
4. Compare complaint descriptions against active complaints and flag likely textual duplicates.
5. Track Pending / Under Process / Resolved / Escalated statuses.
6. Show dashboard counts, category/cell distribution and approaching/overdue SLA.
7. Append audit entries on creation and status changes; audit endpoint is read-only.
8. Enforce roles: Admin and Officer can create/update; Viewer is read-only.

## Important production hardening
This is a functional prototype, not an official AICTE system. Before real deployment:
- Confirm AICTE's official bureau names, routing policy, Permanent ID validation source and statutory SLA.
- Replace demo users with institutional SSO/identity provider and rotate `SECRET_KEY`.
- Store uploaded files in private object storage; this MVP accepts a document URL only.
- Add malware scanning, file type/size restrictions, encryption, backups, retention policy and access logs.
- Make audit storage append-only at the database permission/trigger level.
- Have an officer confirm duplicate suggestions; do not auto-merge cases.
- Review privacy, accessibility, security and applicable government data policies.
