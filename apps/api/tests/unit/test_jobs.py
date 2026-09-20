"""Unit tests for job helpers (no database)."""

from __future__ import annotations

from ent.jobs.base import backoff_seconds
from ent.jobs.scheduler import SCHEDULES
from ent.jobs.tasks import JOB_HANDLE_DOMAIN_EVENT, JOB_PING_DEPENDENCIES


def test_backoff_grows_then_caps() -> None:
    assert backoff_seconds(1) == 2
    assert backoff_seconds(2) == 4
    assert backoff_seconds(8) == 256
    assert backoff_seconds(20) == 300


def test_core_jobs_are_registered() -> None:
    from ent.jobs.base import get_job as lookup

    assert lookup(JOB_HANDLE_DOMAIN_EVENT) is not None
    assert lookup(JOB_PING_DEPENDENCIES) is not None


def test_scheduler_defines_ping_interval() -> None:
    assert any(s.job_name == JOB_PING_DEPENDENCIES for s in SCHEDULES)
