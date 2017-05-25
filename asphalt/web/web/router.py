import re
from collections import namedtuple
from typing import List, Dict, Iterable, Optional, Callable, Union, Tuple, Pattern  # noqa

from typeguard import check_argument_types

from asphalt.web.api import AbstractEndpoint, Router
from asphalt.web.endpoint import HTTPEndpoint
from asphalt.exceptions import RoutingError

Route = namedtuple('Route', ['regex', 'endpoint', 'methods'])


class URLDispatchRouter(Router):
    """Base implementation of AbstractRouter."""

    __slots__ = ('endpoints', 'path', 'subrouters')

    def __init__(self, path):
        self.register_path(path)
        self.subrouters = []  # type: List[Router]
        self.endpoints = {}  # type: Dict[str, HTTPEndpoint]

    def delete(self, fn) -> None:
        self.add_endpoint('DELETE', fn)

    def get(self, fn) -> None:
        self.add_endpoint('GET', fn)

    def head(self, fn) -> None:
        self.add_endpoint('HEAD', fn)

    def options(self, fn) -> None:
        self.add_endpoint('OPTIONS', fn)

    def patch(self, fn) -> None:
        self.add_endpoint('PATCH', fn)

    def post(self, fn) -> None:
        self.add_endpoint('POST', fn)

    def put(self, fn) -> None:
        self.add_endpoint('PUT', fn)

    def trace(self, fn) -> None:
        self.add_endpoint('TRACE', fn)

    def add_subrouter(self, router: Router, prefix: str = None):
        """
        Add a sub-router to the hierarchy.

        :param router: the router to add
        :param prefix: a value for the implementation specific path scheme

        """
        assert check_argument_types()
        self.routers.append(router)

    def register_path(self, path: str) -> None:
        """
        Register a compiled regex path for this router
        """
        assert check_argument_types()

        if not path.startswith('/'):
            path = '/' + path

        self.compiled_path = re.compile('^' + path.replace('.', '\\.') + '$')

    def add_endpoint(self, method: str, func: Callable) -> None:   # return type is TBD (D)
        """
        Map an http method to a function

        :param method: supported HTTP method
        :param func: the endpoint function
        """
        assert check_argument_types()

        if self.endpoints[method]:
            msg = "Router misconfigured:  unique-endpoint-per-method constraint violated."
            raise RoutingError(msg)

        self.endpoints[method] = HTTPEndpoint(func, self.path)

    def resolve(self, method: str) -> Optional[AbstractEndpoint]:  # Optional? (D)
        assert check_argument_types()
        try:
            return self.endpoints[method.upper()]
        except KeyError:
            msg = "Could not resolve {0} endpoint for path: {1}".\
                format(method, self.compiled_path.pattern)
            raise RoutingError(msg)

    # def resolve(self, request: HTTPRequest, path: PurePath) -> Optional[WebEndpoint]:
    #     assert check_argument_types()
    #     for endpoint in self.endpoints:
    #         match = endpoint.match(parts)
    #         if match:
    #             return match
    #
    #     for router in self.routers:
    #         match = router.resolve(request, parts)
    #         if match:
    #             return match
