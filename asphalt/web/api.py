from abc import ABCMeta, abstractmethod
from typing import Optional, Awaitable, Callable
from uuid import UUID

from asphalt.core import Context
from asphalt.web.request import HTTPRequest
from asphalt.web.session import WebSession

HTTP_METHODS = frozenset(['HEAD', 'GET', 'POST', 'PUT', 'DELETE', 'OPTIONS', 'TRACE'])


# class HTTPRequest:
#     """
#     Represents an HTTP request.
#
#     It should be noted that if the application is behind a reverse proxy such as nginx or Apache,
#     some of these values may not reflect their expected values.
#     This affects in particular the ``http_version``, ``peername`` and ``peercert`` attributes.
#     Special measures must be taken to retain the proper values through a reverse proxy connection.
#
#     :ivar str http_version: HTTP version (e.g. ``1.1`` or ``2``)
#     :ivar str method: HTTP method (e.g. ``GET``, ``POST``, etc.)
#     :ivar str path: request path (e.g. ``/some/resource/somewhere``)
#     :ivar str query: HTTP query string
#     :ivar str scheme: ``http`` or ``https`` depending on whether TLS was used to connect to the
#         server
#     :ivar str peername: IP address or UNIX socket path of the client
#     :ivar str peercert: the raw client certificate data if the client presented a certificate
#         .. seealso:: https://docs.python.org/3/library/ssl.html#ssl.SSLSocket.getpeercert
#     """
#
#     @property
#     @abstractmethod
#     def query(self) -> Dict[str, str]:
#         """Return a dictionary of query parameters."""
#
#     @property
#     @abstractmethod
#     def accept(self) -> HTTPAccept:
#         """
#         Return the parsed version of the ``accept`` header.
#
#         :return: an HTTPAccept instance, or ``None`` if the header was not present
#         """
#
#     @property
#     @abstractmethod
#     def accept_charset(self) -> HTTPAcceptCharset:
#         """
#         Return the parsed version of the ``accept-charset`` header.
#
#         :return: an HTTPAcceptCharset instance, or ``None`` if the header was not present
#         """
#
#     @property
#     @abstractmethod
#     def accept_encoding(self) -> HTTPAcceptEncoding:
#         """
#         Return the parsed version of the ``accept-encoding`` header.
#
#         :return: an HTTPAcceptEncoding instance, or ``None`` if the header was not present
#         """
#
#     @property
#     @abstractmethod
#     def accept_language(self) -> HTTPAcceptLanguage:
#         """
#         Return the parsed version of the ``accept-language`` header.
#
#         :return: an HTTPAcceptLanguage instance, or ``None`` if the header was not present
#         """
#
#     @property
#     @abstractmethod
#     def charset(self) -> Optional[str]:
#         """
#         Return the character set of the request.
#
#         The character set is parsed from the of the ``content-type`` header, if present.
#
#         :return: the character set of the request, or ``None`` if none was defined
#         """
#
#     @property
#     @abstractmethod
#     def content_length(self) -> Optional[int]:
#         """
#         Return the content length of the request.
#
#         :return: the content length, or ``None`` if the header was not present
#         """
#
#     @property
#     @abstractmethod
#     def content_type(self) -> Optional[str]:
#         """
#         Return the content type of the request, or ``None`` if none was defined.
#
#         :return:
#         """
#
#     @property
#     @abstractmethod
#     def cookies(self) -> Dict[str, str]:
#         """Return a read-only dictionary containing cookie values sent by the client."""
#
#     @property
#     @abstractmethod
#     def if_modified_since(self) -> Optional[datetime]:
#         """
#         Return the ``if-modified-since`` header as a timezone aware datetime.
#
#         :return: the header's value as a datetime, or ``None`` if the header was not present
#         """
#
#     @property
#     @abstractmethod
#     def if_range(self) -> Optional[HTTPRange]:
#         """
#         Return the ``if-range`` header as a :class:`~HTTPRange` instance
#
#         :return: the header's value as HTTPRange, or ``None`` if the header was not present
#         """
#
#     @property
#     @abstractmethod
#     def if_unmodified_since(self) -> Optional[datetime]:
#         """
#         Return the ``if-unmodified-since`` header as a timezone aware datetime.
#
#         :return: the header's value as a datetime, or ``None`` if the header was not present
#         """
#
#     @property
#     @abstractmethod
#     def is_xhr(self) -> bool:
#         """
#         Return ``True`` if the request was made with XMLHttpRequest, ``False`` otherwise.
#
#         This only works if the ``x-requested-with: XMLHttpRequest`` header was set.
#         Several popular ECMAScript libraries do this but it is purely voluntary.
#         As such, this is not a 100% reliable method of detecting such requests.
#         """
#
#     @property
#     @abstractmethod
#     def max_forwards(self) -> Optional[int]:
#         """
#         Return the ``max_forwards`` header as an integer.
#
#         :return: the header's value as an integer, or ``None`` if the header was not present
#         """
#
#
# class HTTPResponse(metaclass=ABCMeta):
#     """
#     Contains response status, headers and other related data and provides convenient shortcuts
#     for often needed
#
#     Do **NOT** instantiate this class yourself!
#
#     :ivar int status: HTTP status code (default = 200)
#     :ivar multidict.CIMultiDict headers: response headers
#     :ivar str charset: character set to use for encoding a unicode response body (default = utf-8)
#     :ivar str content_type: content type to set on the response (default = determine from the
#         return value)
#     """
#
#     __slots__ = ()
#
#     @abstractmethod
#     def set_header(self, name: str, value: str, **params) -> None:
#         """
#         Set the value of a header, overwriting any previous value.
#
#         :param name: name of the header
#         :param value: value of the header
#         :param params: any parameters appended to the value (e.g. ``; key=value``)
#         """
#
#     @abstractmethod
#     def add_header(self, name: str, value: str, **params) -> None:
#         """
#         Add a header to the response.
#
#         If the header does not exist, this method works identically to :meth:`set_header`.
#         If, however, the header already exists in the response, it will have multiple values
#         (the header is emitted once for every value added).
#
#         :param name: name of the header
#         :param value: value of the header
#         :param params: any parameters appended to the value (e.g. ``; key=value``)
#         """
#
#     @abstractmethod
#     def set_cookie(self, name: str, value, *, domain: str = None, path: str = None,
#                    max_age: Union[int, timedelta] = None, expires: datetime = None,
#                    secure: bool = False, httponly: bool = False) -> None:
#         """
#         Set a cookie in the response headers.
#
#         :param name: name of the cookie
#         :param value: value for the cookie (converted to string if it's not one already)
#         :param domain: the domain the cookie applies to
#         :param path: the path the cookie applies to
#         :param max_age: maximum age of this cookie (in seconds or as a timedelta)
#         :param expires: expiration date of the cookie (must be timezone aware)
#         :param secure: ``True`` if the cookie should only be sent across secure (HTTPS) connections
#         :param httponly: ``True`` if the cookie should not be accessible from client-side scripts
#         """
#
#     @abstractmethod
#     def expire_cookie(self, name: str, *, domain: str = None, path: str = None):
#         """
#         Set the expiration date of a cookie to 1970-01-01, forcing the client to discard it.
#
#         Shortcut for::
#
#             ctx.response.set_cookie(NAME, '', domain=DOMAIN, path=PATH, \
#                 expires=datetime(1970, 1, 1))
#
#         :param name: name of the cookie
#         :param domain: the domain the cookie applies to
#         :param path: the path the cookie applies to
#         """
#
#     @abstractmethod
#     def send_file(self, path: Union[Path, str], *, as_attachment: bool = True) -> Path:
#         """
#         Send a file to the client using the best available method.
#
#         Shortcut for::
#
#             ctx.response.set_header('content-disposition', 'attachment')
#             return Path(PATH)
#
#         :param path: absolute filesystem path to the file
#         :param as_attachment: ``True`` to have the web browser prompt the user for an action
#             regarding the file instead of attempting to display its contents in the browser window
#
#         """


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
