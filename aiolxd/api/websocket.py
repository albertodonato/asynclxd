"""Websocket protocol for the API."""

import abc

from aiohttp import WSMsgType


class WebsocketHandler(metaclass=abc.ABCMeta):
    """A websocket API handler."""

    def __init__(self, websocket):
        self._ws = websocket

    @abc.abstractmethod
    async def handle_message(self, message):
        """Handle a websocket message.

        Must be overridden by subclasses.

        :param dict message: the message content.

        """

    async def handle_error(self, error):
        """Handle a websocket error.

        It does nothing by default, can be overridden by subclasses.

        :param Exception error: the error from the websocket.

        """


async def connect(session, path, handler_class, **handler_kwargs):
    """Connect to a websocket using the specified session.

    Appropriate methods on the handler are called when messages or errors are
    received.

    :param aiohttp.Session session: the session to perform the request.
    :param str path: the request path.
    :param dict params: optional query string parameters.
    :param WebsocketHandler handler_class: a websocket handler class.
    :param dict handler_kwargs: optional keyword arguments to pass to the
        handler class.

    """
    async with session.ws_connect(path) as websocket:
        handler = handler_class(websocket, **handler_kwargs)
        async for message in websocket:
            if message.type == WSMsgType.TEXT:
                await handler.handle_message(message.json())
            elif message.type == WSMsgType.CLOSED:
                websocket.close()
                return
            elif message.type == WSMsgType.ERROR:
                await handler.handle_error(message.data)
