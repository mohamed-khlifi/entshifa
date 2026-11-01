"""Audiology HTTP router aggregate."""

from __future__ import annotations

from fastapi import APIRouter

from ent.features.audiology.routes.audiograms import router as audiograms_router
from ent.features.audiology.routes.evoked import router as evoked_router
from ent.features.audiology.routes.speech import router as speech_router
from ent.features.audiology.routes.tympanometry import router as tympanometry_router

router = APIRouter()
router.include_router(audiograms_router)
router.include_router(speech_router)
router.include_router(tympanometry_router)
router.include_router(evoked_router)
