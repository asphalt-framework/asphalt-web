from __future__ import annotations

from collections.abc import AsyncIterator, Awaitable, Callable
from typing import Any

from aiohttp.web_app import Application
from aiohttp.web_middlewares import middleware
from aiohttp.web_request import Request
from aiohttp.web_response import Response
from aiohttp.web_runner import AppRunner, TCPSite
from asphalt.core import (
    ContainerComponent,
    Context,
    context_teardown,
    resolve_reference,
)


@middleware
async def asphalt_middleware(
    request: Request, handler: Callable[..., Awaitable]
) -> Response:
    async with Context() as ctx:
        ctx.add_resource(request, types=[Request])
        return await handler(request)


class AIOHTTPComponent(ContainerComponent):
    """
    A component that serves an aiohttp application.

    :param app: the application object, or a module:varname reference to one
    :param host: the IP address to bind to
    :param port: the port to bind to
    :param debug: whether to enable debug mode in an implicitly created application
        (default: the value of
        `__debug__ <https://docs.python.org/3/library/constants.html#debug__>`_;
        ignored if an application object is explicitly passed in)
    """

    def __init__(
        self,
        components: dict[str, dict[str, Any] | None] = None,
        *,
        app: Application | str | None = None,
        host: str = "127.0.0.1",
        port: int = 8000,
        debug: bool | None = None,
    ) -> None:
        super().__init__(components)

        debug = debug if isinstance(debug, bool) else __debug__
        self.app = resolve_reference(app) or Application(debug=debug)
        self.app.middlewares.append(asphalt_middleware)
        self.host = host
        self.port = port

    @context_teardown
    async def start(self, ctx: Context) -> AsyncIterator[None]:
        ctx.add_resource(self.app)
        await super().start(ctx)
        runner = AppRunner(self.app)
        await runner.setup()
        site = TCPSite(runner, host=self.host, port=self.port)
        await site.start()

        yield

        await runner.cleanup()
