from datetime import UTC, datetime

from sqlalchemy import DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Lead(Base):
    __tablename__ = "leads"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    instagram_username: Mapped[str] = mapped_column(String, index=True, nullable=False)
    instagram_user_id: Mapped[str] = mapped_column(String, index=True, unique=True, nullable=False)
    message_template: Mapped[str] = mapped_column(Text, nullable=False)

    # pending, sent, failed, replied
    status: Mapped[str] = mapped_column(String, default="pending", index=True)
    sent_timestamp: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Reply tracking data
    reply_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    tag: Mapped[str | None] = mapped_column(String, nullable=True)  # Interested, NotInterested
    reply_timestamp: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )
