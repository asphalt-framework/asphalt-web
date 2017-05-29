from abc import ABCMeta, abstractmethod
from typing import Optional, Awaitable, Callable
from uuid import UUID

from asphalt.core import Context
from asphalt.web.request import HTTPRequest
from asphalt.web.session import WebSession

HTTP_METHODS = frozenset(['HEAD', 'GET', 'POST', 'PUT', 'DELETE', 'OPTIONS', 'TRACE'])


class AbstractEndpoint(metaclass=ABCMeta):
    """
    The low-level request handler interface.

    An endpoint is an object that knows how to handle an HTTP request.
    """

    __slots__ = ('func', 'request', 'parent_ctx')

    def __init__(self, func: Callable, request: HTTPRequest, parent_ctx: Context):
        """
        :param func: the target callable (must accept at least one positional argument)

        """
        self.func = func
        self.request = request
        self.parent_ctx = parent_ctx

    @abstractmethod
    def begin_request(self) -> Optional[Awaitable]:
        """Begin handling the request."""

    def receive_body_data(self, data: bytes) -> None:
        """
        Receive request body data.

        The server calls this method when it has new body data to send to the endpoint.
        An empty bytestring signifies the end of the stream.

        :param data: bytes sent by the client
        """


class Router(metaclass=ABCMeta):
    """A router is an object that knows how to translate a URI to an endpoint."""

    __slots__ = ()

    @abstractmethod
    def resolve(self, method: str, path: str) -> Optional[AbstractEndpoint]:
        """
        Resolve the given path to an endpoint.

        :param method: the request method (``GET``, ``POST``, etc.) (``HEAD`` is substituted with
            ``GET``)
        :param path: the request path
        :return: an endpoint, or ``None`` if no matching endpoint was found
        """


class SessionStore(metaclass=ABCMeta):
    """Interface for storing sessions."""

    __slots__ = ()

    async def start(self, ctx: Context) -> None:
        """
        Allow the session store a chance to claim any resources it needs.

        :param ctx: the current context
        """

    @abstractmethod
    def load(self, session_id: UUID) -> Awaitable[Optional[WebSession]]:
        """
        Retrieve a session from the store.

        :param session_id: unique identifier of the session
        :return: an awaitable resolving to a session if it was found, ``None`` if not
        """

    @abstractmethod
    def save(self, session: WebSession) -> Awaitable[None]:
        """
        Persist the session in the store.

        Updates an existing record if possible.

        :param session: the session instance to persist
        :return: an awaitable that completes when the operation is complete
        """

    @abstractmethod
    def purge_expired_sessions(self) -> Awaitable[None]:
        """
        Remove all expired sessions from the store.

        :return: an awaitable that completes when the operation is complete
        """


class WebServer(metaclass=ABCMeta):
    """Interface for web servers."""

    @abstractmethod
    async def start(self, parent_ctx: Context) -> None:
        """
        Start the server.

        This method should claim all necessary resources and then start listening to incoming
        requests.

        :param parent_ctx: the parent context for any future request contexts
        """

    @abstractmethod
    async def shutdown(self) -> None:
        """
        Shut down the server.

        This method should first stop listening to new requests and then finish up all pending
        requests before returning.
        """
