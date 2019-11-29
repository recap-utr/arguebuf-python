import pendulum

ova_format = "DD/MM/YYYY - HH:mm:ss"
aif_format = "YYYY-MM-DD HH:mm:ss"


def from_ova(text: str) -> pendulum.DateTime:
    return pendulum.from_format(text, ova_format)


def to_ova(dt: pendulum.DateTime) -> str:
    # return "{date:%d/%m/%Y - %H:%M:%S}".format(date=datetime.datetime.now())
    return dt.format(ova_format)


def from_aif(text: str) -> pendulum.DateTime:
    return pendulum.from_format(text, aif_format)


def to_aif(dt: pendulum.DateTime) -> str:
    # return "{date:%Y-%m-%d %H:%M:%S}".format(date=datetime.datetime.now())
    return dt.format(aif_format)
