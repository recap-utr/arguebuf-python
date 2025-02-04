from arguebuf.model import utils
from arguebuf.model.metadata import Metadata
from arguebuf.model.userdata import Userdata

__all__ = ("Participant",)


class Participant:
    name: str | None
    username: str | None
    email: str | None
    url: str | None
    location: str | None
    description: str | None
    metadata: Metadata
    userdata: Userdata
    _id: str

    def __init__(
        self,
        name: str | None = None,
        username: str | None = None,
        email: str | None = None,
        url: str | None = None,
        location: str | None = None,
        description: str | None = None,
        metadata: Metadata | None = None,
        userdata: Userdata | None = None,
        id: str | None = None,
    ) -> None:
        self.name = name
        self.username = username
        self.email = email
        self.url = url
        self.location = location
        self.description = description
        self.metadata = metadata or Metadata()
        self.userdata = userdata or {}
        self._id = id or utils.uuid()

    @property
    def id(self) -> str:
        return self._id
