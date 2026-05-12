import os

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from database import Base, engine
from routes import diagnosis

load_dotenv()

app = FastAPI(title="TorqueTrace", version="1.0.0")

origins = os.getenv(
    "CORS_ORIGINS",
    "http://localhost:5173,http://127.0.0.1:5173",
).split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in origins if o.strip()],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)


@app.get("/api/health")
def health():
    return {"status": "ok", "service": "TorqueTrace"}


@app.get("/api/config")
def public_config():
    """Non-secret flags for the UI (e.g., prompt to configure OpenAI)."""
    key = os.getenv("OPENAI_API_KEY", "").strip()
    return {
        "openai_configured": bool(key),
        "web_search_enabled_default": os.getenv("TORQUE_WEB_SEARCH", "true").strip().lower()
        not in ("0", "false", "no", "off"),
    }


app.include_router(diagnosis.router, prefix="/api")
