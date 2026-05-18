import asyncio
from sqlalchemy import text
from backend.db.session import engine

async def reset_db():
    async with engine.begin() as conn:
        print("Dropping all tables...")
        # Get all table names
        result = await conn.execute(text("SELECT tablename FROM pg_catalog.pg_tables WHERE schemaname = 'public'"))
        tables = [row[0] for row in result.all()]
        
        if tables:
            # Drop all tables in public schema
            tables_str = ", ".join(f'"{t}"' for t in tables)
            await conn.execute(text(f"DROP TABLE IF EXISTS {tables_str} CASCADE"))
            print(f"Dropped: {tables_str}")
        else:
            print("No tables found.")

    await engine.dispose()
    print("Database cleared. Run recreate_schema.py to recreate all tables.")

if __name__ == "__main__":
    asyncio.run(reset_db())

