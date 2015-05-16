import re
from collections import namedtuple
from functools import lru_cache
from typing import List, Dict, Iterable, Optional, Callable, Union, Tuple, Pattern

from typeguard import check_argument_types

from asphalt.web.api import AbstractEndpoint, AbstractRouter, HTTP_METHODS
from asphalt.web.endpoint import HTTPEndpoint

Route = namedtuple('Route', ['regex', 'endpoint', 'methods'])


class Router(AbstractRouter):
    """Base implementation of AbstractRouter."""

    __slots__ = ('routers', 'routes', 'named_routes')

    def __init__(self):
        self.routers = []  # type: List[AbstractRouter]
        self.routes = []  # type: List[Route]
        self.named_routes = {}  # type: Dict[str, AbstractEndpoint]

    def add_router(self, router: AbstractRouter, prefix: str = None):
        """
        Add a sub-router to the hierarchy.

        :param router: the router to add
        :param prefix: a value for the implementation specific path scheme

        """
        assert check_argument_types()
        self.routers.append(router)
        self.get_named_endpoint.cache_clear()

    def add_endpoint(self, endpoint: AbstractEndpoint, path: str,
                     methods: Union[str, Iterable[str]], name: str = None):
        """
        Add an endpoint to this router.

        :param endpoint:
        :param path:
        :param name: a unique name for this endpoint

        """
        assert check_argument_types()

        # Compile the path to a regular expression
        if not path.startswith('/'):
            path = '/' + path
        compiled_path = self.compile_path(path)

        # Validate the allowed HTTP methods
        if isinstance(methods, str):
            allowed_methods = [methods]
        else:
            allowed_methods = set(methods)
            allowed_methods = sorted(m.upper() for m in allowed_methods)

        for method in allowed_methods:
            if method not in HTTP_METHODS:
                raise ValueError('"{}" is not a known HTTP method'.format(method))

        # Register the unique name
        if name:
            if name in self.named_routes:
                raise ValueError('duplicate endpoint name: %s' % name)
            else:
                self.named_routes[name] = endpoint

        self.endpoints.append((compiled_path, endpoint))
        self.resolve.cache_clear()

    def compile_path(self, path: str) -> Pattern:
        return re.compile('^' + path.replace('.', '\\.') + '$')

    def route(self, methods: Union[str, Iterable[str]], path: str = None,
              name: str = None) -> Callable[Callable]:
        """
        Add a route to the given function.

        This is a decorator, used as follows::

            @route('GET', '/someendpoint')
            def someendpoint(ctx):
                ...

        Multiple routes with the same path can coexist as long as their sets of allowed HTTP
        methods don't intersect.

        :param methods: allowed HTTP method or methods
        :param path:
        :param name: the unique name of the endpoint

        """
        def wrapper(func):
            endpoint = HTTPEndpoint(func, path or func.__name__)
            self.add_endpoint(endpoint, path, methods, name)
            return func

        return wrapper

    @lru_cache
    def get_named_endpoint(self, name: str) -> AbstractEndpoint:
        """
        Return the endpoint matching the given name.

        :param name: the unique name of the endpoint
        :return: the endpoint matching the given name
        :raises LookupError: if the named endpoint is not found

        """
        assert check_argument_types()
        try:
            return self.named_routes[name]
        except KeyError:
            raise LookupError('no such named endpoint: ' + name) from None

    @lru_cache
    def resolve(self, path: str, method: str) -> Optional[AbstractEndpoint]:
        pass

    # def resolve(self, request: BodyHTTPRequest, path: PurePath) -> Optional[WebEndpoint]:
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
