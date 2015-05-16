import logging
import re
from inspect import isawaitable
from typing import Callable, Dict, List, Tuple, Union, Optional, Any

from asphalt.core import Context
from asphalt.serialization.api import Serializer
from asphalt.serialization.serializers.json import JSONSerializer
from asyncio_extras import call_in_executor
from typeguard import check_argument_types

from asphalt.web.api import AbstractEndpoint
from asphalt.web.context import HTTPRequestContext
from asphalt.web.exceptions import HTTPError
from asphalt.web.request import HTTPRequest
from asphalt.web.rpc.base import BaseRPCRouter

logger = logging.getLogger(__name__)
prefix_re = re.compile(r'[^.]+(?:\.[^.]+)*', re.I)
json_types = Union[str, int, float, bool, dict, list, None]


class JSONRPCError(Exception):
    """
    An exception that can be raised by application code to return a JSON-RPC error to the client.

    :param code: a numeric error code outside of the reserved range
        (-32700, -32600, -32601, -32602, -32603 and -32099 – -32000)
    :param message: an error message
    :param data: extra data (any JSON type)
    """

    def __init__(self, code: int, message: str, data: json_types = None):
        assert check_argument_types()
        assert (code not in (-32700, -32600, -32601, -32602, -32603) and
                not -32099 <= code <= -32000), 'cannot use reserved error code %d' % code
        super().__init__(message)
        self.code = code
        self.message = message
        self.data = data


class JSONRPCRouter(BaseRPCRouter):
    """
    An endpoint that serves JSON-RPC requests.

    :param serializer: a JSON serializer instance or a resource name (if omitted, a default
        serializer will be created)
    """

    __slots__ = 'serializer'

    def __init__(self, serializer: Union[Serializer, str, None]):
        super().__init__()
        self.serializer = serializer or JSONSerializer()  # type: Serializer
        if not isinstance(serializer, str):
            self._check_serializer_mimetype()

    def _check_serializer_mimetype(self):
        if self.serializer.mimetype != 'application/json':
            raise Exception("the serializer's mimetype must be application/json, not %s" %
                            self.serializer.mimetype)

    def _create_error(self, request_id, code: int, message: str, data: json_types = None) -> bytes:
        error = {'code': code, 'message': message}
        if data:
            error[data] = data

        response = {'jsonrpc': '2.0', 'error': error, 'id': request_id}
        return self.serializer.serialize(response)

    async def begin_request(self) -> bytes:
        if self.request.method != 'POST':
            raise HTTPError(405, 'POST required for JSON-RPC')
        if self.request.content_type != 'application/json':
            raise HTTPError(400, 'Wrong content-type for JSON-RPC (must be application/json)')

        # Acquire the serializer if a string was given
        if isinstance(self.serializer, str):
            self.serializer = self.parent_ctx.request_resource(
                Serializer, self.serializer)  # type: Serializer
            self._check_serializer_mimetype()

        # Deserialize the request
        try:
            jsonrpc_requests = await call_in_executor(self.serializer.deserialize)
        except Exception as e:
            return self._create_error(None, -32700, 'Parse error', str(e))

        # If "requests" is a list, then this is a batch of requests
        batch_mode = isinstance(jsonrpc_requests, list)
        if not batch_mode:
            jsonrpc_requests = [jsonrpc_requests]

        # Handle requests one by one
        results = []  # type: List[bytes]
        for jsonrpc_request in jsonrpc_requests:
            try:
                result = await self.handle_jsonrpc_request(parent_ctx, request, jsonrpc_request)
            except Exception as e:
                result = self._create_error(None, -32603, 'Internal error', str(e))

            results.append(result)

        # Send the results
        if batch_mode:
            return b'[' + b','.join(results) + b']'
        else:
            return results[0]

    async def handle_jsonrpc_request(self, parent_ctx: Context, request: HTTPRequest,
                                     jsonrpc_request: Dict[str, Any]) -> bytes:
        # Bail out if the request isn't a dict
        if not isinstance(jsonrpc_request, dict):
            return self._create_error(None, -32600, 'Invalid Request',
                                      'the request must be an object')

        # Check the JSON-RPC version
        version = jsonrpc_request.get('jsonrpc', '1.0')
        if version != '2.0':
            return self._create_error(None, -32600, 'Invalid Request',
                                      'cannot handle protocol version %s' % version)

        # Extract and validate the method and params
        method, params, request_id = [jsonrpc_request.get(field) for field in
                                      ('method', 'params', 'id')]
        if not method:
            return self._create_error(request_id, -32600, 'Invalid Request',
                                      '"method" must not be empty')
        if isinstance(params, list):
            args, kwargs = params, {}
        elif isinstance(params, dict):
            args, kwargs = (), params
        else:
            return self._create_error(request_id, -32602, 'Invalid Request',
                                      '"params" must be an array or object')

        # Look up the endpoint
        handler = self.route(method)
        if handler is None:
            return self._create_error(request_id, -32601, 'Method not found')

        # Call the handler
        async with HTTPRequestContext(parent_ctx, request) as ctx:
            try:
                retval = handler(ctx, *args, **kwargs)
                if isawaitable(retval):
                    retval = await retval
            except JSONRPCError as e:
                return self._create_error(request_id, e.code, e.message, e.data)
            else:
                response = {'jsonrpc': '2.0', 'result': retval, 'id': request_id}
                return await call_in_executor(self.serializer.serialize, response)
