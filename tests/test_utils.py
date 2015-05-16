from collections import OrderedDict
from datetime import datetime, timezone

import pytest
from multidict import CIMultiDict

from asphalt.web.utils import memoize, parse_headers, parse_header_value, encode_header_value


def test_memoize():
    class Foo:
        @memoize
        def increment(self):
            nonlocal counter
            counter += 1
            return counter

    counter = 0
    foo = Foo()
    assert foo.increment() == 1
    assert foo.increment() == 1
    assert counter == 1

    assert Foo().increment() == 2
    assert counter == 2


@pytest.mark.asyncio
async def test_async_memoize():
    class Foo:
        @memoize
        async def increment(self):
            nonlocal counter
            counter += 1
            return counter

    counter = 0
    foo = Foo()
    assert await foo.increment() == 1
    assert await foo.increment() == 1
    assert counter == 1

    assert await Foo().increment() == 2
    assert counter == 2


def test_parse_headers():
    data = (b'Content-Type: text/html; charset=iso-8859-1\r\n'
            b'content-Disposition: attachment; filename="bl\xe4h.png"\r\n'
            b'some-header: value1\r\n'
            b'some-header: value2\r\n\r\n')
    expected = CIMultiDict([
        ('Content-Type', 'text/html; charset=iso-8859-1'),
        ('content-Disposition', 'attachment; filename="bläh.png"'),
        ('some-header', 'value1'),
        ('some-header', 'value2'),
    ])
    assert parse_headers(data, 'iso-8859-1') == expected


@pytest.mark.parametrize('value, expected', [
    ('text/html', ('text/html', {})),
    ('text/html; charset=UTF-8', ('text/html', {'charset': 'UTF-8'})),
    ('attachment;filename="blah.png";  filename*=utf-8\'\'bl%C3%A4h.png',
     ('attachment', {'filename': 'bläh.png'}))
], ids=['noparams', 'unquoted', 'quoted_escaped'])
def test_parse_header_value(value, expected):
    assert parse_header_value(value) == expected


@pytest.mark.parametrize('value, params, always_quote, expected', [
    ('text/html', {}, False, b'text/html'),
    ('text/html', {'charset': 'UTF-8'}, False, b'text/html; charset=UTF-8'),
    (datetime(2016, 10, 9, 23, 4, 6, 123456, tzinfo=timezone.utc), {}, False,
     b'Sun, 09 Oct 2016 23:04:06 GMT'),
    (123, {}, False, b'123'),
    ('attachment', {'filename': '日本語.png'}, True,
     b'attachment; filename="%E6%97%A5%E6%9C%AC%E8%AA%9E.png"; '
     b'filename*="utf-8\'\'%E6%97%A5%E6%9C%AC%E8%AA%9E.png"'),
    ('attachment', {'filename': 'bla"argh'}, False, b'attachment; filename="bla\\"argh"'),
], ids=['noparams', 'datevalue', 'intvalue', 'unquoted', 'unicode', 'quoted'])
def test_encode_header_value(value, params, always_quote, expected):
    assert encode_header_value(value, params, always_quote=always_quote) == expected
