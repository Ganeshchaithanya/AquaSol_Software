import asyncio
from sqlalchemy import text
from backend.db.session import engine

async def check():
    async with engine.connect() as conn:
        r = await conn.execute(text("SELECT tablename FROM pg_catalog.pg_tables WHERE schemaname='public'"))
        tables = [row[0] for row in r.all()]
        print(f"{'Table':<30} {'Rows':>6}")
        print("-" * 38)
        for t in tables:
            cnt = await conn.execute(text(f'SELECT COUNT(*) FROM "{t}"'))
            print(f"{t:<30} {cnt.scalar():>6}")
            
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(check())

