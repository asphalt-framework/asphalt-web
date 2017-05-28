import logging
from asyncio import (
    start_unix_server, start_server, StreamReader,
    StreamWriter)
from ssl import SSLContext
from typing import Union
from urllib.parse import urlparse, unquote

import h11
from multidict import CIMultiDict
from typeguard import check_argument_types

from asphalt.core import Context
from asphalt.web.request import HTTPRequest
from asphalt.web.servers.base import BaseWebServer

logger = logging.getLogger(__name__)


class HTTPServer(BaseWebServer):
    """
    Serves HTTP requests using HTTP/1.1.

    TLS support can be enabled by passing ``tls_context`` equipped with a key and certificate.

    :param tls_context: an :class:`~ssl.SSLContext` instance or the resource name of one
    :param kwargs: keyword arguments passed to :class:`~asphalt.web.servers.base.BaseWebServer`
    """

    def __init__(self, tls_context: Union[SSLContext, str] = None, **kwargs):
        super().__init__(**kwargs)
        assert check_argument_types()
        self.tls_context = tls_context
        self._server = None

    async def start(self, parent_ctx: Context) -> None:
        await super().start(parent_ctx)
        if isinstance(self.tls_context, str):
            self.tls_context = await parent_ctx.request_resource(SSLContext, self.tls_context)

        if self.socket_path:
            self._server = start_unix_server(
                self.handle_client, self.socket_path, backlog=self.backlog, ssl=self.tls_context)
        else:
            self._server = start_server(
                self.handle_client, self.host, self.port, backlog=self.backlog,
                ssl=self.tls_context)

    async def shutdown(self) -> None:
        # Stop accepting new connections
        self._server.close()
        await self._server.wait_closed()

        # Wait until the existing requests have been processed
        if self.clients:
            logger.info('Waiting for %d requests to finish', len(self.clients))
            for protocol in self.clients:
                await protocol.wait_finish()

    async def handle_client(self, reader: StreamReader, writer: StreamWriter) -> None:
        connection = h11.Connection(h11.SERVER)
        body = None  # type: StreamReader
        while True:
            data = await reader.read(65536)
            connection.receive_data(data)
            event = connection.next_event()
            if event is h11.NEED_DATA:
                continue
            elif isinstance(event, h11.Request):
                headers = CIMultiDict((key.decode('ascii'), value.decode('iso-8859-1'))
                                      for key, value in event.headers)
                peername = writer.get_extra_info('peername')
                peercert = writer.get_extra_info('peercert')
                parsed = urlparse(event.target, allow_fragments=False)
                query = unquote(parsed.query.decode('ascii'))
                request = HTTPRequest(
                    event.http_version.decode('ascii'), event.method.decode('ascii'),
                    parsed.path.decode('utf-8'), query, headers, body, bool(self.tls_context),
                    peername, peercert)
            elif isinstance(event, h11.Data):
                body.feed_data(event.data)
            elif isinstance(event, h11.EndOfMessage):
                body.feed_eof()
