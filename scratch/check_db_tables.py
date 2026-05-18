import os
from sqlalchemy import create_engine, text

db_url = "postgresql://neondb_owner:npg_Lbf9rKJHMSW3@ep-restless-meadow-a1l64nqq-pooler.ap-southeast-1.aws.neon.tech/neondb?sslmode=require"
engine = create_engine(db_url)

with engine.connect() as conn:
    for table in ["farms", "zones", "node_slots", "devices", "sensor_readings", "valve_commands"]:
        count = conn.execute(text(f"SELECT COUNT(*) FROM {table}")).scalar()
        print(f"Table '{table}' has {count} rows.")
        if count > 0:
            print(f"Sample rows from '{table}':")
            rows = conn.execute(text(f"SELECT * FROM {table} ORDER BY 1 DESC LIMIT 3")).fetchall()
            for r in rows:
                print(r)
            print("-" * 40)
