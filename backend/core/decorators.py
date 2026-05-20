import functools
from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncSession
from backend.db.session import get_db
from backend.models.activity_log import ActivityLog
from backend.utils.logger import logger

def audit(action: str, resource: str | None = None):
    """FastAPI dependency decorator to log audit entries.
    Captures the current user (via get_current_user dependency), request IP
    and User‑Agent header, and stores a row in `activity_logs`.
    """
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, request: Request, db: AsyncSession = await get_db(), **kwargs):
            # Try to extract user from kwargs (most endpoints depend on get_current_user)
            user = kwargs.get("current_user")
            user_id = str(user.id) if user else None
            ip = request.client.host if request.client else None
            ua = request.headers.get("user-agent")
            # Create log entry before execution
            log = ActivityLog(
                user_id=user_id,
                action=action,
                resource=resource,
                ip_address=ip,
                user_agent=ua,
            )
            db.add(log)
            await db.flush()
            logger.info(f"[audit] {action} by user {user_id or 'anon'} from {ip}")
            try:
                result = await func(*args, request=request, db=db, **kwargs)
                return result
            except Exception as e:
                # Update log with error info if needed (metadata)
                log.metadata = {"error": str(e)}
                await db.flush()
                logger.error(f"[audit] error during {action}: {e}")
                raise
        return wrapper
    return decorator
