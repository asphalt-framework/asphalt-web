from typing import Union

from asphalt.core.context import Context
from wsproto.connection import WSConnection, ConnectionType
from wsproto.events import ConnectionRequested, ConnectionClosed, DataReceived

from asphalt.web.api import AbstractEndpoint
from asphalt.web.request import HTTPRequest
from asphalt.web.servers.base import BaseHTTPClientConnection


class WebSocketEndpoint(AbstractEndpoint):
    """
    Implements websocket endpoints.

    Subprotocol negotiation is currently not supported.
    """

    __slots__ = ('ctx', '_client', '_ws')

    def __init__(self, ctx: Context, client: BaseHTTPClientConnection):
        self.ctx = ctx
        self._client = client
        self._ws = WSConnection(ConnectionType.SERVER)

    def _process_ws_events(self):
        for event in self._ws.events():
            if isinstance(event, ConnectionRequested):
                self._ws.accept(event)
                self.on_connect()
            elif isinstance(event, DataReceived):
                self.on_data(event.data)
            elif isinstance(event, ConnectionClosed):
                self.on_close()

        bytes_to_send = self._ws.bytes_to_send()
        if bytes_to_send:
            self._client.write(bytes_to_send)

    def begin_request(self, request: HTTPRequest):
        trailing_data = self._client.upgrade()
        self._ws.receive_bytes(trailing_data)
        self._process_ws_events()

    def receive_body_data(self, data: bytes) -> None:
        self._ws.receive_bytes(data)
        self._process_ws_events()

    def send_message(self, payload: Union[str, bytes]) -> None:
        """
        Send a message to the client.

        :param payload: either a unicode string or a bytestring

        """
        self._ws.send_data(payload)
        bytes_to_send = self._ws.bytes_to_send()
        self._client.write(bytes_to_send)

    def close(self) -> None:
        """Close the websocket."""
        self._ws.close()
        self._process_ws_events()

    def on_connect(self) -> None:
        """Called when the websocket handshake has been done."""

    def on_close(self) -> None:
        """Called when the connection has been closed."""

    def on_data(self, data: bytes) -> None:
        """Called when there is new data from the peer."""
