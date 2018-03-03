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
    """Handler for reading events."""

    def __init__(self, remote):
        self._remote = remote

    async def __call__(self, types=None):
        params = {'type': ','.join(types)} if types else None
        await self._remote.websocket(EventHandler, 'events', params=params)


class EventHandler(WebsocketHandler):
    """Handle messages from the events websocket."""

    async def handle_message(self, message):
        return Event(**message)
