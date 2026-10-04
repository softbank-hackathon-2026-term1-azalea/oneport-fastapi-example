from redis.asyncio import Redis


class Cache:
    def __init__(self, url: str) -> None:
        self.client: Redis = Redis.from_url(
            url,
            decode_responses=True,
            socket_connect_timeout=2,
            socket_timeout=2,
            health_check_interval=30,
        )

    async def ping(self) -> None:
        await self.client.ping()  # type: ignore[misc]

    async def close(self) -> None:
        await self.client.aclose()
