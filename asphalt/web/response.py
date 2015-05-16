from datetime import datetime

from multidict import CIMultiDict

UNIX_EPOCH = datetime(1970, 1, 1)


class HTTPResponse:
    """

    :ivar int status: HTTP status code (default = 200)
    :ivar multidict.CIMultiDict headers: response headers
    :ivar str charset: character set to use for encoding a unicode response body (default = utf-8)
    :ivar str content_type: content type to set on the response (default = determine from the
        return value)
    """

    __slots__ = ('status', 'charset', 'headers')

    def __init__(self):
        self.status = 200
        self.charset = 'utf-8'
        self.headers = CIMultiDict()


# class ContentRange:
#     __slots__ = ('start', 'end', 'total')
#
#     def __init__(self, start: Optional[int], end: Optional[int], total: Optional[int]):
#         assert check_argument_types()
#         super().__init__(start, end)
#         self.total = total
#
#         if total is not None:
#             if end is not None and end >= total:
#                 raise ValueError('the end value must be smaller than the total')
#             elif start is not None and start >= total:
#                 raise ValueError('the start value must be smaller than the total')
#
#     @classmethod
#     def parse(cls, value: str) -> 'ContentRange':
#         assert check_argument_types()
#         if value == '*':
#             return cls(None, None, None)
#
#         try:
#             range_, total = value.split('/')
#             start, end = range_.split('-')
#             start = int(start) if start else None
#             end = int(end) if end else None
#             total = int(total) if total else None
#         except ValueError:
#             raise ValueError('malformed content-range header: ' + value) from None
#
#         return cls(start, end, total)
#
#     def __str__(self):
#         if (self.start, self.end, self.total) == (None, None, None):
#             return '*'
#         else:
#             return super().__str__() + '/%s' % (self.total or '*')


# class ServerCookie(Cookie):
#     __slots__ = ('domain', 'path', 'max_age', 'expires', 'secure', 'httponly')
#
#     def __init__(self, name: str, value: str, *, domain: str, path: str = None,
#                  max_age: int = None, expires: datetime = None, secure: bool = False,
#                  httponly: bool = False):
#         assert check_argument_types()
#         super().__init__(name, value)
#         self.domain = domain
#         self.path = path
#         self.max_age = max_age
#         self.expires = expires
#         self.secure = secure
#         self.httponly = httponly
#
#         if path and not path.startswith('/'):
#             raise ValueError('path must start with /')
#         if max_age and max_age <= 0:
#             raise ValueError('max_age must be a positive value')
#         if not expires.tzinfo:
#             expires.replace(tzinfo=timezone.utc)
#
#     def __str__(self):
#         text = super().__str__()
#         if self.domain:
#             text += '; Domain=' + self.domain
#         if self.path:
#             text += '; Path=' + self.path
#         if self.max_age:
#             text += '; Max-Age=%d' % self.max_age
#         if self.expires:
#             text += '; Expires=%s' % format_datetime(self.expires, usegmt=True)
#         if self.secure:
#             text += '; Secure'
#         if self.httponly:
#             text += '; HttpOnly'
#
#         return text
