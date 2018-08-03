from unittest import (
    mock,
    TestCase,
)

from asynctest import TestCase as AsyncTestCase
import iso8601

from ..events import (
    Event,
    Events,
    EventHandler,
)


class EventTests(TestCase):

    def test_event_create(self):
        """An event is created from a set of details."""
        timestamp = '2018-07-06T10:09:08.00012356-10:00'
        details = {
            'type': 'logging',
            'timestamp': timestamp,
            "metadata": {'foo': 'bar'}}
        event = Event(**details)
        self.assertEqual(event.type, 'logging')
        self.assertEqual(event.timestamp, iso8601.parse_date(timestamp))
        self.assertEqual(event.metadata, {'foo': 'bar'})


class EventsTests(AsyncTestCase):

    async def test_call(self):
        """Calling the instance creates a websocket with the handler."""
        calls = []

        async def websocket(*args, **kwargs):
            calls.append((args, kwargs))

        remote = mock.Mock()
        remote.websocket = websocket

        await Events(remote)(None, types=['logging', 'operation'])
        self.assertEqual(
            calls,
            [((mock.ANY, 'events'),
              {'params': {'type': 'logging,operation'}})])


class EventHandlerTests(AsyncTestCase):

    async def test_handle_message(self):
        """The handler handles messages and returns events."""
        events = []

        async def handle_event(event):
            events.append(event)

        handler = EventHandler(handle_event)
        message = {
            'timestamp': '2015-06-09T19:07:24.379615253-06:00',
            'type': 'operation',
            'metadata': {'some': 'data'}}
        await handler.handle_message(message)
        self.assertEqual(
            events,
            [Event(
                type='operation',
                timestamp='2015-06-09T19:07:24.379615253-06:00',
                metadata={'some': 'data'})])
