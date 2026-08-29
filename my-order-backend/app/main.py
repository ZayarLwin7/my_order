from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.trustedhost import TrustedHostMiddleware
from app.config import settings
from app.routers import auth, riders, orders, tracking, riders_wallet, disputes, partners, finance, rider_earnings, pricing, users

is_production = settings.environment.lower() == "production"
app = FastAPI(
    title="My Order API",
    version="0.1.0",
    docs_url=None if is_production else "/docs",
    redoc_url=None if is_production else "/redoc",
)

allowed_origins = settings.csv(settings.allowed_origins)
if allowed_origins:
    cors_kwargs = {
        "allow_methods": ["GET", "POST", "PATCH"],
        "allow_headers": ["Authorization", "Content-Type"],
    }
    if is_production:
        # Strict allowlist in production.
        cors_kwargs["allow_origins"] = allowed_origins
        cors_kwargs["allow_credentials"] = True
    else:
        # Development: any local origin (Flutter web dev server uses a random port).
        cors_kwargs["allow_origin_regex"] = r"http://(localhost|127\.0\.0\.1)(:\d+)?"
    app.add_middleware(CORSMiddleware, **cors_kwargs)

allowed_hosts = settings.csv(settings.allowed_hosts)
if allowed_hosts:
    # Add testserver for test client compatibility
    if not is_production:
        allowed_hosts.append("testserver")
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=allowed_hosts)


@app.middleware("http")
async def enforce_request_size_and_security_headers(request: Request, call_next):
    content_length = request.headers.get("content-length")
    if content_length:
        try:
            exceeds_limit = int(content_length) > settings.max_request_body_bytes
        except ValueError:
            return JSONResponse(status_code=400, content={"detail": "Invalid Content-Length header"})
        if exceeds_limit:
            return JSONResponse(status_code=413, content={"detail": "Request body too large"})

    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "no-referrer"
    response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
    if is_production:
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    return response

app.include_router(auth.router, prefix="/api/v1")
app.include_router(riders.router, prefix="/api/v1")
app.include_router(orders.router, prefix="/api/v1")
app.include_router(tracking.router, prefix="/api/v1")
app.include_router(riders_wallet.router, prefix="/api/v1")
app.include_router(disputes.router, prefix="/api/v1")
app.include_router(partners.router, prefix="/api/v1")
app.include_router(finance.router, prefix="/api/v1")
app.include_router(rider_earnings.router, prefix="/api/v1")
app.include_router(pricing.router, prefix="/api/v1")
app.include_router(users.router, prefix="/api/v1")

@app.get("/")
def root():
    return {"status": "ok", "service": "my-order-backend"}
