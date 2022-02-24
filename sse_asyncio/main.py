import asyncio
import json
import typing as t

from sse_starlette import EventSourceResponse
from starlette.applications import Starlette
from starlette.templating import Jinja2Templates
from starlette.responses import JSONResponse, StreamingResponse
from starlette.routing import Route

if t.TYPE_CHECKING:
    from starlette.requests import Request

templates = Jinja2Templates(directory='templates', auto_reload=True)


async def homepage(request: "Request"):
    return templates.TemplateResponse("index.html", {"request": request})


async def sse(request: "Request"):
    async def _generator():
        i = 0
        closed_by_client = False
        while True:
            if await request.is_disconnected():
                closed_by_client = False
                break

            # event = {"event": "some-event", "data": f"Some data: {i}"}
            data: dict = {
                "id": f"some-data-{i}",
            }
            event = (
                "event: some-event\n"
                f"data: {json.dumps(data)}\n"
                f"id: some-event-{i}\n"
                "\n"
            )
            print(f"Sending event: {event!r}")
            yield event
            i += 1
            await asyncio.sleep(1)

        if closed_by_client:
            print("Connection closed by client")

    response = EventSourceResponse(_generator())
    # response = StreamingResponse(
    #     content=_generator(), 
    #     headers={
    #         "Connection": "Keep-Alive",
    #         "Cache-Control": "no-cache",
    #     },
    #     media_type="text/event-stream",
    # )
    return response


app = Starlette(
    debug=True, 
    routes=[
        Route('/', homepage),
        Route("/sse", sse),
    ],
)
