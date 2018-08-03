from asynctest import TestCase

from ..testing import (
    FakeSession,
    FakeWebSocket,
    FakeWSMessage,
)
from ..websocket import (
    WebsocketHandler,
    connect,
)


class SampleWebsocketHandler(WebsocketHandler):

    def __init__(self, messages=None, errors=None):
        self.messages = []
        self.errors = []

    async def handle_message(self, message):
        self.messages.append(message)

    async def handle_error(self, error):
        self.errors.append(error)


class ConnectTests(TestCase):

    async def test_messages(self):
        """"connect() processses messages."""
        messages = [FakeWSMessage('foo'), FakeWSMessage('bar')]
        session = FakeSession(websocket=FakeWebSocket(messages=messages))
        handler = SampleWebsocketHandler()
        await connect(session, '/', handler)
        self.assertEqual(handler.messages, ['"foo"', '"bar"'])

    async def test_error(self):
        """"connect() processes errors."""
        messages = [FakeWSMessage('error', type="ERROR")]
        session = FakeSession(websocket=FakeWebSocket(messages=messages))
        handler = SampleWebsocketHandler()
        await connect(session, '/', handler)
        self.assertEqual(handler.errors, ['error'])

    async def test_close(self):
        """"connect() processes closes messages."""
        messages = [FakeWSMessage(None, type="CLOSED")]
        websocket = FakeWebSocket(messages=messages)
        session = FakeSession(websocket=websocket)
        handler = SampleWebsocketHandler()
        await connect(session, '/', handler)
        self.assertEqual(handler.messages, [])
        self.assertEqual(handler.errors, [])
        self.assertTrue(websocket.closed)
