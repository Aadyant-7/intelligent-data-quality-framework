from sqlalchemy.orm import sessionmaker

from app.database import engine
from app.models import Dataset

SessionLocal = sessionmaker(bind=engine)

db = SessionLocal()

dataset = Dataset(
    file_name="sales.csv",
    file_path="datasets/sales.csv",
    rows_count=5000,
    columns_count=12
)

db.add(dataset)
db.commit()

print("✅ Record inserted successfully")