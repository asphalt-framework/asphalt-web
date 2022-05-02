from aiohttp.abc import Request
from aiohttp.web_app import Application
from aiohttp.web_response import Response
from aiohttp.web_routedef import RouteTableDef

routes = RouteTableDef()


@routes.get("/")
async def root(request: Request) -> Response:
    return Response(text="Hello, world!")


application = Application()
application.add_routes(routes)
