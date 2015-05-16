from collections import OrderedDict
from datetime import datetime, date, timezone, timedelta
from decimal import Decimal

from lxml.etree import XML
import pytest

from asphalt.web.rpc.xmlrpc.serialization import serialize, deserialize


@pytest.mark.parametrize('obj, expected', [
    (0, '<i4>0</i4>'),
    (-2147483648, '<i4>-2147483648</i4>'),
    (2147483647, '<i4>2147483647</i4>'),
    (True, '<boolean>1</boolean>'),
    (False, '<boolean>0</boolean>'),
    ('foo < & >', '<string>foo &lt; &amp; &gt;</string>'),
    (-12.24, '<double>-12.24</double>'),
    (datetime(2015, 1, 17, 23, 19, 0), '<dateTime.iso8601>20150117T23:19:00</dateTime.iso8601>'),
    (date(2015, 1, 17), '<dateTime.iso8601>20150117T00:00:00</dateTime.iso8601>'),
    (b'\xff\xe6\x00', '<base64>/+YA</base64>'),
    (['foo', 4],
     '<array><data><value><string>foo</string></value><value><i4>4</i4></value></data></array>'),
    (OrderedDict([('str', 'foo'), ('int', 4)]),
     ('<struct><member><name>str</name><value><string>foo</string></value></member>'
      '<member><name>int</name><value><i4>4</i4></value></member></struct>'))
], ids=['int_0', 'int_min', 'int_max', 'bool_true', 'bool_false', 'str', 'double', 'datetime',
        'date', 'bytes', 'array', 'struct'])
def test_serialize(obj, expected: str):
    wrapped_expected = '<value>%s</value>' % expected
    assert serialize(obj) == wrapped_expected


def test_unserializable():
    exc = pytest.raises(TypeError, serialize, lambda: None)
    assert str(exc.value) == 'function is not serializable'


@pytest.mark.parametrize('obj, error', [
    (float('inf'), 'XML-RPC does not support serializing infinity or NaN float objects'),
    (float('NaN'), 'XML-RPC does not support serializing infinity or NaN float objects'),
    (2147483648, '2147483648 is out of range of XML-RPC (32-bit) integer')
])
def test_serialize_bad_value(obj, error: str):
    exc = pytest.raises(ValueError, serialize, obj)
    assert str(exc.value) == error


@pytest.mark.parametrize('xml, expected', [
    ('<i4>-2147483648</i4>', -2147483648),
    ('<i4>2147483647</i4>', 2147483647),
    ('<boolean>1</boolean>', True),
    ('<boolean>0</boolean>', False),
    ('<string>foo &lt; &amp; &gt;</string>', 'foo < & >'),
    ('<double>-12.24</double>', -12.24),
    ('<dateTime.iso8601>20150117T23:19:00</dateTime.iso8601>', datetime(2015, 1, 17, 23, 19, 0)),
    ('<base64>/+YA</base64>', b'\xff\xe6\x00'),
    ('<array><data><value><string>foo</string></value><value><i4>4</i4></value></data></array>',
     ['foo', 4]),
    (('<struct><member><name>str</name><value><string>foo</string></value></member>'
      '<member><name>int</name><value><i4>4</i4></value></member></struct>'),
     OrderedDict([('str', 'foo'), ('int', 4)]))
], ids=['int_min', 'int_max', 'bool_true', 'bool_false', 'str', 'double', 'datetime', 'base64',
        'array', 'struct'])
def test_deserialize(xml, expected: str):
    element = XML('<value>%s</value>' % xml)
    assert deserialize(element) == expected


def test_deserializable_unknown_type():
    element = XML('<value><badtype /></value>')
    exc = pytest.raises(LookupError, deserialize, element)
    assert str(exc.value) == 'unknown XML-RPC type: badtype'


def test_invalid_boolean():
    element = XML('<value><boolean>blah</boolean></value>')
    exc = pytest.raises(ValueError, deserialize, element)
    assert str(exc.value) == 'invalid value for boolean: blah'
