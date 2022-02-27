from abc import ABCMeta
from dataclasses import dataclass
import logging
import typing as t

logger = logging.getLogger(__name__)


@dataclass
class BaseSSEvent(metaclass=ABCMeta):
    """
    Define the properties of a base Server-Sent Event.
    """
    event: str
    data: dict
    id: t.Optional[str]


class UserUpdate(BaseSSEvent):
    """Emit this when any field of a user table has been updated."""


EVENT_QUEUES = {
    UserUpdate.__name__: [],
}
