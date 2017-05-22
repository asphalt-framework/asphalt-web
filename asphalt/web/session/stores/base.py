from concurrent.futures import Executor
from typing import Union

from asphalt.core import Context
from asphalt.serialization.api import Serializer
from typeguard import check_argument_types

from asphalt.web.api import SessionStore


class BaseSessionStore(SessionStore):
    """
    Stores sessions in memory. Recommended for development and testing.

    :param serializer: a serializer instance or resource name
    :param executor: thread pool executor to use when (de)serializing session data
    :param max_session_size: maximum size of the serialized session data, in bytes
    """

    __slots__ = ('serializer', 'max_session_size', 'executor')

    def __init__(self, serializer: Union[Serializer, str], max_session_size: int = 65536,
                 executor: Executor = None):
        assert check_argument_types()
        self.serializer = serializer
        self.max_session_size = max_session_size
        self.executor = executor

    async def start(self, ctx: Context) -> None:
        if isinstance(self.serializer, str):
            self.serializer = await ctx.request_resource(Serializer, self.serializer)

    def _check_serialized_data_length(self, serialized_data):
        if len(serialized_data) > self.max_session_size:
            raise RuntimeError('session data limit exceeded ({} bytes > {} bytes)'.
                               format(len(serialized_data), self.max_session_size))
