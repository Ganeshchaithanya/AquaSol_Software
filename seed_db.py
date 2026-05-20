import asyncio
import uuid
from sqlalchemy import select
from passlib.context import CryptContext
from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession

from backend.db.session import engine
from backend.models.user import User

pwd_ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")

async def seed_db():
    AsyncSessionLocal = async_sessionmaker(bind=engine, class_=AsyncSession)

    async with AsyncSessionLocal() as db:
        # Create Admin User
        admin_phone = "9449584809"
        result = await db.execute(select(User).where(User.phone == admin_phone))
        if not result.scalar_one_or_none():
            admin = User(
                id=uuid.uuid4(),
                name="Admin User",
                phone=admin_phone,
                email="admin@aquasol.com",
                hashed_password=pwd_ctx.hash("admin@agz2026"),
                preferred_lang="en"
            )
            db.add(admin)
            await db.commit()
            print(f"Admin user created: {admin_phone} / admin@agz2026")
        else:
            print("Admin user already exists.")




    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(seed_db())

