# TorqueTrace

TorqueTrace is a full-stack workshop console for capturing vehicle symptoms, OBD-II codes, and sensory clues, then producing ranked mechanical hypotheses with severity, cost bands, and drive-away safety guidance. Results persist in PostgreSQL for case history.

## Stack

- **Frontend:** React + Vite + Tailwind CSS  
- **Backend:** Python FastAPI + SQLAlchemy  
- **Database:** PostgreSQL  
- **AI:** OpenAI API when `OPENAI_API_KEY` is set; otherwise a deterministic rule library (including P0420, P0430, P0300, rough idle, sulfur smell, ticking, and overheating patterns)

## Prerequisites

- Node.js 18+ and npm  
- Python 3.11+  
- Docker Desktop (or another Docker engine) for PostgreSQL, **or** your own PostgreSQL instance

## 1. Start PostgreSQL

From the project root:

```bash
docker compose up -d
```

Default connection (matches `.env.example`):

`postgresql://torquetrace:torquetrace@localhost:5432/torquetrace`

If you previously ran an older compose file with different Postgres credentials, stop containers and remove the old named volume before bringing the stack up again, or point `DATABASE_URL` at your existing database.

## 2. Backend

```bash
cd backend
python -m venv .venv
```

**Windows (PowerShell)**

```powershell
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy ..\\.env.example .env
```

**macOS / Linux**

```bash
source .venv/bin/activate
pip install -r requirements.txt
cp ../.env.example .env
```

Edit `.env` if your database URL differs. Optionally set `OPENAI_API_KEY` for live model responses.

Run the API (creates tables on startup):

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

(Optional) Load demo rows into an empty database:

```bash
python seed_db.py
```

## 3. Frontend

```bash
cd frontend
npm install
copy .env.example .env
npm run dev
```

The Vite dev server proxies `/api` to `http://127.0.0.1:8000`. For a production build served separately from the API, set `VITE_API_URL` to your API origin.

## API

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/diagnose` | Run diagnosis and persist record |
| `GET` | `/api/diagnoses` | List history (newest first) |
| `GET` | `/api/diagnoses/{id}` | Fetch one record |
| `DELETE` | `/api/diagnoses/{id}` | Remove a record |
| `GET` | `/api/health` | Health check |

## GitHub

Initialize and push to a new repository (replace the URL with yours):

```bash
git init
git add .
git commit -m "Initial commit: TorqueTrace full-stack app"
git branch -M main
git remote add origin https://github.com/<your-username>/<your-repo>.git
git push -u origin main
```

Add a `.gitignore` (included) and **do not commit** real `.env` files or API keys.

## Disclaimer

Diagnostic output is informational and does not replace hands-on inspection, certified technicians, or manufacturer service information. Always follow safe workshop practices.
