from asynctest import TestCase

from ..testing import (
    FakeSession,
    FakeWebSocket,
    FakeWSMessage,
)
from ..websocket import (
    connect,
    WebsocketHandler,
)


class SampleWebsocketHandler(WebsocketHandler):

    def __init__(self, websocket, messages=None, errors=None):
        super().__init__(websocket)
        self.messages = messages if messages is not None else []
        self.errors = errors if errors is not None else []

    async def handle_message(self, message):
        self.messages.append(message)

    async def handle_error(self, error):
        self.errors.append(error)


class ConnectTests(TestCase):

    def setUp(self):
        super().setUp()

    async def test_messages(self):
        """"connect() processses messages."""
        messages = [FakeWSMessage('foo'), FakeWSMessage('bar')]
        session = FakeSession(websocket=FakeWebSocket(messages=messages))
        received_messages = []
        await connect(
            session, '/', SampleWebsocketHandler, messages=received_messages)
        self.assertEqual(received_messages, ['"foo"', '"bar"'])

    async def test_error(self):
        """"connect() processes errors."""
        messages = [FakeWSMessage('error', type="ERROR")]
        session = FakeSession(websocket=FakeWebSocket(messages=messages))
        received_errors = []
        await connect(
            session, '/', SampleWebsocketHandler, errors=received_errors)
        self.assertEqual(received_errors, ['error'])

    async def test_close(self):
        """"connect() processes closes messages."""
        messages = [FakeWSMessage(None, type="CLOSED")]
        websocket = FakeWebSocket(messages=messages)
        session = FakeSession(websocket=websocket)
        received_messages = []
        received_errors = []
        await connect(
            session, '/', SampleWebsocketHandler, messages=received_messages,
            errors=received_errors)
        self.assertEqual(received_messages, [])
        self.assertEqual(received_errors, [])
        self.assertTrue(websocket.closed)
