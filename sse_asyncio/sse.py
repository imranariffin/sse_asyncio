from asyncio import Queue, create_task
from dataclasses import dataclass
import json
import logging
import typing as t

from sse_asyncio.events import EVENT_QUEUES, UserUpdate

if t.TYPE_CHECKING:
    from asyncio import Task
    from starlette.requests import Request  


class EventQueue(Queue):
    def __init__(self, maxsize: int = 0, *, id, **kwargs) -> None:
        super().__init__(maxsize=maxsize, **kwargs)
        self.id = id


async def sse_generator(request: "Request"):
    closed_by_client = False
    client_id = request.client.port
    logger_ = logging.getLogger(__name__ + f" [{client_id}]")

    own_queue = EventQueue(id=client_id)
    EVENT_QUEUES[UserUpdate.__name__].append(own_queue)

    async def _subscribe(request: "Request", subscriber: "EventQueue", publisher: "EventQueue"):
        while True:
            if await request.is_disconnected():
                break

            event = await publisher.get()
            await subscriber.put(event)
            logger_.info("Queue %s published event %s to queue %s", publisher.id, event, subscriber.id)


    subscriptions: list["Task"] = []
    for queue in EVENT_QUEUES[UserUpdate.__name__]:
        if queue == own_queue:
            continue
        subscription = create_task(_subscribe(request=request, subscriber=own_queue, publisher=queue))
        subscriptions.append(subscription)
        reverse_subscription = create_task(_subscribe(request=request, subscriber=queue, publisher=own_queue))
        subscriptions.append(reverse_subscription)


    while True:
        if await request.is_disconnected():
            closed_by_client = False
            for subscription in subscriptions:
                subscription.cancel()
                await subscription
            break

        event_: UserUpdate = await own_queue.get()
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