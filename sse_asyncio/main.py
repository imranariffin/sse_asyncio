from asyncio import create_task
import logging
from os import environ
import typing as t

from sse_starlette import EventSourceResponse

from starlette.applications import Starlette
from starlette.templating import Jinja2Templates
from starlette.responses import JSONResponse
from starlette.routing import Route

from tortoise import Tortoise

from sse_asyncio.events import UserUpdate, publish
from sse_asyncio.sse import sse_generator
from sse_asyncio.models import User

if t.TYPE_CHECKING:
    from starlette.requests import Request

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

templates = Jinja2Templates(directory="templates", auto_reload=True)


async def homepage(request: "Request"):
    return templates.TemplateResponse("index.html", {"request": request})


async def sse(request: "Request"):
    content_generator = sse_generator(request=request)
    response = EventSourceResponse(content=content_generator)
    return response


if environ["DEBUG"]:

    async def load_test_data(request: "Request"):
        assert request.method == "POST"
        user_names = {f"User {i}" for i in range(1, 200)}
        existing_user_names = set(
            await User.filter(name__in=user_names).values_list("name", flat=True)
        )
        new_user_names = user_names - existing_user_names
        r = await User.bulk_create(objects=(User(name=name) for name in new_user_names))
        return JSONResponse(content={"new_users": len(r)}, status_code=201)


async def update_user(request: "Request"):
    user_id = request.path_params["user_id"]
    body = await request.json()
    new_name = body["name"]
    await User.select_for_update().filter(id=user_id).update(name=new_name)
    event = UserUpdate(
        event="some-event",
        id=f"some-event-{user_id}",
        data={"id": f"{user_id}.name", "value": new_name},
    )
    await publish(event)
    return JSONResponse(content={"id": user_id, "name": new_name}, status_code=200)


async def users_chart(request: "Request"):
    users = User.all().order_by("name")
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


routes = [
    Route("/", homepage),
    Route("/sse", sse),
    Route("/users/chart", users_chart),
    Route("/users/{user_id:int}", update_user, methods=["PATCH"]),
]

if environ["DEBUG"]:
    routes.append(Route("/load-test-data", load_test_data, methods=["POST"]))


app = Starlette(
    debug=True,
    routes=routes,
    on_startup=[on_startup_task],
)
