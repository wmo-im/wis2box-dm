from typing import List, Union
from sqlalchemy import String, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import mapped_column, registry, Mapped


mapper_registry = registry()
Base = mapper_registry.generate_base()
numeric = Union[int, float]


# Simple class to store pygeoapi resource dict as jsonb
class Resource(Base):
    __tablename__ = "resources"
    __table_args__ = {"schema": "pygeoapi"}
    id: Mapped[str] = mapped_column(String, primary_key = True)
    type: Mapped[str] = mapped_column(String, nullable=False)
    details: Mapped[dict] = mapped_column(JSONB, nullable=True)