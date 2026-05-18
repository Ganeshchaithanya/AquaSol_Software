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
        admin_phone = "9900990099"
        result = await db.execute(select(User).where(User.phone == admin_phone))
        if not result.scalar_one_or_none():
            admin = User(
                id=uuid.uuid4(),
                name="Admin User",
                phone=admin_phone,
                email="admin@aquasol.com",
                hashed_password=pwd_ctx.hash("password123"),
                preferred_lang="en"
            )
            db.add(admin)
            await db.commit()
            print(f"Admin user created: {admin_phone} / password123")
        else:
            print("Admin user already exists.")

        # Create Custom User for chaithanyaug@gmail.com
        user_email = "chaithanyaug@gmail.com"
        result_user = await db.execute(select(User).where(User.email == user_email))
        if not result_user.scalar_one_or_none():
            user = User(
                id=uuid.uuid4(),
                name="Chaithanya UG",
                phone="9988776655",
                email=user_email,
                hashed_password=pwd_ctx.hash("password123"),
                preferred_lang="en"
            )
            db.add(user)
            await db.commit()
            print(f"User created: {user_email} / password123")
        else:
            print(f"User {user_email} already exists.")


    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(seed_db())

