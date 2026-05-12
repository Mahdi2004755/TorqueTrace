# TorqueTrace

**Repository:** [https://github.com/Mahdi2004755/TorqueTrace](https://github.com/Mahdi2004755/TorqueTrace)

TorqueTrace is a full-stack workshop console for capturing vehicle symptoms, OBD-II codes, and sensory clues, then producing ranked mechanical hypotheses with severity, cost bands, and drive-away safety guidance. Results are saved in PostgreSQL so you can review past cases.

## Stack

- **Frontend:** React + Vite + Tailwind CSS  
- **Backend:** Python FastAPI + SQLAlchemy  
- **Database:** PostgreSQL  
- **AI:** OpenAI API when `OPENAI_API_KEY` is set; otherwise a built-in rule library (including P0420, P0430, P0300, rough idle, sulfur smell, ticking, and overheating patterns)

---

## Prerequisites

Install these on your computer before you start:

| Tool | Why you need it |
|------|------------------|
| **Docker Desktop** (Windows/macOS) or Docker Engine (Linux) | Runs PostgreSQL in one command |
| **Node.js 18+** and **npm** | Runs the web UI |
| **Python 3.11+** | Runs the API server |

Optional: an **OpenAI API key** if you want cloud-model answers instead of the offline rule engine.

---

## Get the code

**Step 1.** Clone the repository:

```bash
git clone https://github.com/Mahdi2004755/TorqueTrace.git
cd TorqueTrace
```

---

## Setup (first time only)

Do these steps once per machine.

### A. Start the database

**Step 2.** Open a terminal in the **project root** (the folder that contains `docker-compose.yml`).

**Step 3.** Start PostgreSQL:

```bash
docker compose up -d
```

**Step 4.** Wait a few seconds for Postgres to become ready. The default connection string (used by the app if you copy `.env.example` later) is:

`postgresql://torquetrace:torquetrace@localhost:5432/torquetrace`

If port `5432` is already used by another Postgres instance, either stop that service or change the host port in `docker-compose.yml` and update `DATABASE_URL` in `backend/.env` to match.

### B. Configure and run the backend

**Step 5.** Open a **new** terminal and go to the `backend` folder:

```bash
cd backend
```

**Step 6.** Create a Python virtual environment:

```bash
python -m venv .venv
```

**Step 7.** Activate the virtual environment.

- **Windows (PowerShell):**

  ```powershell
  .\.venv\Scripts\Activate.ps1
  ```

- **macOS / Linux:**

  ```bash
  source .venv/bin/activate
  ```

**Step 8.** Install dependencies:

```bash
pip install -r requirements.txt
```

**Step 9.** Create your local environment file from the template.

- **Windows (PowerShell), from `backend`:**

  ```powershell
  copy ..\.env.example .env
  ```

- **macOS / Linux, from `backend`:**

  ```bash
  cp ../.env.example .env
  ```

**Step 10.** (Optional) Edit `backend/.env` and set `OPENAI_API_KEY=` to your key if you want OpenAI-powered diagnoses. Leave it blank to use the free rule-based engine.

**Step 11.** Start the API server (leave this terminal **open**):

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

You should see Uvicorn listening on port **8000**. The API also creates database tables automatically on startup.

**Step 12.** (Optional) In **another** terminal with the same venv activated, load demo history rows (only works if the diagnoses table is empty):

```bash
cd backend
python seed_db.py
```

### C. Install and run the frontend

**Step 13.** Open a **third** terminal and go to the `frontend` folder:

```bash
cd frontend
```

**Step 14.** Install UI dependencies:

```bash
npm install
```

**Step 15.** Copy the frontend environment template.

- **Windows (PowerShell):**

  ```powershell
  copy .env.example .env
  ```

- **macOS / Linux:**

  ```bash
  cp .env.example .env
  ```

For normal local development you can leave `VITE_API_URL` empty; Vite proxies `/api` to the backend on port 8000.

**Step 16.** Start the web app (leave this terminal **open**):

```bash
npm run dev
```

Note the URL in the terminal (usually **http://localhost:5173**).

---

## How to operate TorqueTrace (using the app)

Follow these steps whenever you want to run a diagnosis session.

### 1. Make sure all services are running

1. **Database:** Docker is up (`docker compose up -d` from the project root).  
2. **Backend:** Uvicorn is running (`uvicorn main:app --reload --host 0.0.0.0 --port 8000` from `backend`).  
3. **Frontend:** Vite is running (`npm run dev` from `frontend`).

Quick check: open [http://127.0.0.1:8000/api/health](http://127.0.0.1:8000/api/health) in a browser. You should see JSON with `"status": "ok"`.

### 2. Open the dashboard

1. In your browser, go to **http://localhost:5173** (or the URL printed by `npm run dev`).  
2. You will see the **TorqueTrace** header, a **New intake** form on the left (or top on small screens), and a **case panel** on the right.

### 3. Enter vehicle and symptom information

1. Fill in **Year**, **Make**, and **Model** (required).  
2. Optionally add **Engine**, **Mileage**, **Symptoms**, **OBD-II codes**, **Noise description**, and **Smell description**.  
3. OBD codes can be typed like `P0420` or `P0420, P0300` (letters are not case sensitive in practice).

**Shortcut:** Use the pill buttons above the form (for example **P0420 + sulfur + rough idle**) to auto-fill realistic sample data. You can edit the fields afterward.

### 4. Run a diagnosis

1. Click **Run AI diagnosis**.  
2. Wait until the button returns to normal (a few seconds; longer if OpenAI is enabled).  
3. If you see an error message, confirm the backend is running and Postgres is up, then try again.

### 5. Read the results

The **right-hand panel** (or section below the form on small screens) shows the active case:

1. **Severity** and **Safe to drive** badges — treat **Safe to drive: No** seriously; it is a conservative flag for risky patterns (for example overheating or certain misfire codes in rule mode).  
2. **Estimated repair cost** — a rough band, not a quote.  
3. **Summary** — short overview in plain language.  
4. **Top likely causes** — up to three items, each with:  
   - **Probability** bar  
   - **Explanation**  
   - **Next steps** — what to verify on the vehicle or with a scan tool  

Every successful run is **saved to the database** automatically.

### 6. Use case history

1. Scroll to **Case history** at the bottom.  
2. Each **card** shows vehicle, codes snippet, symptoms preview, severity, and top cause.  
3. Click **Open in panel** (or the card body) to load that record into the main result panel on the right.  
4. Click **Delete** to remove a saved case from the database (this cannot be undone).

### 7. When you are finished

1. Stop the frontend terminal with **Ctrl+C**.  
2. Stop the backend terminal with **Ctrl+C**.  
3. Optionally stop Postgres: from the project root, `docker compose down` (add `-v` only if you intend to wipe the database volume).

---

## API reference

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/diagnose` | Run diagnosis and save a record |
| `GET` | `/api/diagnoses` | List all diagnoses (newest first) |
| `GET` | `/api/diagnoses/{id}` | Get one diagnosis by id |
| `DELETE` | `/api/diagnoses/{id}` | Delete a diagnosis |
| `GET` | `/api/health` | Health check |

Interactive docs (while the backend is running): [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

---

## Production build (frontend)

From `frontend`:

```bash
npm run build
```

Output is in `frontend/dist/`. If the API is on another host, set `VITE_API_URL` in `.env` to that API’s origin (no trailing slash), then rebuild.

---

## Troubleshooting

| Problem | What to try |
|---------|-------------|
| Blank history / “Failed to load” | Start the backend; check [http://127.0.0.1:8000/api/health](http://127.0.0.1:8000/api/health). |
| Backend crashes on start | Confirm Docker Postgres is running and `DATABASE_URL` in `backend/.env` is correct. |
| `pip` or `python` not found | Use `py -3.12` (Windows) or install Python from [python.org](https://www.python.org/) and ensure it is on your PATH. |
| Port 8000 in use | Run Uvicorn on another port, e.g. `--port 8001`, and update the Vite proxy in `frontend/vite.config.js` to match. |

---

## Disclaimer

Diagnostic output is informational and does not replace hands-on inspection, certified technicians, or manufacturer service information. Always follow safe workshop practices.

**Do not commit** real `.env` files or API keys to Git.
