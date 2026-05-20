"""Contact‑Us support endpoint.

Stores a request in the `support_requests` table.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from backend.db.session import get_db
from backend.models.support_request import SupportRequest
from backend.api.auth import get_current_user
from backend.utils.logger import logger

router = APIRouter(prefix="/support", tags=["Support"])

class ContactUsRequest(BaseModel):
    subject: str
    message: str
    # Optional: allow anonymous submissions
    user_id: str | None = None

@router.post("/contact", status_code=201)
async def contact_us(
    payload: ContactUsRequest,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user),
):
    """Create a support request.

    If the request is made by an authenticated user, their user_id is stored;
    otherwise the optional `user_id` field may be provided.
    """
    user_id = payload.user_id or getattr(current_user, "id", None)
    req = SupportRequest(
        user_id=user_id,
        subject=payload.subject,
        message=payload.message,
    )
    db.add(req)
    await db.commit()
    logger.info(f"[support] New contact request stored for user {user_id}")
    return {"status": "received", "request_id": str(req.id)}
