class CacheNotConfiguredError(Exception):
    def __init__(self) -> None:
        super().__init__("cache is not configured")
