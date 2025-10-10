from __future__ import annotations

from discord import Color

# fmt: off
__all__ = (
    "danny_red",
    "danny_green",
)
# fmt: on

def danny_red() -> Color:
    """A factory method that returns a Colour with a value of 0xDD5F53."""
    return Color(0xDD5F53)

def danny_green() -> Color:
    """A factory method that returns a Colour with a value of 0x53DDA4."""
    return Color(0x53DDA4)
