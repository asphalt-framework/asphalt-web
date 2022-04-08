from __future__ import annotations

from asgiref.typing import ASGI3Application, HTTPScope
from asphalt.core import Context
from starlette.applications import Starlette
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

from asphalt.web.asgi import ASGIComponent


class AsphaltMiddleware(BaseHTTPMiddleware):
    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        async with Context() as ctx:
            ctx.add_resource(request.scope, types=[HTTPScope])
            ctx.add_resource(request)
            return await call_next(request)


class StarletteComponent(ASGIComponent[Starlette]):
    def wrap_in_middleware(self, app: Starlette) -> ASGI3Application:
        return AsphaltMiddleware(app)

    async def start(self, ctx: Context):
        ctx.add_resource(self.app, types=[ASGI3Application.__origin__, Starlette])
        await super().start(ctx)
