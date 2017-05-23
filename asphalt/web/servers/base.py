import logging
from abc import ABCMeta, abstractmethod
from asyncio.transports import ReadTransport, WriteTransport
from pathlib import Path
from typing import Union, Sequence

from asphalt.core import Context, resolve_reference
from multidict import CIMultiDict
from typeguard import check_argument_types

from asphalt.web.api import Router, WebServer


class BaseWebServer(WebServer):
    """
    Base implementation for web servers.

    :param router: the router that will be used to resolve request paths to endpoints:

        * a :class:`~asphalt.web.api.Router` instance
        * a ``module:varname`` reference to one
        * name of a :class:`~asphalt.web.api.Router` resource
    :param host: host name or IP address of local interface (or a sequence of such) to bind to
        (``None`` = all interfaces)
    :param port: port to bind to
    :param socket_path: file system path of a UNIX socket to bind to (if set, ``host`` and
        ``port`` are ignored)
    """

    def __init__(self, router: Union[Router, str], host: Union[str, Sequence[str]] = None,
                 port: int = 8888, socket_path: Union[str, Path] = None, backlog: int = 100,
                 external_host: str = None, external_port: int = None,
                 external_prefix: str = None):
        assert check_argument_types()
        self.router = resolve_reference(router)  # type: Router
        self.host = host if isinstance(host, str) else tuple(host)
        self.port = port
        self.socket_path = str(socket_path) if socket_path else None
        self.backlog = backlog
        self.external_host = external_host
        self.external_port = external_port or port
        self.external_prefix = external_prefix
        self.parent_ctx = None  # type: Context
        self.clients = set()
        self.logger = logging.getLogger(self.__class__.__module__)

    @abstractmethod
    async def start(self, parent_ctx: Context) -> None:
        self.parent_ctx = parent_ctx

        if isinstance(self.router, str):
            self.router = await parent_ctx.request_resource(Router, self.router)


class BaseHTTPClientConnection(metaclass=ABCMeta):
    def __init__(self, transport: Union[ReadTransport, WriteTransport], parent_ctx: Context,
                 router: Router):
        self.transport = transport  # type: Union[ReadTransport, WriteTransport]
        self.parent_ctx = parent_ctx
        self.router = router

    @abstractmethod
    async def send_headers(self, status: int, headers: CIMultiDict) -> None:
        pass

    @abstractmethod
    async def write(self, data: bytes) -> None:
        """
        Send data to the client.

        :param data: bytes to send
        """

    @abstractmethod
    def upgrade(self) -> None:
        """
        Upgrade to a different protocol.

        :raises NotimplementedError: if the underlying protocol does not support upgrading
        """

    @abstractmethod
    def finish_request(self) -> None:
        pass
