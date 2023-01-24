from __future__ import annotations

import typing as t

import pendulum
from pendulum.datetime import DateTime



class Metadata:
    created: DateTime
    updated: DateTime
    # _analyst: t.Optional[Analyst] = None

    def __init__(
        self,
        created: t.Optional[DateTime] = None,
        updated: t.Optional[DateTime] = None,
    ) -> None:
        now = pendulum.now()

        self.created = created or now
        self.updated = updated or now

    # @property
    # def analyst(self) -> t.Optional[Analyst]:
    #     return self._analyst

    def update(self) -> None:
        self.updated = pendulum.now()
