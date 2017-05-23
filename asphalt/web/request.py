import re
from asyncio import StreamReader
from decimal import Decimal
from email.utils import parsedate_to_datetime
from http.cookies import SimpleCookie
from inspect import getmembers
from pathlib import Path
from typing import Optional, Callable, Any, Union, Iterable, List, Tuple, Sequence, Dict
from urllib.parse import parse_qs, parse_qsl

from async_generator import async_generator, yield_, aclosing
from asyncio_extras import open_async
from multidict import CIMultiDict, MultiDict, MultiDictProxy
from typeguard import check_argument_types

from asphalt.web.exceptions import HTTPRangeError, HTTPBadRequest
from asphalt.web.utils import parse_headers, parse_header_value, memoize


class ConvertedHeader:
    def __init__(self, converter: Callable[[Any], Any]):
        self.header_name = None
        self.converter = converter

    def __set_name__(self, owner, name: str) -> None:
        self.header_name = name.replace('_', '-')

    def __get__(self, instance: 'HTTPRequest', owner):
        if self.header_name is None:
            header_name = next(
                attr for attr, value in getmembers(owner, lambda value: value is self))
            self.__set_name__(owner, header_name)

        value = instance._headers.get(self.header_name)
        return self.converter(value) if value is not None else None


class FormField:
    """
    Represents a form field.

    :ivar CIMultiDict headers: any field specific headers
    :ivar str name: name of the field
    :ivar str filename: the ``filename`` attribute of the field, if supplied
    """

    __slots__ = ('headers', 'complete', 'name', 'filename', '_body', '_boundary')

    def __init__(self, headers: CIMultiDict, body: StreamReader, boundary: bytes):
        self.headers = headers
        self.complete = False
        self._body = body
        self._boundary = boundary

        disposition = headers['content-disposition']
        value, params = parse_header_value(disposition)
        if value.lower() != 'form-data':
            raise HTTPBadRequest('unexpected content disposition in multipart form: ' + value)

        try:
            self.name = params['name']
        except KeyError:
            raise HTTPBadRequest('missing form field name in multipart form part') from None

        self.filename = params.get('filename')

    async def save_file(self, directory: Union[Path, str], filename: str = None) -> None:
        """
        Save the contents of the form field to a file.

        :param directory: path to the directory to save the file in
        :param filename: name of the file

        """
        filename = filename or self.filename
        if not filename:
            raise RuntimeError('file name not present in field and no filename argument given')

        path = Path(directory) / filename
        async with open_async(path, 'wb') as f:
            while True:
                data = await self._body.read(65536)
                if not data:
                    break

                boundary_start = data.find(self._boundary)
                if boundary_start >= 0:
                    await f.send_message(data[:boundary_start])


# class Cookie:
#     __slots__ = ('name', 'value')
#
#     def __init__(self, name: str, value: str):
#         assert check_argument_types()
#         self.name = name
#         self.value = value
#
#     @classmethod
#     def parse(cls, value: str) -> List['Cookie']:
#         pass


class HTTPRange:
    """Represents the parsed value of an HTTP ``range`` header."""

    __slots__ = 'ranges'

    def __init__(self, value: str):
        assert check_argument_types()
        specifier, _, rest = value.replace(' ', '').partition('=')
        if not rest:
            raise ValueError('malformed range header')
        if specifier != 'bytes':
            raise ValueError('unexpected range specifier: ' + specifier)

        self.ranges = []
        for range_set in rest.split(','):
            start, end = range_set.split('-')
            try:
                start = int(start) if start else 0
                end = int(end) if end else None
            except ValueError:
                raise ValueError('malformed range header')

            if start is None and end is None:
                raise ValueError('malformed range header')

            self.ranges.append((start, end))

    def compute_ranges(self, max_length: int) -> Sequence[range]:
        """
        Transform the range sets to actual ranges based on the given maximum length.

        :param max_length: the length to compute against
        :return: a sequence of range objects
        :raises HTTPRangeError: the range was not satisfiable

        """
        assert check_argument_types()
        ranges = []
        for start, end in self.ranges:
            if start < 0:
                start += max_length
            if end is not None:
                end = max_length - 1

            if start >= max_length:
                raise HTTPRangeError('start offset exceeds maximum length: %d >= %d' %
                                     (start, max_length))
            elif end >= max_length:
                raise HTTPRangeError('end offset exceeds maximum length: %d >= %d' %
                                     (end, max_length))

            ranges.append(range(start, end + 1))

        return ranges

    def __repr__(self):
        ranges = ','.join(
            '%s-%s' % (start or '', end if end is not None else '')
            for start, end in self.ranges)
        return '%s(%s)' % (self.__class__.__name__, ranges)


class HTTPAccept:
    """Represents the parsed value of an HTTP ``accept`` header."""

    __slots__ = 'content_types'

    language_re = re.compile(r'(\*|(?:[a-z]+))(?:-([a-z]+))?(?:;q=(\d(?:\.\d{1,3})?))?$', re.I)

    def __init__(self, value: Optional[str]):
        assert check_argument_types()
        self.content_types = []  # type: List[Tuple[str, Optional[str], Optional[Decimal]]]
        if value:
            for part in [x.strip() for x in value.replace(' ', '').split(',')]:
                match = self.language_re.match(part)
                if match:
                    language, variant, quality = match.groups()
                    quality = Decimal(quality) if quality else 1
                    self.content_types.append((language, variant, quality))

    def best_match(self, available: Iterable[str], fallback: str = None) -> Optional[str]:
        """
        Pick the language that best matches the acceptable languages specified by the header.

        :param available: an iterable of language codes (like ``en``, ``en-us``, ``fi``, etc.);
            the case is ignored and the separator can be either ``-`` or ``_``
        :param fallback: the value to return if there was no match
        :return: the best choice from ``available``, or the value of ``default`` if there was no
            match

        """
        best_type = best_subtype = best_quality = None
        candidates = [val.lower().partition('/')[::2] for val in available]
        for type_, subtype, quality in self.content_types:
            if best_quality is None or quality > best_quality:
                for avail_type, avail_variant in candidates:
                    if (type_ == '*' or type_ == avail_type and
                            subtype in (avail_variant, None)):
                        best_type, best_subtype, best_quality = avail_type, avail_variant, quality
                        break

        if best_type:
            return '%s-%s' % (best_type, best_subtype) if best_subtype else best_type
        else:
            return fallback

    def __repr__(self):
        content_types = []
        for type_, subtype, quality in self.content_types:
            if subtype:
                text = '%s-%s' % (type_, subtype)
            else:  # skip the hyphen used with subtype
                text = '%s' % (type_)
            if quality < 1:
                text += ';q=%s' % quality

            content_types.append(text)

        return '%s(%r)' % (self.__class__.__name__, ', '.join(content_types))


class HTTPAcceptLanguage:
    """Represents the parsed value of an HTTP ``accept-language`` header."""

    __slots__ = 'languages'

    language_re = re.compile(r'(\*|(?:[a-z]+))(?:-([a-z]+))?(?:;q=(\d(?:\.\d{1,3})?))?$', re.I)

    def __init__(self, value: Optional[str]):
        assert check_argument_types()
        self.languages = []  # type: List[Tuple[str, Optional[str], Union[Decimal, int]]]
        if value:
            for part in [x.strip() for x in value.replace(' ', '').split(',')]:
                match = self.language_re.match(part)
                if match:
                    language, variant, quality = match.groups()
                    quality = Decimal(quality) if quality else 1
                    self.languages.append((language, variant, quality))

    def best_match(self, available: Sequence[str], fallback: str = None) -> Optional[str]:
        """
        Pick the language that best matches the acceptable languages specified by the header.

        :param available: a sequence of language codes (like ``en``, ``en-us``, ``fi``, etc.);
            the case is ignored and the separator can be either ``-`` or ``_``
        :param fallback: the value to return if there was no match
        :return: the best choice from ``available``, or the value of ``default`` if there was no
            match

        """
        if not self.languages:
            return available[0] if available else fallback

        best_lang = best_variant = best_quality = None
        candidates = [val.lower().replace('_', '-').partition('-')[::2] for val in available]
        for language, variant, quality in self.languages:
            if best_quality is None or quality > best_quality:
                for avail_lang, avail_variant in candidates:
                    if (language == '*' or language == avail_lang and
                            variant in (avail_variant, None)):
                        best_lang, best_variant, best_quality = avail_lang, avail_variant, quality
                        break

        if best_lang:
            return '%s-%s' % (best_lang, best_variant) if best_variant else best_lang
        else:
            return fallback

    def __repr__(self):
        languages = []
        for language, variant, quality in self.languages:
            text = language
            if variant:
                text += '-' + variant
            if quality < 1:
                text += ';q=%s' % quality

            languages.append(text)

        return '%s(%r)' % (self.__class__.__name__, ', '.join(languages))


class HTTPRequest:
    """
    Represents an HTTP request.

    It should be noted that if the application is behind a reverse proxy such as nginx or Apache,
    some of these values may not reflect their expected values.
    This affects in particular the ``http_version``, ``peername`` and ``peercert`` attributes.
    Special measures must be taken to retain the proper values through a reverse proxy connection.

    :ivar str http_version: HTTP version (e.g. ``1.1`` or ``2``)
    :ivar str method: HTTP method (e.g. ``GET``, ``POST``, etc.)
    :ivar str path: request path (e.g. ``/some/resource/somewhere``)
    :ivar str query: HTTP query string
    :ivar str scheme: ``http`` or ``https`` depending on whether TLS was used to connect to the
        server
    :ivar str peername: IP address or UNIX socket path of the client
    :ivar str peercert: the raw client certificate data if the client presented a certificate
        .. seealso:: https://docs.python.org/3/library/ssl.html#ssl.SSLSocket.getpeercert
    """

    def __init__(self, http_version: str, method: str, path: str, query_string: str,
                 headers: CIMultiDict, body: Optional[StreamReader], secure: bool, peername: str,
                 peercert: Optional[str]):
        assert check_argument_types()
        self.http_version = http_version
        self.method = method.upper()
        self.path = path
        self.query_string = query_string
        self._headers = headers
        self._body = body
        self.secure = secure
        self.peername = peername
        self.peercert = peercert

    accept = ConvertedHeader(HTTPAccept)
    # accept_charset = ConvertedHeader(HTTPAcceptCharset.parse)
    # accept_encoding = ConvertedHeader(HTTPAcceptEncoding.parse)
    accept_language = ConvertedHeader(HTTPAcceptLanguage)
    range = ConvertedHeader(HTTPRange)
    content_length = ConvertedHeader(int)
    if_modified_since = ConvertedHeader(parsedate_to_datetime)
    if_range = ConvertedHeader(HTTPRange)
    if_unmodified_since = ConvertedHeader(parsedate_to_datetime)
    max_forwards = ConvertedHeader(int)

    @property
    @memoize
    def headers(self) -> MultiDictProxy:
        """Return the raw, unparsed request headers."""
        return MultiDictProxy(self._headers)

    @property
    @memoize
    def query(self) -> MultiDictProxy:
        """Return a dictionary of query parameters."""
        query_dict = MultiDict(parse_qsl(self.query, errors='strict'))
        return MultiDictProxy(query_dict)

    @property
    @memoize
    def charset(self) -> Optional[str]:
        """Return the character set of the request, or ``None`` if none was defined."""
        main, params = parse_header_value(self._headers.get('content-type', ''))
        return params.get('charset').lower() if 'charset' in params else None

    @property
    @memoize
    def content_type(self) -> Optional[str]:
        """Return the content type of the request, or ``None`` if none was defined."""
        main, params = parse_header_value(self._headers.get('content-type', ''))
        return main.lower() if main else None

    @property
    @memoize
    def cookies(self) -> MultiDictProxy:
        """Return a read-only dictionary containing cookie values sent by the client."""
        cookie_val = self._headers.get('cookie', '')
        cookies_dict = {key: value.value for key, value in SimpleCookie(cookie_val).items()}
        return MultiDictProxy(cookies_dict)

    @property
    def is_xhr(self) -> bool:
        """
        Return ``True`` if the request was made with XMLHttpRequest, ``False`` otherwise.

        This only works if the ``X-Requested-With: XMLHttpRequest`` header was set.
        Several popular ECMAScript libraries do this but it is purely voluntary.
        As such, this is not a 100% reliable method of detecting such requests.

        """
        return self._headers.get('x-requested-with') == 'XMLHttpRequest'

    async def read(self):
        """
        Read and decode the request body according to its content type.

        Forms (``application/x-www-form-urlencoded`` and ``multipart/form-data``) are automatically
        parsed. If instead the content type matches a known serializer, it is used to deserialize
        the request body. If the content type's main part is ``text``, the body is decoded as
        unicode using the given charset. Otherwise, the binary body is returned as is.

        :return: the decoded body

        """
        if self.content_type == 'application/x-www-form-urlencoded':
            body = await self._body.read()
            return parse_qs(body, strict_parsing=True, encoding=self.charset or 'utf-8',
                            errors='strict')
        elif self.content_type == 'multipart/form-data':
            form = {}
            async with aclosing(self.read_iter()) as stream:
                async for field in stream:
                    form[field.name] = field
        else:
            body = await self._body.read()
            if self.content_type.startswith('text/'):
                return body.decode(self.charset or 'utf-8')
            else:
                return body

    @async_generator
    async def read_iter(self):
        content_type, params = parse_header_value(self._headers.get('content-type', ''))
        if content_type != 'multipart/form-data':
            if self.content_type is None:
                raise RuntimeError('no content-type header present in request')
            else:
                raise RuntimeError('expected "multipart/form-data" as content type, not "%s"' %
                                   self.content_type)

        boundary = params.get('boundary')
        if not boundary:
            raise RuntimeError('no boundary specified for multipart/form-data')

        boundary = boundary.encode('ascii') + b'\r\n\r\n'
        while True:
            header_data = await self._body.readuntil(boundary)
            if not header_data:
                break

            headers = parse_headers(header_data)
            field = FormField(headers, self._body, boundary)
            await yield_(field)
