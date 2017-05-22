import logging
import ssl
from asyncio import Task, Protocol, get_event_loop
from functools import partial
from ssl import SSLContext
from typing import Dict, Optional, Union

import h11
from asphalt.core import Context, resolve_reference
from h2.connection import H2Connection
from multidict import CIMultiDict
from typeguard import check_argument_types

from asphalt.web.api import Router
from asphalt.web.request import HTTPRequest
from asphalt.web.servers.base import BaseWebServer, BaseHTTPClientConnection

logger = logging.getLogger(__name__)


class HTTPServer(BaseWebServer):
    """
    Serves HTTP requests using HTTP/1.1 and/or HTTP/2.

    HTTP/2 support is only available if SSL is enabled and ALPN support is available
    (``ssl.HAS_ALPN`` is ``True``). If a custom SSL context is passed, its list of ALPN protocols
    is overridden to only accept the ``h2`` protocol.

    Websocket support is not available for HTTP/2 connections as HTTP/2 currently lacks a mechanism
    to do a protocol upgrade.

    Server push for HTTP/2 has not been implemented yet.

    :param ssl: one of the following:

        * ``False`` to disable SSL
        * ``True`` to enable SSL using the default context
        * an :class:`ssl.SSLContext` instance
        * a ``module:varname`` reference to an :class:`~ssl.SSLContext` instance
        * name of an :class:`ssl.SSLContext` resource
    :param http2: ``True`` = require HTTP/2 (implies ssl), ``False`` = disable HTTP/2,
        ``None`` = use HTTP/2 when possible
    :param kwargs: keyword arguments passed to :class:`~asphalt.web.servers.base.BaseWebServer`
    """

    def __init__(self, ssl: Union[bool, str, SSLContext] = False, http2: bool = None, **kwargs):
        super().__init__(**kwargs)
        assert check_argument_types()
        self.ssl = resolve_reference(ssl) or bool(http2)
        self.http2 = http2

    async def start(self, parent_ctx: Context) -> None:
        await super().start(parent_ctx)
        if self.ssl:
            if isinstance(self.ssl, str):
                self.ssl = await parent_ctx.request_resource(SSLContext, self.ssl)
            elif isinstance(self.ssl, bool):
                self.ssl = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)

            # Enable HTTP/2
            if ssl.HAS_ALPN:
                if self.http2 in (True, None):
                    self.ssl.set_alpn_protocols(['h2'])
            elif self.http2:
                raise Exception('HTTP/2 is required but ALPN support is not available')

        loop = get_event_loop()
        if self.socket_path:
            address = self.socket_path
            server = loop.create_unix_server(self.create_protocol, self.socket_path,
                                             backlog=self.backlog, ssl=self.ssl)
        else:
            address = '%s:%d' % (self.host or '*', self.port)
            server = loop.create_server(self.create_protocol, self.host, self.port,
                                        backlog=self.backlog, ssl=self.ssl)

        parent_ctx.finished.connect(partial(self.shutdown, server, address))
        http_2_enabled = self.ssl and 'h2' in self.ssl.get_alpn_protocols()
        logger.info('Started HTTP server on %s (HTTP/2: %s)', address,
                    'enabled' if http_2_enabled else 'disabled')

    async def shutdown(self, server, address) -> None:
        # Stop accepting new connections
        server.close()
        await server.wait_closed()

        # Wait until the existing requests have been processed
        if self.clients:
            logger.info('Waiting for %d requests to finish', len(self.clients))
            for protocol in self.clients:
                await protocol.wait_finish()

        logger.info('Shut down HTTP server on %s', address)

    def create_protocol(self):
        protocol = HTTPProtocol(self.parent_ctx, self.router)
        self.clients.add(protocol)
        return protocol


class HTTPProtocol(Protocol):
    def __init__(self, parent_ctx: Context, router: Router):
        self.parent_ctx = parent_ctx
        self.router = router
        self.connection = None  # type: BaseHTTPClientConnection

    def connection_made(self, transport):
        ssl_object = transport.get_extra_info('ssl_object')
        if ssl_object and ssl_object.selected_alpn_protocol() == 'h2':
            self.connection = HTTP2ConnectionWrapper(transport, self.parent_ctx, self.router)
        else:
            self.connection = HTTP1ConnectionWrapper(transport, self.parent_ctx, self.router)

    def data_received(self, data: bytes) -> None:
        self.connection.data_received(data)

    def eof_received(self):
        self.connection.eof_received()

    def connection_lost(self, exc):
        self.connection.connection_lost(exc)

    def pause_writing(self):
        super().pause_writing()

    def resume_writing(self):
        super().resume_writing()


class HTTP1ConnectionWrapper(BaseHTTPClientConnection):
    def __init__(self, parent_ctx: Context, transport, router: Router):
        super().__init__(transport, parent_ctx, router)
        self.connection = h11.Connection(h11.SERVER)
        self.request = None  # type: HTTPRequest
        self.task = None  # type: Task

    def data_received(self, data: bytes) -> None:
        self.connection.receive_data(data)
        while True:
            event = self.connection.next_event()
            if event is h11.NEED_DATA:
                return
            elif isinstance(event, h11.Request):
                self.begin_request(event.headers)
            elif isinstance(event, h11.Data):
                request = self.requests[len(self.requests) - 1]
                request.body.feed_data(event.data)
            elif isinstance(event, h11.EndOfMessage):
                request = self.requests[len(self.requests) - 1]
                request.body.feed_eof()

    def eof_received(self) -> None:
        self.connection.send(h11.ConnectionClosed())

    def connection_lost(self, exc: Optional[Exception]) -> None:
        if self.request_task and not self.request_task.done():
            self.request_task.cancel()

    def begin_request(self, event):
        headers = CIMultiDict((decode_ascii(key)[0], decode_latin1(value))
                              for key, value in event.headers)
        self.request = HTTPRequest(
            event.http_version.decode('ascii'), event.method.decode('ascii'),
            event.target.decode('ascii'), headers)
        coro = self.root.begin_request(self.parent_ctx, self.request)
        self.request_task = get_event_loop().create_task(coro)

    def send_headers(self, stream_id: Optional[int], status: int, headers: CIMultiDict) -> None:
        event = h11.Response(status_code=status, headers=headers)
        payload = self.connection.send(event)
        self.transport.write(payload)

    def send_data(self, stream_id: Optional[int], data: bytes) -> None:
        event = h11.Data(data=data)
        payload = self.connection.send(event)
        self.transport.write(payload)

    def finish_request(self, stream_id: Optional[int]) -> None:
        event = h11.EndOfMessage()
        payload = self.connection.send(event)
        self.transport.write(payload)
        self.connection.start_next_cycle()


class HTTP2ConnectionWrapper(BaseHTTPClientConnection):
    def __init__(self, parent_ctx: Context, transport, router: Router):
        super().__init__(transport, parent_ctx, router)
        self.requests = {}  # type: Dict[int, HTTPRequest]
        self.tasks = {}  # type: Dict[int, Task]
        connection = H2Connection(client_side=False)
        connection.initiate_connection()
        transport.send_message(connection.data_to_send())

    def data_received(self, data: bytes) -> None:
        events = self.connection.receive_data(data)
        for event in events:
            if isinstance(event, RequestReceived):
                self.begin_request(event.stream_id, event.headers)
            elif isinstance(event, DataReceived):
                request = self.requests[event.stream_id]
                request.body.feed_data(event.data)
            elif isinstance(event, StreamEnded):
                request = self.requests[len(self.requests) - 1]
                request.body.feed_eof()

        self.transport.send_message(self.connection.data_to_send())

    def connection_lost(self, exc: Optional[Exception]) -> None:
        # Cancel all unfinished tasks for this connection
        if isinstance(self.connection, h11.Connection):
            tasks = [task for request, task in self.requests if not task.done()]
        else:
            tasks = [task for request, task in self.requests.values() if not task.done()]

        for task in tasks:
            task.cancel()

    def begin_request(self, stream_id: int, headers: Iterable[Tuple[bytes, bytes]]) -> None:
        headers = CIMultiDict((decode_ascii(key)[0], decode_ascii(value)[0])
                              for key, value in headers)
        request = HTTPRequest(
            headers[':scheme'].split('/')[1], headers[':method'], headers[':path'],
            headers)
        coro = self.root.begin_request(self.parent_ctx, request)
        self.tasks[stream_id] = get_event_loop().create_task(coro)
        self.requests[stream_id] = request

    def finish_request(self, stream_id: Optional[int]) -> None:
        self.connection.end_stream(stream_id)
        payload = self.connection.data_to_send()
        self.transport.send_message(payload)

    def send_headers(self, stream_id: Optional[int], status: int, headers: CIMultiDict) -> None:
        self.connection.send_headers(stream_id, headers)
        payload = self.connection.data_to_send()
        self.transport.send_message(payload)

    def send_data(self, stream_id: Optional[int], data: bytes) -> None:
        self.connection.send_data(stream_id, data)
        payload = self.connection.data_to_send()
        self.transport.send_message(payload)
