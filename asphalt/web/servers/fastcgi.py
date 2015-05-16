from asyncio import Protocol, ReadTransport, WriteTransport, Task, get_event_loop, ensure_future
from functools import partial
from inspect import isawaitable
from pathlib import PurePath
from typing import Dict, Union
import logging

from asphalt.core import Context
from fcgiproto import FastCGIConnection, RequestAbortEvent, RequestBeginEvent, RequestDataEvent
from multidict import CIMultiDict

from asphalt.web.api import AbstractRouter
from asphalt.web.response import HTTPResponse
from asphalt.web.router import Router
from asphalt.web.servers.base import BaseWebServer

logger = logging.getLogger(__name__)


class FastCGIServer(BaseWebServer):
    """
    Serves HTTP requests using the FastCGI protocol.

    This requires a "front-end" web server with FastCGI support (nginx, Apache or similar) that is
    configured to forward requests to this "back-end" server.

    The following FastCGI parameters are recognized:

    * ``SERVER_PROTOCOL``
    * ``REQUEST_METHOD``
    * ``DOCUMENT_URI``
    * ``QUERY_STRING``
    * ``HTTPS``
    * ``REMOTE_ADDR``
    * ``CLIENT_CERTIFICATE`` (non-standard, specific to asphalt-web)

    All parameters except for ``HTTPS`` and ``CLIENT_CERTIFICATE`` are required.
    """

    async def start(self, parent_ctx: Context) -> None:
        await super().start(parent_ctx)
        loop = get_event_loop()
        factory = partial(FastCGIProtocol, parent_ctx, self.router)
        if self.socket_path:
            address = self.socket_path
            server = loop.create_unix_server(factory, self.socket_path, backlog=self.backlog)
        else:
            address = '%s:%d' % (self.host or '*', self.port)
            server = loop.create_server(factory, self.host, self.port, backlog=self.backlog)

        parent_ctx.finished.connect(partial(self.shutdown, server, address))
        logger.info('Started FastCGI server on %s', address)

    async def shutdown(self, server, address) -> None:
        await super().shutdown(server, address)
        logger.info('Shut down FastCGI server on %s', address)

    def create_protocol(self):
        protocol = FastCGIProtocol(self.parent_ctx, self.router)
        self.clients.add(protocol)
        return protocol


class FastCGIProtocol(Protocol):
    def __init__(self, parent_ctx: Context, router: AbstractRouter):
        self.parent_ctx = parent_ctx
        self.router = router
        self.transport = None  # type: Union[ReadTransport, WriteTransport]
        self.connection = FastCGIConnection(fcgi_values={'FCGI_MPXS_CONNS': '0'})
        self.endpoint = None  # type: WebEndpoint

    def connection_made(self, transport) -> None:
        self.transport = transport

    def data_received(self, data: bytes) -> None:
        events = self.connection.feed_data(data)
        for event in events:
            if isinstance(event, RequestBeginEvent):
                self.begin_request(event)
            elif isinstance(event, RequestDataEvent):
                self.endpoint.receive_body_data(event.data)
            elif isinstance(event, RequestAbortEvent):
                self.abort_request()

        self.transport.write(self.connection.data_to_send())

    def connection_lost(self, exc) -> None:
        self.abort_request()

    def begin_request(self, event: RequestBeginEvent) -> None:
        params = event.params
        headers = CIMultiDict((key[5:].title(), value) for key, value in params.items()
                              if key.startswith('HTTP_'))

        http_version = params['SERVER_PROTOCOL'][6:]
        method = params['REQUEST_METHOD']
        path = params['DOCUMENT_URI']
        query_string = params['QUERY_STRING']
        secure = 'HTTPS' in params
        peername = params['REMOTE_ADDR']
        peercert = params.get('CLIENT_CERTIFICATE')
        # request = BodyHTTPRequest(http_version, method, path, query_string, headers, secure,
        #                           peername, peercert=peercert)
        self.endpoint = self.router.resolve(path, method)
        retval = self.endpoint.begin_request(request, self)
        if isawaitable(retval):
            ensure_future(retval).add_done_callback(self._request_finished)
        else:
            self._request_finished(retval)

    def _request_finished(self, retval) -> None:
        pass

    def abort_request(self) -> None:
        self.transport.abort()

    async def wait_finish(self) -> None:
        """Wait until the request has finished."""


class FastCGIResponse(HTTPResponse):
    __slots__ = ('_request_id', '_connection', '_transport')

    def __init__(self, request_id, connection: FastCGIConnection, transport: WriteTransport):
        super().__init__(None)
        self._request_id = request_id
        self._connection = connection
        self._transport = transport

    def write(self, data: bytes) -> None:
        self._connection.send_data(self._request_id, data)
        self._transport.write(self._connection.data_to_send())

    def upgrade(self):
        raise NotImplementedError('FastCGI does not support protocol upgrades')
