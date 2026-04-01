import os
import sys
import time
import logging
import asyncio
import threading
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Fix httpx/WinError 10035 on Windows (WSAEWOULDBLOCK with ProactorEventLoop)
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from database.connection import init_db

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger(__name__)

# ── Sentry ────────────────────────────────────────────────────────────────────
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.starlette import StarletteIntegration

_sentry_dsn = os.getenv("SENTRY_DSN_BACKEND")
if _sentry_dsn:
    sentry_sdk.init(
        dsn=_sentry_dsn,
        integrations=[
            StarletteIntegration(transaction_style="endpoint"),
            FastApiIntegration(),
        ],
        traces_sample_rate=0.1,
    )
    log.info("Sentry initialised for backend")

# ── App ───────────────────────────────────────────────────────────────────────
app = FastAPI(title="RealTrack API")

# CORS — allow origins from env (comma-separated) or default to localhost:3000
_cors_origins = os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in _cors_origins],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ───────────────────────────────────────────────────────────────────
from routers import properties, mortgages, tenants, income, expenses, events, summary, maintenance, demo, watchlist, geocode

app.include_router(properties.router,  prefix="/api")
app.include_router(mortgages.router,   prefix="/api")
app.include_router(tenants.router,     prefix="/api")
app.include_router(income.router,      prefix="/api")
app.include_router(expenses.router,    prefix="/api")
app.include_router(events.router,      prefix="/api")
app.include_router(summary.router,     prefix="/api")
app.include_router(maintenance.router, prefix="/api")
app.include_router(demo.router,        prefix="/api")
app.include_router(watchlist.router,   prefix="/api")
app.include_router(geocode.router,     prefix="/api")

# ── DB init ───────────────────────────────────────────────────────────────────
@app.on_event("startup")
def on_startup():
    init_db()
    log.info("Database ready")

# ── Heartbeat / auto-shutdown ─────────────────────────────────────────────────
# Backend shuts itself down if the frontend stops sending heartbeats for 30 s.
# This keeps the process from lingering after the Electron window closes.
_last_heartbeat: float = 0.0
_connected = False

def _watch():
    global _connected
    while True:
        time.sleep(10)
        if _connected and time.time() - _last_heartbeat > 30:
            log.info("No heartbeat for >30 s — shutting down")
            os._exit(0)

threading.Thread(target=_watch, daemon=True).start()

@app.post("/api/heartbeat")
def heartbeat():
    global _last_heartbeat, _connected
    _last_heartbeat = time.time()
    _connected = True
    return {"ok": True}

@app.api_route("/", methods=["GET", "HEAD"])
def root():
    return {"status": "ok"}
