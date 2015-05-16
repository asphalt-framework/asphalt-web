from asyncio import ensure_future
from inspect import isawaitable

from asphalt.web.api import AbstractEndpoint
from asphalt.web.context import HTTPRequestResponseContext


class HTTPEndpoint(AbstractEndpoint):
    """Handler for traditional HTTP endpoints."""

    __slots__ = ()

    def begin_request(self):
        ctx = HTTPRequestResponseContext(self.parent_ctx, self.request)
        try:
            retval = self.func(ctx)
            if isawaitable(retval):
                ensure_future(retval).add_done_callback(self.process_return_value)
        except Exception as e:
            pass

    def receive_body_data(self, data: bytes) -> None:
        self.request.body.feed_data(data)

    def process_return_value(self, retval):
        pass
