import asyncio
from backend.db.session import engine
from backend.db.base import Base

# Import all models to ensure metadata is populated
import backend.models.user
import backend.models.farm
import backend.models.device
import backend.models.sensor_data
import backend.models.state
import backend.models.decision
import backend.models.crop
import backend.models.i18n
import backend.models.pairing_session

async def recreate_schema():
    async with engine.begin() as conn:
        print("Recreating all tables...")
        await conn.run_sync(Base.metadata.create_all)
        print("Schema recreation complete.")
        
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(recreate_schema())

