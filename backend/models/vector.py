import enum
import uuid
from datetime import datetime

from sqlalchemy import String, Boolean, Text, Enum, ForeignKey, DateTime, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from pgvector.sqlalchemy import Vector

from models.base import Base, UUIDPrimaryKeyMixin


class VectorSourceType(str, enum.Enum):
    task = "task"
    task_completion = "task_completion"
    inventory = "inventory"
    calendar_event = "calendar_event"
    chat_message = "chat_message"
    pattern = "pattern"
    onboarding_answer = "onboarding_answer"
    summary = "summary"


class VectorDocument(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "vector_documents"

    household_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("households.id", ondelete="CASCADE"), nullable=False, index=True
    )
    member_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("members.id", ondelete="SET NULL"), nullable=True
    )
    source_type: Mapped[VectorSourceType] = mapped_column(
        Enum(VectorSourceType, name="vector_source_type"), nullable=False
    )
    source_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    embedding = mapped_column(Vector(1536), nullable=True)
    embedding_model: Mapped[str] = mapped_column(
        String, nullable=False, default="text-embedding-3-small"
    )
    metadata_: Mapped[dict | None] = mapped_column("metadata", JSONB, nullable=True)
    is_summary: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    summarizes_before: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    household = relationship("Household", back_populates="vector_documents")
