from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import PlainTextResponse, Response

application = Starlette()


@application.route("/")
async def root(request: Request) -> Response:
    return PlainTextResponse("Hello, world!")
