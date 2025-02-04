import pendulum

__all__ = ("Metadata",)


class Metadata:
    created: pendulum.DateTime
    updated: pendulum.DateTime

    def __init__(
        self,
        created: pendulum.DateTime | None = None,
        updated: pendulum.DateTime | None = None,
    ) -> None:
        now = pendulum.now()

        self.created = created or now
        self.updated = updated or now

    def update(self) -> None:
        self.updated = pendulum.now()
