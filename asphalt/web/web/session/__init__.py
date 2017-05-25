import re
from datetime import date, timedelta, datetime
from decimal import Decimal
from fractions import Fraction
from typing import Dict, Any
from uuid import UUID

from typeguard import check_argument_types

immutable_types = (type(None), str, bytes, bool, int, float, complex, range, Decimal, Fraction,
                   date, datetime, timedelta, UUID, type(re.compile('')))


class WebSession:
    __slots__ = ('id', 'expires', 'data', 'dirty')

    def __init__(self, id: UUID, expires: datetime, data: Dict[str, Any] = None):
        assert check_argument_types()
        self.id = id
        self.expires = expires
        self.dirty = data is None
        self.data = data or {}  # type: Dict[str, Any]

    def get(self, key: str, default=None):
        assert check_argument_types()
        return self.data.get(key, default)

    def __getitem__(self, key: str) -> None:
        assert check_argument_types()
        try:
            value = self.data[key]
        except KeyError:
            raise LookupError('no such session variable: %s' % key) from None

        if not self.dirty and type(value) not in immutable_types:
            self.dirty = True

        return value

    def __setitem__(self, key: str, value) -> None:
        assert check_argument_types()
        if self.data.setdefault(key, value) is not value:
            self.data[key] = value
            self.dirty = True
