"""Patient SMS and WhatsApp capture for local delivery and tests."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

from ent.settings import Settings, get_settings

logger = logging.getLogger("ent.messaging")


@dataclass(frozen=True, slots=True)
class OutboundMessage:
    channel: str
    to: str
    locale: str
    template_code: str
    context: dict[str, Any]


@dataclass
class MessagingOutbox:
    messages: list[OutboundMessage] = field(default_factory=list)

    def clear(self) -> None:
        self.messages.clear()


_outbox = MessagingOutbox()


def get_messaging_outbox() -> MessagingOutbox:
    return _outbox


def send_patient_message(
    *,
    channel: str,
    to: str,
    locale: str,
    template_code: str,
    context: dict[str, Any],
    settings: Settings | None = None,
) -> None:
    resolved = settings or get_settings()
    logger.info("patient_message channel=%s template=%s", channel, template_code)
    if resolved.app_env == "local":
        _outbox.messages.append(
            OutboundMessage(
                channel=channel,
                to=to,
                locale=locale,
                template_code=template_code,
                context=dict(context),
            ),
        )
