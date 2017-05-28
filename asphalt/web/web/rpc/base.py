import re
from typing import List, Union, Optional, Dict, Callable, Tuple  # noqa

from typeguard import check_argument_types

from asphalt.web.api import AbstractEndpoint

prefix_re = re.compile(r'[^.]+(?:\.[^.]+)*', re.I)


class BaseRPCRouter(AbstractEndpoint):
    """Provides a base implementation for RPC routers."""

    __slots__ = ('routers', 'methods')

    def __init__(self):
        assert check_argument_types()
        self.routers = []  # type: List[Tuple[str, BaseRPCRouter]]
        self.methods = {}  # type: Dict[str, Callable]

    def route(self, method: str) -> Optional[Callable]:
        """
        Look up the callable that corresponds to the given RPC method name.

        :param method: the method to look up (e.g. ``foo.bar.baz``)
        :return: the matching callable if found, else ``None``

        """
        if method in self.methods:
            return self.methods[method]

        for prefix, router in self.routers:
            if method.startswith(prefix):
                return router.route(method[len(prefix):])

        return None

    def attach(self, prefix: str, router: 'BaseRPCRouter') -> None:
        """
        Attach another router under the given prefix.

        The methods of the attached router will be accessible via the given prefix.
        For example, if the attached router has a method ``frobnicate()`` and the router is
        attached using the prefix ``foobar``, the method will be available as
        ``foobar.frobnicate``.

        :param prefix:
        :param router:

        """
        assert check_argument_types()
        if not prefix_re.fullmatch(prefix):
            raise ValueError('invalid prefix: %s' % prefix)

        prefix += '.'
        for prefix_, router_ in self.routers:
            if prefix_ == prefix:
                raise Exception('prefix "%s" is already in use by another router' % prefix)

        self.routers.append((prefix, router))

    def register_method(self, func: Callable, name: str = None) -> None:
        assert check_argument_types()
        name = name or func.__name__
        if self.methods.setdefault(name, func) is not func:
            raise RuntimeError('duplicate registration of method: ' + name)

    def method(self, name_or_func: Union[str, Callable]) -> Callable:
        def wrapper(func: Callable) -> Callable:
            self.register_method(func, name_or_func)
            return func

        assert check_argument_types()
        if isinstance(name_or_func, str):
            return wrapper
        else:
            return self.register_method(name_or_func)
