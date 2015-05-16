import logging
from abc import ABCMeta, abstractmethod
from asyncio.transports import ReadTransport, WriteTransport
from pathlib import Path
from typing import Union, Sequence
from weakref import WeakSet

from asphalt.core import Context, resolve_reference
from multidict import CIMultiDict
from typeguard import check_argument_types

from asphalt.web.api import AbstractRouter


class BaseWebServer(metaclass=ABCMeta):
    """
    Abstract base class for all web servers.

    :param router: the router that will be used to resolve request paths to endpoints:

        * a :class:`~asphalt.web.api.WebRouter` instance
        * a ``module:varname`` reference to one
        * name of a :class:`~asphalt.web.api.WebRouter` resource
    :param host: host name or IP address of local interface (or a sequence of such) to bind to
        (``None`` = all interfaces)
    :param port: port to bind to
    :param socket_path: file system path of a UNIX socket to bind to (if set, ``host`` and
        ``port`` are ignored)
    """

    def __init__(self, router: Union[AbstractRouter, str], host: Union[str, Sequence[str]] = None,
                 port: int = 8888, socket_path: Union[str, Path] = None, backlog: int = 100,
                 external_host: str = None, external_port: int = None,
                 external_prefix: str = None):
        assert check_argument_types()
        self.router = resolve_reference(router)  # type: AbstractRouter
        self.host = host if isinstance(host, str) else tuple(host)
        self.port = port
        self.socket_path = str(socket_path) if socket_path else None
        self.backlog = backlog
        self.external_host = external_host
        self.external_port = external_port or port
        self.external_prefix = external_prefix
        self.parent_ctx = None  # type: Context
        self.clients = WeakSet()
        self.logger = logging.getLogger(self.__class__.__module__)

    @abstractmethod
    async def start(self, parent_ctx: Context) -> None:
        self.parent_ctx = parent_ctx
        if isinstance(self.router, str):
            self.router = await parent_ctx.request_resource(AbstractRouter, self.router)

    async def shutdown(self, server, address) -> None:
        # Stop accepting new connections
        server.close()
        await server.wait_closed()

        # Wait until the existing requests have been processed
        if self.clients:
            self.logger.info('Waiting for %d requests to finish', len(self.clients))
            for protocol in self.clients:
                await protocol.wait_finish()


class BaseHTTPClientConnection(metaclass=ABCMeta):
    def __init__(self, transport: Union[ReadTransport, WriteTransport], parent_ctx: Context,
                 router: AbstractRouter):
        self.transport = transport  # type: Union[ReadTransport, WriteTransport]
        self.parent_ctx = parent_ctx
        self.router = router

    @abstractmethod
    def send_headers(self, status: int, headers: CIMultiDict) -> None:
        pass

    @abstractmethod
    def write(self, data: bytes) -> None:
        """
        Send data to the client.

        :param data: bytes to send
        """

    @abstractmethod
    def upgrade(self) -> None:
        """
        Upgrade to a different protocol.

        :raises NotimplementedError: if the underlying protocol does not support upgrading.
        """

    @abstractmethod
    def finish_request(self) -> None:
        pass
