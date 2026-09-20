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
import traceback

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


def _cors_origin(request_origin: str) -> str:
    """Return the origin to echo back in Access-Control-Allow-Origin."""
    if "*" in ALLOWED_ORIGINS:
        return "*"
    if request_origin in ALLOWED_ORIGINS:
        return request_origin
    return ""


# ---------------------------------------------------------------------------
# Raw ASGI middleware — wraps the ENTIRE app including all inner middleware.
# BaseHTTPMiddleware has a known bug where unhandled exceptions in call_next
# produce bare 500 responses that bypass outer middleware. This raw ASGI
# wrapper is immune to that: it intercepts the response at the ASGI protocol
# level and injects CORS headers into every single response.
# ---------------------------------------------------------------------------
class CORSAlwaysMiddleware:
    """Raw ASGI middleware that guarantees CORS headers on every response."""

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        # Extract origin from request headers
        request_headers = dict(scope.get("headers", []))
        raw_origin = request_headers.get(b"origin", b"").decode("latin-1")
        cors_origin = _cors_origin(raw_origin) if raw_origin else "*"

        # Handle preflight
        if scope["method"] == "OPTIONS":
            response_headers = [
                (b"access-control-allow-origin", cors_origin.encode()),
                (b"access-control-allow-methods", b"GET, POST, PUT, DELETE, OPTIONS, PATCH, HEAD"),
                (b"access-control-allow-headers", b"*"),
                (b"access-control-allow-credentials", b"true"),
                (b"access-control-max-age", b"86400"),
                (b"content-length", b"0"),
            ]
            if cors_origin != "*":
                response_headers.append((b"vary", b"Origin"))
            await send({"type": "http.response.start", "status": 200, "headers": response_headers})
            await send({"type": "http.response.body", "body": b""})
            return

        # For non-preflight requests, intercept the response to inject CORS headers
        cors_headers_to_inject = [
            (b"access-control-allow-origin", cors_origin.encode()),
            (b"access-control-allow-credentials", b"true"),
        ]
        if cors_origin != "*":
            cors_headers_to_inject.append((b"vary", b"Origin"))

        async def send_with_cors(message):
            if message["type"] == "http.response.start":
                # Filter out any existing CORS headers to avoid duplicates
                existing = [
                    (k, v) for k, v in message.get("headers", [])
                    if k.lower() not in (
                        b"access-control-allow-origin",
                        b"access-control-allow-credentials",
                    )
                ]
                message["headers"] = existing + cors_headers_to_inject
            await send(message)

        try:
            await self.app(scope, receive, send_with_cors)
        except Exception:
            # If the inner app crashes catastrophically, still send a
            # CORS-compliant 500 so the browser doesn't mask it as CORS.
            logger.error("Unhandled ASGI error:\n%s", traceback.format_exc())
            error_headers = cors_headers_to_inject + [
                (b"content-type", b"application/json"),
            ]
            body = b'{"detail":"Internal server error"}'
            error_headers.append((b"content-length", str(len(body)).encode()))
            await send({
                "type": "http.response.start",
                "status": 500,
                "headers": error_headers,
            })
            await send({"type": "http.response.body", "body": body})


# ---------------------------------------------------------------------------
# API Key enforcement as raw ASGI middleware (avoids BaseHTTPMiddleware bugs)
# ---------------------------------------------------------------------------
class ApiKeyMiddleware:
    """Raw ASGI middleware for API key enforcement."""

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        path = scope.get("path", "/")

        # Skip auth for public paths and OPTIONS
        if path in PUBLIC_PATHS or scope["method"] == "OPTIONS":
            await self.app(scope, receive, send)
            return

        # Check API key if configured
        if API_KEY:
            request_headers = dict(scope.get("headers", []))
            provided = request_headers.get(b"x-api-key", b"").decode("latin-1")
            if provided != API_KEY:
                logger.warning("Rejected request to %s - missing/invalid API key.", path)
                body = b'{"detail":"Missing or invalid API key."}'
                headers = [
                    (b"content-type", b"application/json"),
                    (b"content-length", str(len(body)).encode()),
                ]
                await send({"type": "http.response.start", "status": 401, "headers": headers})
                await send({"type": "http.response.body", "body": body})
                return

        await self.app(scope, receive, send)


# Build the ADK FastAPI app
app: FastAPI = get_fast_api_app(
    agents_dir=AGENTS_DIR,
    allow_origins=ALLOWED_ORIGINS,
    web=False,
    auto_create_session=True,
    host=HOST,
    port=PORT,
)

# Wrap with our raw ASGI middleware (order: CORSAlways -> ApiKey -> ADK app)
# In ASGI wrapping, the outermost wrapper runs first.
app = ApiKeyMiddleware(app)
app = CORSAlwaysMiddleware(app)


if __name__ == "__main__":
    uvicorn.run(app, host=HOST, port=PORT)

