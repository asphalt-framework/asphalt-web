import math
from base64 import b64encode, b64decode
from collections import OrderedDict
from collections.abc import Sequence, Mapping
from datetime import date, datetime
from typing import List, Dict, Any
from xml.sax.saxutils import escape

from asphalt.core.utils import qualified_name
from lxml.etree import Element

__all__ = ('serialize', 'deserialize')

_serializers = OrderedDict()
_deserializers = OrderedDict()


def serialize(obj) -> str:
    """
    Serialize the given object into an XML-RPC ``<value>`` element.

    :param obj: the object to serialize
    :return: an XML fragment

    """
    for cls, func in _serializers.items():
        if isinstance(obj, cls):
            return '<value>%s</value>' % func(obj)

    raise TypeError('%s is not serializable' % qualified_name(obj.__class__))


def serializer(cls: type):
    def wrapper(func):
        _serializers[cls] = func
        return func
    return wrapper


@serializer(str)
def serialize_str(obj: str) -> str:
    return '<string>%s</string>' % escape(obj)


@serializer(bool)
def serialize_bool(obj: bool) -> str:
    return '<boolean>%d</boolean>' % obj


@serializer(int)
def serialize_int(obj: int) -> str:
    if not -2147483648 <= obj <= 2147483647:
        raise ValueError('%d is out of range of XML-RPC (32-bit) integer' % obj)

    return '<i4>%d</i4>' % obj


@serializer(float)
def serialize_float(obj: float) -> str:
    if math.isnan(obj) or math.isinf(obj):
        raise ValueError('XML-RPC does not support serializing infinity or NaN float objects')
    return '<double>%s</double>' % str(obj).rstrip('0')


@serializer(bytes)
def serialize_bytes(obj: bytes):
    return '<base64>%s</base64>' % b64encode(obj).decode()


@serializer(datetime)
def serialize_datetime(obj: datetime) -> str:
    return '<dateTime.iso8601>%s</dateTime.iso8601>' % obj.strftime('%Y%m%dT%H:%M:%S')


@serializer(date)
def serialize_date(obj: date) -> str:
    return '<dateTime.iso8601>%s</dateTime.iso8601>' % obj.strftime('%Y%m%dT00:00:00')


@serializer(Sequence)
def serialize_sequence(obj: Sequence) -> str:
    payload = [serialize(value) for value in obj]
    return '<array><data>%s</data></array>' % ''.join(payload)


@serializer(Mapping)
def serialize_mapping(obj: Mapping) -> str:
    payload = '<struct>'
    for key, value in obj.items():
        serialized_value = serialize(value)
        payload += '<member><name>%s</name>%s</member>' % (escape(key), serialized_value)
    return payload + '</struct>'


def deserialize(value: Element):
    """
    Deserialize an XML-RPC <value> element.

    :param value: an XML element with the tag <value>
    :return: the deserialized value

    """
    child = value[0]
    try:
        func = _deserializers[child.tag]
    except KeyError:
        raise LookupError('unknown XML-RPC type: %s' % child.tag) from None

    return func(child)


def deserializer(*names: str):
    def wrapper(func):
        _deserializers.update({key: func for key in names})
        return func
    return wrapper


@deserializer('string')
def deserialize_str(element: Element) -> str:
    return element.text


@deserializer('boolean')
def deserialize_bool(element: Element) -> float:
    if element.text == '1':
        return True
    elif element.text == '0':
        return False
    else:
        raise ValueError('invalid value for boolean: %s' % element.text)


@deserializer('int', 'i4')
def deserialize_int(element: Element) -> int:
    return int(element.text)


@deserializer('double', 'float')
def deserialize_float(element: Element) -> float:
    return float(element.text)


@deserializer('base64')
def deserialize_base64(element: Element) -> bytes:
    return b64decode(element.text)


@deserializer('dateTime.iso8601')
def deserialize_datetime(element: Element) -> datetime:
    return datetime.strptime(element.text, '%Y%m%dT%H:%M:%S')


@deserializer('array')
def deserialize_array(element: Element) -> List:
    return [deserialize(value) for value in element.findall('data/value')]


@deserializer('struct')
def deserialize_struct(element: Element) -> Dict[str, Any]:
    members = element.findall('member')
    return {member.find('name').text: deserialize(member.find('value')) for member in members}
