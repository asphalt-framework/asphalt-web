from typeguard import check_argument_types


class HTTPError(Exception):
    def __init__(self, code: int, body: str = None):
        assert check_argument_types()
        self.code = code
        self.body = body


class RoutingError(LookupError):
    """Raised when a router cannot resolve a path to an endpoint."""


class HTTPBadRequest(Exception):
    """Raised when the incoming request is invalid in some way."""


class HTTPRangeError(Exception):
    """Raised by :class:`~.request.HTTPRange.compute_range` when the range is not satisfiable."""
