"""
CO2Ops backend entrypoint.

Replaces the bare `adk api_server` CLI invocation with a wrapped FastAPI app that
requires an API key on every request. ADK's own docs say it plainly:

    "This server's endpoints are unauthenticated. Run it on a trusted network
    only, and put it behind your own authentication and authorization layer
    before exposing it to untrusted or public networks."

This agent can stop/resize/restart real EC2 instances (see safe_executor_agent),
so that authentication layer is not optional here.

Required env var:
    CO2OPS_API_KEY   - shared secret the frontend must send as the
                        `X-API-Key` header on every request.

Optional env var:
    ALLOWED_ORIGINS  - comma-separated list of allowed frontend origins
                        (e.g. "https://app.example.com"). Defaults to "*"
                        with a loud warning if unset - tighten this for prod.
"""

import logging
import os
import sys

# Ensure AGENTS_DIR and its parent directory are on sys.path so 'co2ops_agent' is always
# discoverable as a package, whether running locally or inside Docker containers.
AGENTS_DIR = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(AGENTS_DIR)
for p in [parent_dir, AGENTS_DIR]:
    if p and p not in sys.path:
        sys.path.insert(0, p)

import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from google.adk.cli.fast_api import get_fast_api_app
from starlette.middleware.base import BaseHTTPMiddleware

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("co2ops.server")

HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "8080"))

API_KEY = os.getenv("CO2OPS_API_KEY")
# Paths that don't require the API key (container health checks and app discovery).
PUBLIC_PATHS = {"/", "/health", "/list-apps", "/docs", "/openapi.json"}

_raw_origins = os.getenv("ALLOWED_ORIGINS")
if _raw_origins:
    ALLOWED_ORIGINS = [o.strip() for o in _raw_origins.split(",") if o.strip()]
else:
    ALLOWED_ORIGINS = ["*"]
    logger.warning(
        "ALLOWED_ORIGINS is not set - defaulting to '*'. "
        "Set it to your real frontend URL(s) before going to production."
    )

if not API_KEY:
    logger.warning(
        "CO2OPS_API_KEY is not set. Running in open-access mode. "
        "Set CO2OPS_API_KEY to enforce token authentication in production."
    )


class ApiKeyMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if request.url.path in PUBLIC_PATHS:
            return await call_next(request)

        # Enforce API key if configured
        if API_KEY:
            provided = request.headers.get("x-api-key")
            if provided != API_KEY:
                logger.warning(f"Rejected request to {request.url.path} - missing/invalid API key.")
                return JSONResponse(status_code=401, content={"detail": "Missing or invalid API key."})

        return await call_next(request)


# Mirrors the flags the old CMD passed to `adk api_server --host 0.0.0.0 --port 8080
# --allow_origins "*" --auto_create_session "/app"`, just built programmatically so
# we can attach the auth middleware.
app: FastAPI = get_fast_api_app(
    agents_dir=AGENTS_DIR,
    allow_origins=ALLOWED_ORIGINS,
    web=False,
    auto_create_session=True,
    host=HOST,
    port=PORT,
)

app.add_middleware(ApiKeyMiddleware)


if __name__ == "__main__":
    uvicorn.run(app, host=HOST, port=PORT)
