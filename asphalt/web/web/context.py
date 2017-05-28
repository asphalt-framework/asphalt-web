from datetime import datetime, timedelta
from numbers import Number
from pathlib import Path
from typing import Dict, Any, Optional, Union

from typeguard import check_argument_types

from asphalt.core.context import Context
from asphalt.serialization.api import Serializer
from asphalt.templating.api import TemplateRenderer
from asphalt.web.request import HTTPRequest
from asphalt.web.response import HTTPResponse
from asphalt.web.utils import encode_header_value


class HTTPRequestContext(Context):
    """
    Base context class for all HTTP requests.

    :ivar WebRequest request: the HTTP request object
    """

    def __init__(self, parent: Context, request: HTTPRequest):
        super().__init__(parent)
        self.request = request


class HTTPRequestResponseContext(HTTPRequestContext):
    """
    Context class for traditional HTTP requests.

    :ivar WebResponse response: the HTTP response object
    """

    def __init__(self, parent: Context, request: HTTPRequest):
        super().__init__(parent, request)
        self.response = HTTPResponse

    def render(self, template: str, vars: Dict[str, Any] = None, *, status: Optional[int] = None,
               content_type: str = 'text/html',
               renderer: Union[str, TemplateRenderer] = 'default') -> str:
        """
        Render a template to the response stream.

        :param template: name of the template file to render
        :param vars: variables passed to the template renderer
        :param status: optional HTTP status code to set
        :param content_type: value for the ``content-type`` header
        :param renderer: a template renderer instance or resource name

        """
        assert check_argument_types()
        if isinstance(renderer, str):
            renderer = getattr(self._ctx, renderer)
            assert isinstance(renderer, TemplateRenderer),\
                '"renderer" must refer to a TemplateRenderer'

        rendered = renderer.render(template, **vars)
        self.response.headers.setdefault('content-type', content_type)

        if status is not None:
            self.response.status = status

        return rendered

    def serialize(self, obj, serializer: Union[str, Serializer] = 'default', *,
                  status: Optional[int] = None) -> bytes:
        """
        Serialize an object to the response stream.

        :param obj: object to serialize
        :param serializer: a serializer instance or resource name
        :param status: optional HTTP status code to set

        """
        assert check_argument_types()
        if isinstance(serializer, str):
            serializer = getattr(self._ctx, serializer)
            assert isinstance(serializer, Serializer), '"serializer" must refer to a Serializer'

        serialized = serializer.serialize(obj)
        self.response.headers.setdefault('content-type', serializer.mimetype)

        if status is not None:
            self.response.status = status

        return serialized

    def set_header(self, name: str, value: Union[str, datetime, Number], **params):
        header_value = encode_header_value(value, params)
        self.response.headers[name] = header_value

    def add_header(self, name: str, value: Union[str, datetime, Number], **params):
        header_value = encode_header_value(value, params)
        self.response.headers.add(name, header_value)

    def set_cookie(self, name: str, value, *, domain: str = None, path: str = None,
                   max_age: Union[int, timedelta] = None, expires: datetime = None,
                   secure: bool = False, httponly: bool = False) -> None:
        """
        Set a cookie in the response headers.

        :param name: name of the cookie
        :param value: value for the cookie (converted to string if it's not one already)
        :param domain: the domain the cookie applies to
        :param path: the path the cookie applies to
        :param max_age: maximum age of this cookie (in seconds or as a timedelta)
        :param expires: expiration date of the cookie (must be timezone aware)
        :param secure: ``True`` if the cookie should only be sent across secure (HTTPS) connections
        :param httponly: ``True`` if the cookie should not be accessible from client-side scripts

        """
        assert check_argument_types()
        main_value = '%s="%s"' % (name, quote(value))
        self.add_header('set-cookie', main_value, domain=domain, path=path, maxAge=max_age,
                        expires=expires, secure=secure, httponly=httponly)

    def expire_cookie(self, name: str, *, domain: str = None, path: str = None):
        """
        Set the expiration date of a cookie to 1970-01-01, forcing the client to discard it.

        Shortcut for::

            ctx.response.set_cookie(NAME, '', domain=DOMAIN, path=PATH, \
                expires=datetime(1970, 1, 1))

        :param name: name of the cookie
        :param domain: the domain the cookie applies to
        :param path: the path the cookie applies to

        """
        self.set_cookie(name, '', domain=domain, path=path, expires=UNIX_EPOCH)

    def send_file(self, path: Union[Path, str], *, as_attachment: bool = True) -> Path:
        """
        Send a file to the client using the best available method.

        Shortcut for::

            ctx.response.set_header('content-disposition', 'attachment')
            return Path(PATH)

        :param path: absolute filesystem path to the file
        :param as_attachment: ``True`` to have the web browser prompt the user for an action
            regarding the file instead of attempting to display its contents in the browser window

        """
        assert check_argument_types()
        path = Path(path)
        disposition = 'attachment' if as_attachment else 'inline'
        self.set_header('content-disposition', disposition, filename=path.name)
        return path
