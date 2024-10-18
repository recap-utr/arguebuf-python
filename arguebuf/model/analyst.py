from arguebuf.model import utils
from arguebuf.model.userdata import Userdata

__all__ = ("Analyst",)


class Analyst:
    name: str | None
    email: str | None
    userdata: Userdata
    _id: str

    def __init__(
        self,
        name: str | None = None,
        email: str | None = None,
        userdata: Userdata | None = None,
        id: str | None = None,
    ) -> None:
        self.name = name
        self.email = email
        self.userdata = userdata or {}
        self._id = id or utils.uuid()

    @property
    def id(self) -> str:
        return self._id
