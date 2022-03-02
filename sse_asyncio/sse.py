import asyncio
from asyncio import Queue, create_task
from dataclasses import dataclass
import json
import logging
import typing as t

import aioredis

from sse_asyncio.events import EVENT_CLASSES, UserUpdate

if t.TYPE_CHECKING:
    from asyncio import Task
    from starlette.requests import Request


redis = aioredis.Redis.from_url(
    "redis://localhost", max_connections=10, decode_responses=True
)


class EventQueue(Queue):
    def __init__(self, maxsize: int = 0, *, id, **kwargs) -> None:
        super().__init__(maxsize=maxsize, **kwargs)
        self.id = id


async def sse_generator(request: "Request"):
    closed_by_client = False
    client_id = request.client.port
    logger_ = logging.getLogger(__name__ + f" [{client_id}]")

    own_queue = EventQueue(id=client_id)

    async def _subscribe(request: "Request", subscriber: "EventQueue"):
        async with redis.pubsub() as pubsub:
            for event_class in EVENT_CLASSES:
                await pubsub.subscribe(event_class.__name__)

            while True:
                if await request.is_disconnected():
                    break

                redis_message: dict = await pubsub.get_message(
                    ignore_subscribe_messages=True
                )
                if redis_message is None:
                    await asyncio.sleep(0.01)
                    continue
                event = UserUpdate.from_json(redis_message["data"])
                await subscriber.put(event)

    create_task(_subscribe(request=request, subscriber=own_queue))

    while True:
        if await request.is_disconnected():
            closed_by_client = False
            break

        event_: UserUpdate = await own_queue.get()
        if not event_:
            logger_.warning("Got None as event, skipping")
            continue
        event = Event(event=event_.event, id=event_.id, data=event_.data)

        logger_.info(f"Sending event: {event!r}")
        yield event.to_json()

    if closed_by_client:
        logger_.info("Connection closed by client")


@dataclass
class Event:
    event: str
    data: dict
    id: t.Optional[str]

    def __str__(self) -> str:
        event_line = f"event: {self.event}"
        data_line = f"data: {json.dumps(self.data)}"
        id_line = f"id: {self.id}" if self.id else ""
        return "\n".join([event_line, data_line, id_line]) + "\n"

    def to_json(self) -> dict:
        event_json = {
            "event": self.event,
            "data": json.dumps(self.data),
        }
        if self.id:
            event_json["id"] = self.id
        return event_json
