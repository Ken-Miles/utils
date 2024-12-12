from enum import Enum
from typing import Callable, List

import aiohttp
from discord import app_commands
from discord.app_commands import locale_str
from typing_extensions import Self

# fmt: off
__all__ = (
    "EnumU",
    "RequestType",
    "IntegrationType",
)
# fmt: on

class EnumU(Enum):
    """
    A custom enum class that makes implementing it as slash command/prefix command options easy.

    The following methods have default behavior, but should be overridden for your use case:
    `actual_value` (property, default returns the standard value. If you store dict info in the value, override this to return your default value)
    `to_choice` (default makes the enum name the name=, enum value the value=)
    `from_str` (default compares string to case-insensitive enum.name, case-insensitive str(enum.value))
    `to_locale_choice` (default calls to_choice and converts name to locale_str)
    `all` (classmethod)
    """

    @property
    def actual_value(self):
        return self.value

    @classmethod
    def all(cls) -> List[Self]:
        """A method to retrieve all instances of an enum.
        
        Returns an iterable with all instances of the enum within it."""
        return [x for x in cls]

    def to_choice(self) -> app_commands.Choice:
        """Converts the enum instance into a discord app commands choice.

        Returns
        -------
        :class:`discord.app_commands.Choice`
        The returned choice.
        """
        return app_commands.Choice(name=self.name, value=self.actual_value)
    
    def to_locale_choice(self, **kwargs) -> app_commands.Choice:
        """Converts the enum instance into a discord app commands choice.
        This method calls :meth:`.to_choice`, converts the name to a :class:`discord.app_commands.locale_str`, and returns it by default.
        If overridden, the returned choice should convert the name to a locale str.

        Any kwargs passed into this method will be passed into :class:`discord.app_commands.locale_str` when called.

        Returns
        -------
        :class:`discord.app_commands.Choice`
            The returned choice.
        """
        choice = self.to_choice()
        return app_commands.Choice(name=locale_str(choice.name, **kwargs), value=choice.value)

    @classmethod
    def from_str(cls, s: str) -> Self:
        """Returns an instance of this enum with a name/matching criteria to the string `s`.

        If no matching enum is found, a ValueError is raised.
        """
        s = s.strip().lower()

        for instance in cls.all():
            if s == instance.name.lower().strip() \
            or s == str(instance.actual_value).lower().strip():
            
                return instance
        
        raise ValueError(f"String {s} does not match any instances of enum {cls.__name__}")

class RequestType(Enum):
    GET = "GET"
    POST = "POST"
    PATCH = "PATCH"
    PUT = "PUT"
    DELETE = "DELETE"

    def get_method_callable(self, session: aiohttp.ClientSession) -> Callable:
        """Returns the method callable for the request type.
        Returns the callable is for the provided `session` object (ex: `session.get` for a GET instance of the enum).
        
        Parameters
        ----------
            session: :class:`aiohttp.ClientSession` The session object to get the method callable for.
        
        Returns
        -------
            :class:`Callable` The method callable for the request type.
        """

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
