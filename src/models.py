from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import Boolean, DateTime, Numeric, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class MedicalReceipt(Base):
    __tablename__ = "medical_receipts"

    id: Mapped[int] = mapped_column(primary_key=True)
    date: Mapped[datetime] = mapped_column(DateTime)
    provider: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    amount: Mapped[float] = mapped_column(Numeric(10, 2))
    hsa_eligible: Mapped[bool] = mapped_column(Boolean, default=True)
    reimbursed: Mapped[bool] = mapped_column(Boolean, default=False)
    image: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    thumbnail: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    reimbursed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
