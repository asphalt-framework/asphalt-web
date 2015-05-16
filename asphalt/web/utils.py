import re
from datetime import datetime, timezone
from email.utils import quote, unquote, decode_rfc2231, encode_rfc2231, format_datetime
from functools import wraps
from inspect import iscoroutinefunction
from numbers import Number
from typing import Callable, Tuple, Dict, Union
from urllib.parse import quote as urllib_quote, unquote as urllib_unquote
from weakref import WeakKeyDictionary

from multidict import CIMultiDict
from typeguard import check_argument_types

header_param_re = re.compile(r"""\s*                     # initial whitespace
                                 (?P<key>[^=]+)          # the key
                                 =(?P<value>             # "=" starts a value
                                   (?:"(?:\\"|[^"])*")|  # value as quoted string
                                   (?:[^; ]*)            # value as token
                                 )(?:;|$)                # end of value or line
""", re.IGNORECASE | re.ASCII | re.VERBOSE)


def memoize(func: Callable) -> Callable:
    @wraps(func)
    def wrapper(key):
        try:
            return cache[key]
        except KeyError:
            retval = cache[key] = func(key)
            return retval

    @wraps(func)
    async def async_wrapper(key):
        try:
            return cache[key]
        except KeyError:
            retval = cache[key] = await func(key)
            return retval

    cache = WeakKeyDictionary()
    return async_wrapper if iscoroutinefunction(func) else wrapper


def parse_headers(header_data: bytes, value_encoding: str = 'ascii') -> CIMultiDict:
    assert check_argument_types()
    headers = CIMultiDict()
    for line in header_data.rstrip().split(b'\r\n'):
        key, value = line.split(b':', 1)
        key = key.strip().decode('ascii')
        value = value.strip().decode(value_encoding)
        headers.add(key, value)

    return headers


def parse_header_value(header: str) -> Tuple[str, Dict[str, str]]:
    """
    Parse an HTTP header value.

    Parameter values will be unquoted.
    If the key ends with an asterisk (``*``), the asterisk is removed from the key name and the
    value is then decoded according to :rfc:`2231`.

    :param header:
    :return: a tuple of (main value, params dict)

    """
    assert check_argument_types()
    main_value, params_str = header.partition(';')[::2]
    params = {}
    for match in header_param_re.finditer(params_str):
        key, value = match.groups()
        value = unquote(value)
        if key.endswith('*'):
            key = key[:-1]
            encoding, value = decode_rfc2231(value)[::2]
            value = urllib_unquote(value, encoding)

        params[key] = value

    return main_value.rstrip(), params


def encode_header_value(value: Union[str, datetime, Number],
                        params: Dict[str, Union[str, datetime, Number]], *,
                        encoding: str = 'ascii', always_quote: bool = False) -> bytes:
    """
    Encode a structured header value for transmission over the network.

    If a parameter value cannot be encoded to the given encoding, the :rfc:`5987` method is used to
    encode the value in an alternate field using :rfc:`2231` encoding where the field name ends
    with ``*``. The original field will have an urlencoded version of the value.

    Any datetimes in the ``value`` argument or any of the parameter values will be formatted
    as defined by :rfc:`822`. Any numeric values will be converted to strings. If a parameter value
    is ``False`` or ``None``, the parameter is omitted entirely from the output. If the value is
    ``True``, only the key will be included in the output (without any ``=``). All other value
    types are disallowed.

    :param value: the main value of the header
    :param params: a dictionary of parameter names and values
    :param encoding: the character encoding to use (either ``ascii`` or ``iso-8859-1``)
    :param always_quote: always enclose the parameter values in quotes, even if it's unnecessary
    :return: the encoded bytestring

    """
    def transform_value(val):
        if isinstance(val, str):
            return val
        elif isinstance(val, datetime):
            return format_datetime(val.astimezone(timezone.utc), usegmt=True)
        else:
            return str(val)

    assert check_argument_types()
    buffer = transform_value(value).encode(encoding)
    for key, value in params.items():
        key = key.encode(encoding)
        buffer += b'; ' + key
        value = transform_value(value)
        quoted_value = quote(value)
        add_quotes = always_quote or quoted_value != value
        try:
            quoted_value = quoted_value.encode(encoding)
        except UnicodeEncodeError:
            ascii_value = urllib_quote(quoted_value).encode('ascii')
            rfc2231_value = encode_rfc2231(quoted_value, 'utf-8').encode('utf-8')
            if add_quotes:
                ascii_value = b'"' + ascii_value + b'"'
                rfc2231_value = b'"' + rfc2231_value + b'"'

            buffer += b'=' + ascii_value + b'; ' + key + b'*=' + rfc2231_value
        else:
            if add_quotes:
                quoted_value = b'"' + quoted_value + b'"'

            buffer += b'=' + quoted_value

    return buffer
