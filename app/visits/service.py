from app.core.cache import Cache

VISITS_KEY = "notes:visits"


async def record_visit(cache: Cache) -> int:
    return int(await cache.client.incr(VISITS_KEY))


async def count_visits(cache: Cache) -> int:
    value = await cache.client.get(VISITS_KEY)
    return int(value or 0)
