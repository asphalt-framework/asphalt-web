import pytest

from asphalt.web.rpc.jsonrpc import JSONRPCError


@pytest.mark.parametrize('code', [0, -32701, -32100, -31900, 32050])
def test_valid_jsonrpc_error(code):
    exc = JSONRPCError(code, 'message', {'structured': 'data'})
    assert exc.code == code
    assert exc.message == 'message'
    assert exc.data == {'structured': 'data'}


@pytest.mark.parametrize('code', [-32700, -32600, -32601, -32602, -32603, -32099, -32000])
def test_invalid_jsonrpc_error(code):
    exc = pytest.raises(AssertionError, JSONRPCError, code, 'message')
    assert str(exc.value) == 'cannot use reserved error code %d' % code
