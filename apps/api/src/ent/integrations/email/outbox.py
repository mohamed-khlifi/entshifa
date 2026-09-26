"""Transactional email capture for local delivery and tests.

Production SMTP sending is not wired yet. In ``local`` the message (including
the one-time token) is kept in process memory so tests and developers can
complete invite and reset flows. Other environments only log the template code.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

from ent.settings import Settings, get_settings

logger = logging.getLogger("ent.email")


@dataclass(frozen=True, slots=True)
class OutboundEmail:
    to: str
    template_code: str
    context: dict[str, Any]


@dataclass
class EmailOutbox:
    messages: list[OutboundEmail] = field(default_factory=list)

    def clear(self) -> None:
        self.messages.clear()


_outbox = EmailOutbox()


def get_email_outbox() -> EmailOutbox:
    return _outbox


def send_transactional(
    *,
    to: str,
    template_code: str,
    context: dict[str, Any],
    settings: Settings | None = None,
) -> None:
    resolved = settings or get_settings()
    logger.info("transactional_email template=%s", template_code)
    if resolved.app_env == "local":
        _outbox.messages.append(
            OutboundEmail(to=to, template_code=template_code, context=dict(context)),
        )
