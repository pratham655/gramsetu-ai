from datetime import datetime
import uuid
from sqlalchemy import (
    Column,
    String,
    Text,
    Boolean,
    DateTime,
    ForeignKey,
    JSON,
)
from sqlalchemy.orm import relationship
from app.database.base import Base


class Scheme(Base):
    __tablename__ = "schemes"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(255), nullable=False, index=True)
    short_description = Column(String(500), nullable=False)
    detailed_description = Column(Text, nullable=False)
    benefits = Column(JSON, nullable=False, default=list)  # List of benefit descriptions
    state = Column(String(100), nullable=True, index=True)  # Nullable for Central schemes
    category = Column(String(100), nullable=True)  # e.g., Agriculture, Housing, Health
    occupation = Column(String(100), nullable=True)  # e.g., Farmer, Artisan, Student
    official_source_url = Column(String(500), nullable=False)
    application_url = Column(String(500), nullable=True)
    required_documents = Column(JSON, nullable=False, default=list)  # List of document names
    active = Column(Boolean, default=True, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    rules = relationship(
        "EligibilityRule",
        back_populates="scheme",
        cascade="all, delete-orphan",
        lazy="joined",
    )


class EligibilityRule(Base):
    __tablename__ = "eligibility_rules"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    scheme_id = Column(String(36), ForeignKey("schemes.id", ondelete="CASCADE"), nullable=False, index=True)
    field = Column(String(100), nullable=False)  # age, income, state, district, gender, occupation, landholding, category, bpl
    operator = Column(String(50), nullable=False)  # equals, not_equals, greater_than, greater_than_or_equal, less_than, less_than_or_equal, in, not_in
    value = Column(String(255), nullable=False)  # Serialized target value
    description = Column(Text, nullable=True)  # Human-readable rule explanation

    scheme = relationship("Scheme", back_populates="rules")
