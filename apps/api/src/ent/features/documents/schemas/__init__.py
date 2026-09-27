"""Document schemas."""

from ent.features.documents.schemas.requests import (
    DocumentCreate,
    DocumentFinalize,
    DocumentRecipientCreate,
    DocumentTemplateCreate,
    DocumentTemplateVersionCreate,
)
from ent.features.documents.schemas.responses import (
    DocumentDownloadRead,
    DocumentRead,
    DocumentRecipientRead,
    DocumentTemplateRead,
)

__all__ = [
    "DocumentCreate",
    "DocumentDownloadRead",
    "DocumentFinalize",
    "DocumentRead",
    "DocumentRecipientCreate",
    "DocumentRecipientRead",
    "DocumentTemplateCreate",
    "DocumentTemplateRead",
    "DocumentTemplateVersionCreate",
]
