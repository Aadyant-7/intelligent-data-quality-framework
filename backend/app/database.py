from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from app.models import Base

DATABASE_URL = None # Credential removed

engine = create_engine(DATABASE_URL)

try:
    with engine.connect() as connection:
        connection.execute(text("SELECT 1"))
    print("✅ Database connected successfully")
except Exception as e:
    print(f"❌ Database connection failed: {e}")

Base.metadata.create_all(bind=engine)

print("✅ Tables created successfully")