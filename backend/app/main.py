"""
FastAPI Application Factory & Middleware
"""
import os
from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from backend.config.settings import get_settings
from backend.utils.logger import logger

# Import routers
from backend.api.auth import router as auth_router
from backend.api.sensors import router as sensor_router
from backend.api.dashboard import router as dashboard_router
from backend.api.control import router as control_router
from backend.api.chatbot import router as chatbot_router
from backend.api.planner import router as planner_router
from backend.api.reports import router as reports_router
from backend.api.farm import router as farm_router
from backend.api.v1.subsidy import router as subsidy_router
from backend.api.stage import router as stage_router
from backend.api.device import router as device_router
from backend.api.pairing import router as pairing_router
from backend.api.alerts import router as alerts_router
from backend.api.intelligence import router as intelligence_router

# Import startup lifecycle
from backend.app.startup import lifespan


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title=settings.PROJECT_NAME,
        version=settings.VERSION,
        lifespan=lifespan,
    )

    # CORS Policy
    # We allow the specific render domain, plus a wildcard regex to catch any render subdomain if it gets renamed, 
    # as well as localhost for local development.
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "https://irrigation-api-v2.onrender.com",
            "http://localhost:3000",
            "http://localhost:8000"
        ],
        allow_origin_regex=r"https?://.*\.onrender\.com(:\d+)?",
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["*"],
    )

    # Request Logger for Debugging
    @app.middleware("http")
    async def log_requests(request: Request, call_next):
        logger.info(f"[app] {request.method} {request.url.path}")
        response = await call_next(request)
        return response

    # Global Exception Handler
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        logger.error(f"[app] Validation error on {request.url.path}: {exc.errors()}")
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={"detail": exc.errors(), "body": str(exc.body)},
        )

    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        logger.error(f"[app] Unhandled exception on {request.url.path}: {exc}")
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal Server Error", "error": str(exc)},
        )

    # Routers
    api_prefix = "/api/v1"
    app.include_router(auth_router, prefix=api_prefix)
    app.include_router(sensor_router, prefix=api_prefix)
    app.include_router(dashboard_router, prefix=api_prefix)
    app.include_router(control_router, prefix=api_prefix)
    app.include_router(chatbot_router, prefix=api_prefix)
    app.include_router(planner_router, prefix=api_prefix)
    app.include_router(reports_router, prefix=api_prefix)
    app.include_router(farm_router, prefix=api_prefix)
    app.include_router(subsidy_router, prefix=api_prefix)
    app.include_router(stage_router, prefix=api_prefix)
    app.include_router(device_router, prefix=api_prefix)
    # Master Hardware Compatibility Redirects
    app.include_router(sensor_router, prefix="/api")
    app.include_router(device_router, prefix="/api/device")
    app.include_router(device_router, prefix="/api")
    app.include_router(control_router, prefix="/api")
    app.include_router(control_router, prefix="/api/control")
    
    app.include_router(pairing_router, prefix=api_prefix)
    app.include_router(alerts_router, prefix=api_prefix)
    app.include_router(intelligence_router, prefix=api_prefix)

    # Company-internal admin endpoints (protected by X-Admin-Key header)
    from backend.api.admin import router as admin_router
    from backend.api.profile import router as profile_router
    from backend.api.support import router as support_router
    from backend.api.notifications import router as notifications_router
    app.include_router(admin_router, prefix=api_prefix)
    # New routers
    app.include_router(profile_router, prefix=api_prefix)
    app.include_router(support_router, prefix=api_prefix)
    app.include_router(notifications_router, prefix=api_prefix)

    # Root endpoint for health checks (Fixes the 404 on /)
    @app.get("/")
    async def root():
        return {
            "status": "online", 
            "message": "AquaSol API is running",
            "version": settings.VERSION
        }

    # Favicon endpoint (Fixes the 404 on /favicon.ico)
    @app.get("/favicon.ico", include_in_schema=False)
    async def favicon():
        # Return 204 No Content for favicon requests from browsers
        from fastapi import Response
        return Response(status_code=204)

    return app

app = create_app()

# Serve static avatar files
from fastapi.staticfiles import StaticFiles
app.mount("/static", StaticFiles(directory="static"), name="static")
