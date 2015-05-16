import logging
import re
from datetime import date
from typing import Union
from xml.etree.ElementTree import ParseError

from asphalt.core.context import Context
from asyncio_extras.threads import call_in_executor, threadpool
from defusedxml import cElementTree
from typeguard import check_argument_types

from asphalt.web.context import HTTPRequestContext
from asphalt.web.exceptions import HTTPError
from asphalt.web.request import BodyHTTPRequest
from asphalt.web.rpc.base import BaseRPCRouter
from asphalt.web.rpc.xmlrpc.serialization import serialize, deserialize

logger = logging.getLogger(__name__)
xmlrpc_types = Union[str, bytes, int, float, date]


class XMLRPCError(Exception):
    """
    An exception that can be raised by application code to return a XML-RPC error to the client.

    :param code: a numeric error code outside of the reserved range
        (-32700, -32600, -32601, -32602, -32603 and -32099 – -32000)
    :param message: an error message
    """

    def __init__(self, code: int, message: str):
        assert check_argument_types()
        super().__init__(message)
        self.code = code
        self.message = message


class XMLRPCRouter(BaseRPCRouter):
    """
    An endpoint that serves XML-RPC requests.

    Responses can contain any types compatible with XML-RPC:

    * int (signed, 32-bit; -2147483648 to 2147483647)
    * bool
    * str
    * float
    * datetime (any timezone information is ignored)
    * date (serialized as datetime with time as 00:00:00)
    * bytes (serialized as base64)
    * Sequence (list, tuple and other compatible types; serialized as ``<array>``)
    * Mapping (dict and other compatible types; serialized as ``<struct>``)

    .. note:: The ``None`` type is **NOT** compatible with XML-RPC.
    """

    __slots__ = ('routers', 'methods')

    @staticmethod
    def _create_error(code: int, message: str) -> bytes:
        fault = serialize({'faultCode': code, 'faultString': message})
        return ('<?xml version="1.0"?>\n<methodResponse><fault>' + fault +
                '</fault></methodResponse>')

    async def begin_request(self, parent_ctx: Context, request: BodyHTTPRequest):
        # Check that the HTTP method was "POST"
        if request.method != 'POST':
            raise HTTPError(405, 'POST required for XML-RPC')

        # Check that the content type is correct
        if request.content_type != 'text/xml':
            raise HTTPError(400, 'Wrong content-type for XML-RPC (must be text/xml)')

        # Parse the XML request
        body = await request.body.read()
        try:
            document = cElementTree.fromstring(body.decode('utf-8'))
        except (UnicodeDecodeError, ParseError) as e:
            raise XMLRPCError(-32701, 'Parse error: %s' % e)

        # Find the requested method name
        methodname = document.find('methodName')
        if not methodname:
            raise XMLRPCError(-32600, 'Server error: invalid xml-rpc')

        # Find the callable by the method name
        method = self.methods.get(methodname)
        if method is None:
            raise XMLRPCError(-32601, 'Server error: method not found')

        # Deserialize the arguments
        param_elements = document.findall('params/param/value')
        try:
            async with threadpool():
                args = [deserialize(element) for element in param_elements]
        except Exception as e:
            raise XMLRPCError(-32602, 'Server error: invalid arguments: %s' % e)

        # Create a request context and call the callable in it
        async with HTTPRequestContext(parent_ctx, self, request) as ctx:
            retval = exception = fault_code = None
            try:
                retval = await method(ctx, *args)
            except XMLRPCError as e:
                exception = e
                fault_code = e.fault_code
            except Exception as e:
                exception = e
                fault_code = -32500
                logger.exception('Error during method invocation')

            # Serialize the return value
            serialized_retval = None
            try:
                serialized_retval = await call_in_executor(serialize, retval)
            except Exception as e:
                exception = e
                fault_code = -32603

        # Finish the request context
        try:
            await ctx.dispatch_event('finished', exception)
        except Exception as e:
            exception = e
            fault_code = -32400
            logger.exception('Error during XML-RPC request context teardown')

        # Generate the methodResponse XML
        if exception is None:
            body = ('<?xml version="1.0"?>\n<methodResponse><params><value>%s'
                    '</value></params></methodResponse>' % serialized_retval)
        else:
            fault = serialize({'faultCode': fault_code, 'faultString': str(exception)})
            body = ('<?xml version="1.0"?>\n<methodResponse><fault>%s'
                    '</fault></methodResponse>' % fault)

        ctx.response.content_type = 'text/xml'
