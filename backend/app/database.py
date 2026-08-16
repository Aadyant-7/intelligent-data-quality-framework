import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from app.models import Base

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()

try:
    with engine.connect() as connection:
        connection.execute(text("SELECT 1"))
    print("✅ Database connected successfully")
except Exception as e:
    print(f"❌ Database connection failed: {e}")

Base.metadata.create_all(bind=engine)

print("✅ Tables created successfully")