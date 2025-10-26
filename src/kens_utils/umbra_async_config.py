"""
Sourced from https://github.com/AbstractUmbra/Shared-Bot-Utilities/blob/aa4bd59a5b64e39f5de32b501a9ff3e71ad4048b/async_config.py

This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at http://mozilla.org/MPL/2.0/.

This file was sourced from [RoboDanny](https://github.com/Rapptz/RoboDanny).
"""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING, Any, TypeVar, overload

from .formats import from_json, to_json

if TYPE_CHECKING:
    import pathlib

    T = TypeVar("T", default=Any)
else:
    T = TypeVar("T")
_defT = TypeVar("_defT")  # noqa: N816 # how typeshed does it


class Config[T]:
    """The "database" object. Internally based on ``json``."""

    def __init__(
        self,
        path: pathlib.Path,
        /,
        *,
        load_later: bool = False,
    ) -> None:
        self.path = path
        self.loop = asyncio.get_event_loop()
        self.lock = asyncio.Lock()
        self._db: dict[str, T] = {}

        if load_later:
            self.loop.create_task(self.load())
        else:
            self.load_from_file()

    def load_from_file(self) -> None:
        try:
            with self.path.open() as f:
                self._db = from_json(f.read())
        except FileNotFoundError:
            self._db = {}

    async def load(self) -> None:
        async with self.lock:
            await self.loop.run_in_executor(None, self.load_from_file)

    def _dump(self) -> None:
        temp = self.path.with_suffix(".tmp")
        with temp.open("w", encoding="utf-8") as tmp:
            tmp.write(to_json(self._db.copy()))

        # atomically move the file
        temp.replace(self.path)

    async def save(self) -> None:
        async with self.lock:
            await self.loop.run_in_executor(None, self._dump)

    @overload
    def get(self, key: Any) -> T | None: ...

    @overload
    def get(self, key: Any, default: _defT) -> T | _defT: ...

    def get(self, key: Any, default: _defT | None = None) -> T | _defT | None:
        """Retrieves a config entry."""
        return self._db.get(str(key), default)

    async def put(self, key: Any, value: T) -> None:
        """Edits a config entry."""
        self._db[str(key)] = value
        await self.save()

    async def remove(self, key: Any) -> None:
        """Removes a config entry."""
        try:
            del self._db[str(key)]
        except KeyError:
            return
        await self.save()

    def __contains__(self, item: Any) -> bool:
        return str(item) in self._db

    def __getitem__(self, item: Any) -> T:
        return self._db[str(item)]

    def __len__(self) -> int:
        return len(self._db)

    def all(self) -> dict[str, T]:
        return self._db