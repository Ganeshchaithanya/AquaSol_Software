"""Backend API package initializer.

All routers are imported here so that `backend/api/__init__.py` can be included
by the FastAPI app factory. New routers added in this iteration are:
- profile (avatar upload)
- support (contact‑us)
- notifications (SSE stream)
"""

from fastapi import APIRouter

# Existing routers (imported in create_app) – re‑exported for convenience
from backend.api.auth import router as auth_router
from backend.api.device import router as device_router
from backend.api.farm import router as farm_router
from backend.api.sensors import router as sensor_router
from backend.api.dashboard import router as dashboard_router
from backend.api.control import router as control_router
from backend.api.chatbot import router as chatbot_router
from backend.api.planner import router as planner_router
from backend.api.reports import router as reports_router
from backend.api.stage import router as stage_router
from backend.api.pairing import router as pairing_router
from backend.api.alerts import router as alerts_router
from backend.api.intelligence import router as intelligence_router
from backend.api.admin import router as admin_router

# New routers
from backend.api.profile import router as profile_router
from backend.api.support import router as support_router
from backend.api.notifications import router as notifications_router

# Consolidated router for external import if desired
api_router = APIRouter()
for r in [
    auth_router,
    sensor_router,
    dashboard_router,
    control_router,
    chatbot_router,
    planner_router,
    reports_router,
    farm_router,
    stage_router,
    device_router,
    pairing_router,
    alerts_router,
    intelligence_router,
    admin_router,
    profile_router,
    support_router,
    notifications_router,
]:
    api_router.include_router(r)
