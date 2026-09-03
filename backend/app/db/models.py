"""
Real persisted tables, replacing the in-memory dicts that used to live in
app/agents/tools/evidence_tools.py and notify_tools.py. Complex nested
structures (EvidenceRecord's per-source lists, lineage entries) are stored
as JSON columns rather than fully normalized -- this is still real
persistence (survives a process restart, queryable by event_id, backed by
an actual file on disk), not a stub; full normalization is a reasonable
follow-up once the schema stabilizes, not a prerequisite for "real."
"""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import JSON, Boolean, DateTime, Float, ForeignKey, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class EvidenceRecordRow(Base):
    __tablename__ = "evidence_records"

    event_id: Mapped[str] = mapped_column(String, primary_key=True)
    created_at: Mapped[datetime] = mapped_column(DateTime)
    window_start: Mapped[datetime] = mapped_column(DateTime)
    window_end: Mapped[datetime] = mapped_column(DateTime)
    bbox: Mapped[dict] = mapped_column(JSON)
    sources: Mapped[dict] = mapped_column(JSON)
    lineage: Mapped[list] = mapped_column(JSON)
    vision_confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    vision_lineage_ref: Mapped[str | None] = mapped_column(String, nullable=True)


class FieldImageRow(Base):
    __tablename__ = "field_images"

    event_id: Mapped[str] = mapped_column(
        String, ForeignKey("evidence_records.event_id"), primary_key=True
    )
    image_bytes: Mapped[bytes] = mapped_column()
    uploaded_at: Mapped[datetime] = mapped_column(DateTime)


class ApprovalRow(Base):
    __tablename__ = "approvals"

    approval_id: Mapped[str] = mapped_column(String, primary_key=True)
    event_id: Mapped[str] = mapped_column(String, ForeignKey("evidence_records.event_id"))
    proposed_action: Mapped[dict] = mapped_column(JSON)
    status: Mapped[str] = mapped_column(String, default="pending")  # pending|approved|rejected
    approver: Mapped[str | None] = mapped_column(String, nullable=True)
    reason: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime)


class LifeSafetyGuidanceRow(Base):
    __tablename__ = "lifesafety_guidance"

    event_id: Mapped[str] = mapped_column(
        String, ForeignKey("evidence_records.event_id"), primary_key=True
    )
    guidance_text: Mapped[str] = mapped_column(String)
    approved: Mapped[bool] = mapped_column(Boolean, default=False)


class InsurerExposureReportRow(Base):
    __tablename__ = "insurer_exposure_reports"

    event_id: Mapped[str] = mapped_column(
        String, ForeignKey("evidence_records.event_id"), primary_key=True
    )
    policies: Mapped[list] = mapped_column(JSON)
    total_estimated_exposure_usd: Mapped[float] = mapped_column(Float)
    approved: Mapped[bool] = mapped_column(Boolean, default=False)
