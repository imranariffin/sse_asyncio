import logging
from os import environ
import typing as t

from sse_starlette import EventSourceResponse

from starlette.applications import Starlette
from starlette.templating import Jinja2Templates
from starlette.responses import JSONResponse
from starlette.routing import Route

from tortoise import Tortoise

from sse_asyncio.sse import sse_generator
from sse_asyncio.models import User

if t.TYPE_CHECKING:
    from starlette.requests import Request

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

templates = Jinja2Templates(directory='templates', auto_reload=True)


async def homepage(request: "Request"):
    return templates.TemplateResponse("index.html", {"request": request})


async def sse(request: "Request"):
    content_generator = sse_generator(request=request)
    response = EventSourceResponse(content=content_generator)
    return response


async def users_chart(request: "Request"):
    users = User.all()
    chart = {
        "categories": [
            {
                "key": "id",
                "value": "ID",
            },
            {
                "key": "name",
                "value": "Name",
            },
        ],
        "rows": [],
    }
    async for user in users:
        user_row = {}
        for category in chart["categories"]:
            category_key = category["key"]
            user_row[category_key] = getattr(user, category_key)
        rows: list[dict] = chart["rows"]
        rows.append(user_row)
    return JSONResponse(content=chart)


async def on_startup_task():
    logger.info("[%s] Connecting to database", on_startup_task.__qualname__)
    await Tortoise.init(
        db_url=environ["DATABASE_URL"],
        modules={
            "models": [
                "sse_asyncio.models",
            ],
        },
    )
    logger.info("Generating schemas")
    await Tortoise.generate_schemas()


app = Starlette(
    debug=True, 
    routes=[
        Route('/', homepage),
        Route("/sse", sse),
        Route("/users/chart", users_chart),
    ],
    on_startup=[on_startup_task],
)
