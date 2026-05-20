"""Profile related endpoints.

Provides avatar upload for a user. The uploaded image is saved under
`static/avatars/<uuid>.<ext>` and the user's `avatar_url` field is updated
to point to the relative path.
"""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from pathlib import Path
import uuid
import shutil

from backend.db.session import get_db
from backend.models.user import User
from backend.api.auth import get_current_user
from backend.utils.logger import logger

router = APIRouter(prefix="/users", tags=["Profile"])

# Ensure the avatars directory exists at startup (lazy init)
AVATAR_DIR = Path(__file__).parents[3] / "static" / "avatars"
AVATAR_DIR.mkdir(parents=True, exist_ok=True)

ALLOWED_TYPES = {"image/jpeg", "image/png"}

@router.post("/{user_id}/avatar", status_code=201)
async def upload_avatar(
    user_id: str,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Upload a profile avatar for a user.

    Only the owner or an admin can upload.
    """
    if str(current_user.id) != user_id and not getattr(current_user, "is_admin", False):
        raise HTTPException(status_code=403, detail="Not authorized to change this avatar.")

    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(status_code=415, detail="Unsupported file type. Use JPEG or PNG.")

    # Generate a safe unique filename
    ext = Path(file.filename).suffix.lower() or ".png"
    filename = f"{uuid.uuid4()}{ext}"
    file_path = AVATAR_DIR / filename

    # Save file to disk
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        logger.error(f"[avatar] Failed to save file: {e}")
        raise HTTPException(status_code=500, detail="Failed to store avatar.")

    # Update user's avatar_url (relative path used by static mounting)
    result = await db.execute(
        User.__table__.update()
        .where(User.id == user_id)
        .values(avatar_url=str(Path("avatars") / filename))
    )
    await db.commit()

    logger.info(f"[avatar] User {user_id} uploaded new avatar {filename}")
    return JSONResponse(content={"status": "success", "avatar_url": f"/static/avatars/{filename}"})
