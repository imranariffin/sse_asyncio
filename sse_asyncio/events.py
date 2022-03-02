from abc import ABCMeta
from dataclasses import dataclass
from enum import Enum
import json
import logging
import typing as t

import aioredis

logger = logging.getLogger(__name__)


@dataclass
class BaseSSEvent(metaclass=ABCMeta):
    """
    Define the properties of a base Server-Sent Event.
    """

    event: str
    data: dict
    id: t.Optional[str]

    def to_json(self):
        return json.dumps(self.__dict__)

    @classmethod
    def from_json(cls, json_str: str) -> "BaseSSEvent":
        d = json.loads(json_str)
        return cls(**d)


class UserUpdate(BaseSSEvent):
    """Emit this when any field of a user table has been updated."""


EVENT_CLASSES = [
    UserUpdate,
]


_publisher = aioredis.Redis.from_url(
    "redis://localhost", max_connections=10, decode_responses=True
)


async def publish(event: BaseSSEvent) -> None:
    channel = event.__class__.__name__
    logger.info("Publishing event %s to channel %s", event, channel)
    await _publisher.publish(channel=channel, message=event.to_json())
