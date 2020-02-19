"""API resources for events."""

import attr
import iso8601

from ..websocket import WebsocketHandler


@attr.s
class Event:
    """An event from the API."""

    type = attr.ib()
    timestamp = attr.ib(converter=iso8601.parse_date)
    metadata = attr.ib()


class Events:
    """Handler for reading events.

    When called, it creates a task that reads events and calls the specified
    handler with each :class:`Event`.

    """

    def __init__(self, remote):
        self._remote = remote

    def __call__(self, handle_event, types=None):
        params = {"type": ",".join(types)} if types else None
        return self._remote.websocket(
            EventHandler(handle_event), "events", params=params
        )


class EventHandler(WebsocketHandler):
    """Handle messages from the events websocket.

    the `handle_event` handler is called with an :class:`Event` instance.

    """

    def __init__(self, handle_event):
        self.handle_event = handle_event

    async def handle_message(self, message):
        await self.handle_event(Event(**message))
