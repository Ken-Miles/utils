from enum import Enum
from typing import Callable

import aiohttp

# fmt: off
__all__ = (
    "RequestType",
    "IntegrationType",
)
# fmt: on

class RequestType(Enum):
    GET = "GET"
    POST = "POST"
    PATCH = "PATCH"
    PUT = "PUT"
    DELETE = "DELETE"

    def get_method_callable(self, session: aiohttp.ClientSession) -> Callable:
        if self is RequestType.GET:
            return session.get
        elif self is RequestType.POST:
            return session.post
        elif self is RequestType.PATCH:
            return session.patch
        elif self is RequestType.PUT:
            return session.put
        elif self is RequestType.DELETE:
            return session.delete
        raise ValueError(f"Invalid request type {self}")

    def __str__(self):
        return self.value.upper()


class IntegrationType(Enum):
    """An Enum representing the type of integration for a discord bot."""    
    guild = 0
    user = 1

    def __int__(self) -> int:
        return self.value

    def __str__(self) -> str:
        return self.name
