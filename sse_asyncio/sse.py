import asyncio
from dataclasses import dataclass
import json
import typing as t

if t.TYPE_CHECKING:
    from starlette.requests import Request


async def sse_generator(request: "Request"):
    i = 0
    closed_by_client = False
    while True:
        if await request.is_disconnected():
            closed_by_client = False
            break

        data: dict = {
            "id": f"some-data-{i}",
        }
        event = (
            "event: some-event\n"
            f"data: {json.dumps(data)}\n"
            f"id: some-event-{i}\n"
            "\n"
        )
        event = Event(event="some-event", data=data, id=f"some-event-{i}")
        print(f"Sending event: {event!r}")
        yield event
        i += 1
        await asyncio.sleep(1)

    if closed_by_client:
        print("Connection closed by client")


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