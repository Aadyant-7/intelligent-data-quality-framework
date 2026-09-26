from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import Column, Integer, String, DateTime
from datetime import datetime, timezone


class Base(DeclarativeBase):
    pass


def utc_now_naive() -> datetime:
    """Keep the existing timestamp column type while avoiding deprecated utcnow()."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


class Dataset(Base):
    __tablename__ = "datasets"

    id = Column(Integer, primary_key=True, index=True)

    file_name = Column(String, nullable=False)

    file_path = Column(String, nullable=False)

    rows_count = Column(Integer)

    columns_count = Column(Integer)

    uploaded_at = Column(DateTime, default=utc_now_naive)
