import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

load_dotenv()
url = os.getenv('DATABASE_URL')
if not url:
    raise RuntimeError('DATABASE_URL not set')
engine = create_engine(url)
with engine.connect() as conn:
    result = conn.execute(text('SELECT COUNT(*) FROM sensor_readings')).fetchall()
    print('Sensor readings count:', result)
