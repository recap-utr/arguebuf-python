from __future__ import absolute_import, annotations

import datetime
import uuid


def ova_date() -> str:
    return "{date:%d/%m/%Y - %H:%M:%S}".format(date=datetime.datetime.now())


def aif_date() -> str:
    return "{date:%Y-%m-%d %H:%M:%S}".format(date=datetime.datetime.now())


def unique_id() -> int:
    return uuid.uuid1().int >> 64


def xstr(data: Any):
    return "" if data is None else str(data)
