"""JobRun persistence (architecture section 25.17 / P0-07)."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import CheckConstraint, Index, Integer, String, Text, text
from sqlalchemy.orm import Mapped, mapped_column

from ent.core.db.base import Base
from ent.core.db.mixins import SurrogatePkMixin
from ent.core.db.mysql_types import datetime6, mysql_json
from ent.core.db.types import ULIDType
from ent.core.utils.ids import new_ulid

JOB_STATUSES = ("pending", "running", "succeeded", "failed", "dead")


class JobRun(SurrogatePkMixin, Base):
    """One execution attempt family keyed by a unique idempotency key."""

    __tablename__ = "job_run"
    __table_args__ = (
        CheckConstraint(
            "status IN ('pending','running','succeeded','failed','dead')",
            name="ck_job_run__status",
        ),
        Index("ix_job_run__status__started_at", "status", "started_at"),
        Index("ix_job_run__job_name__started_at", "job_name", "started_at"),
    )

    public_id: Mapped[str] = mapped_column(
        ULIDType(),
        nullable=False,
        unique=True,
        default=new_ulid,
        insert_default=new_ulid,
    )
    job_name: Mapped[str] = mapped_column(String(80), nullable=False)
    idempotency_key: Mapped[str] = mapped_column(
        String(120, collation="utf8mb4_0900_as_cs"),
        nullable=False,
        unique=True,
    )
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending")
    started_at: Mapped[datetime | None] = mapped_column(datetime6(), nullable=True)
    finished_at: Mapped[datetime | None] = mapped_column(datetime6(), nullable=True)
    attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    payload: Mapped[dict[str, Any] | None] = mapped_column(mysql_json(), nullable=True)
    error_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        datetime6(),
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP(6)"),
    )
