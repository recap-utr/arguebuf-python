import typing as t

from arguebuf.model import utils
from arguebuf.model.userdata import Userdata

__all__ = ("Analyst",)


class Analyst:
    name: t.Optional[str]
    email: t.Optional[str]
    userdata: Userdata
    _id: str

    def __init__(
        self,
        name: t.Optional[str] = None,
        email: t.Optional[str] = None,
        userdata: t.Optional[Userdata] = None,
        id: t.Optional[str] = None,
    ) -> None:
        self.name = name
        self.email = email
        self.userdata = userdata or {}
        self._id = id or utils.uuid()

    @property
    def id(self) -> str:
        return self._id
