import typing as t

from sse_starlette import EventSourceResponse
from starlette.applications import Starlette
from starlette.templating import Jinja2Templates
from starlette.routing import Route

from sse_asyncio.sse import sse_generator

if t.TYPE_CHECKING:
    from starlette.requests import Request

templates = Jinja2Templates(directory='templates', auto_reload=True)


async def homepage(request: "Request"):
    return templates.TemplateResponse("index.html", {"request": request})


async def sse(request: "Request"):
    content_generator = sse_generator(request=request)
    response = EventSourceResponse(content=content_generator)
    return response


app = Starlette(
    debug=True, 
    routes=[
        Route('/', homepage),
        Route("/sse", sse),
    ],
)
