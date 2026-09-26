from functools import lru_cache

from ent.features.health.service import HealthService
from ent.settings import get_settings


@lru_cache
def get_health_service() -> HealthService:
    return HealthService(settings=get_settings())


def get_health_service_for_request() -> HealthService:
    return get_health_service()
