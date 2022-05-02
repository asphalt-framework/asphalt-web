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

    :param aiohttp.web_app.Application app: the application object
    :param dict site: keyword arguments passed to :class:`aiohttp.web_runner.TCPSite`
    """

    def __init__(
        self,
        components: dict[str, dict[str, Any] | None] = None,
        *,
        app: str | Application | None = None,
        site: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(components)

        self.app = resolve_reference(app) or Application()
        self.app.middlewares.append(asphalt_middleware)
        self.site_options = site or {}
        self.site_options.setdefault("port", 8000)

    @context_teardown
    async def start(self, ctx: Context) -> AsyncIterator[None]:
        ctx.add_resource(self.app)
        await super().start(ctx)
        runner = AppRunner(self.app)
        await runner.setup()
        site = TCPSite(runner, **self.site_options)
        await site.start()

        yield

        await runner.cleanup()
