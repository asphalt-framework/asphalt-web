from __future__ import annotations

from asyncio import create_task, sleep
from dataclasses import dataclass
from typing import Any, Dict, Generic, Optional, TypeVar

import uvicorn
from asgiref.typing import (
    ASGI3Application,
    ASGIReceiveCallable,
    ASGISendCallable,
    HTTPScope,
    Scope,
)
from asphalt.core import (
    ContainerComponent,
    Context,
    context_teardown,
    current_context,
    resolve_reference,
)
from uvicorn import Config

T_Application = TypeVar("T_Application", bound=ASGI3Application)


@dataclass
class AsphaltMiddleware:
    app: ASGI3Application

    async def __call__(
        self, scope: Scope, receive: ASGIReceiveCallable, send: ASGISendCallable
    ) -> None:
        if scope["type"] == "http":
            assert current_context() is not None
            async with Context() as ctx:
                ctx.add_resource(scope, types=[HTTPScope])
                await self.app(scope, receive, send)
        else:
            await self.app(scope, receive, send)


class ASGIComponent(ContainerComponent, Generic[T_Application]):
    def __init__(
        self,
        components: Dict[str, Optional[Dict[str, Any]]] = None,
        *,
        app: T_Application,
        host: str = "127.0.0.1",
        port: int = 8000,
    ) -> None:
        super().__init__(components)
        self.app: T_Application = resolve_reference(app)
        self.host = host
        self.port = port

    def wrap_in_middleware(self, app: T_Application) -> ASGI3Application:
        return AsphaltMiddleware(app)

    @context_teardown
    async def start(self, ctx: Context):
        config = Config(
            app=self.wrap_in_middleware(self.app),
            host=self.host,
            port=self.port,
            use_colors=False,
            log_config=None,
            lifespan="off",
        )
        server = uvicorn.Server(config)
        server.install_signal_handlers = lambda: None
        assert current_context() is ctx
        server_task = create_task(server.serve())
        while not server.started:
            await sleep(0)

        yield

        server.should_exit = True
        await server_task
