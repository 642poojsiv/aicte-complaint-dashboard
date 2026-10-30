from datetime import datetime, timezone
from sqlalchemy import String, Integer, DateTime, ForeignKey, Text, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .database import Base

def utcnow():
    return datetime.now(timezone.utc)

class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120))
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(20), default="Viewer")

class Institution(Base):
    __tablename__ = "institutions"
    id: Mapped[int] = mapped_column(primary_key=True)
    permanent_id: Mapped[str] = mapped_column(String(80), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(255))
    region: Mapped[str] = mapped_column(String(120), default="")
    compliance_rating: Mapped[str] = mapped_column(String(40), default="Not assessed")

class Complaint(Base):
    __tablename__ = "complaints"
    id: Mapped[int] = mapped_column(primary_key=True)
    complaint_no: Mapped[str] = mapped_column(String(30), unique=True, index=True)
    institution_id: Mapped[int] = mapped_column(ForeignKey("institutions.id"))
    complainant_name: Mapped[str] = mapped_column(String(160))
    complainant_email: Mapped[str] = mapped_column(String(255))
    category: Mapped[str] = mapped_column(String(80))
    subject: Mapped[str] = mapped_column(String(255))
    description: Mapped[str] = mapped_column(Text)
    document_url: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    assigned_cell: Mapped[str] = mapped_column(String(120))
    status: Mapped[str] = mapped_column(String(30), default="Pending")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    due_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    institution: Mapped[Institution] = relationship()

class AuditLog(Base):
    __tablename__ = "audit_logs"
    id: Mapped[int] = mapped_column(primary_key=True)
    complaint_id: Mapped[int] = mapped_column(ForeignKey("complaints.id"), index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    action: Mapped[str] = mapped_column(String(120))
    details: Mapped[str] = mapped_column(Text, default="")
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    user: Mapped[User] = relationship()
