"""Email integration."""

from ent.integrations.email.outbox import (
    OutboundEmail,
    get_email_outbox,
    send_transactional,
)

__all__ = ["OutboundEmail", "get_email_outbox", "send_transactional"]
