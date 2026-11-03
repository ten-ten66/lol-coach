class RiotAPIError(Exception):
    def __init__(self, status_code: int, message: str, url: str | None = None) -> None:
        self.status_code = status_code
        self.url = url
        super().__init__(f"{status_code} {message}" + (f" ({url})" if url else ""))


class NotFoundError(RiotAPIError):
    pass


class UnauthorizedError(RiotAPIError):
    pass


class ForbiddenError(RiotAPIError):
    pass


class RateLimitError(RiotAPIError):
    def __init__(self, retry_after: float, url: str | None = None) -> None:
        self.retry_after = retry_after
        super().__init__(429, f"rate limited, retry after {retry_after:.1f}s", url)


class ServerError(RiotAPIError):
    pass
