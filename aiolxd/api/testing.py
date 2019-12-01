"""API testing helpers."""

from asyncio import get_event_loop
import io
from json import dumps as json_dumps

from aiohttp import (
    ClientResponse,
    RequestInfo,
    WSMsgType,
)
from multidict import CIMultiDict
from yarl import URL

from .http import (
    ContentStream,
    Response,
)


class AsyncIterator:
    """Wrapper to convert a sync iterator to async."""

    def __init__(self, iterable):
        self.iterable = iter(iterable)

    async def __anext__(self):
        try:
            return next(self.iterable)
        except StopIteration:
            raise StopAsyncIteration()


class FakeRemote:
    """A fake Remote class."""

    version = "1.0"

    def __init__(self, responses=None):
        self.responses = responses or []
        self.calls = []

    async def request(
        self, method, path, params=None, headers=None, content=None, upload=None
    ):
        self.calls.append((method, path, params, headers, content, upload))
        response = self.responses.pop(0)
        if isinstance(response, Response):
            return response
        return Response(self, 200, {}, make_response_content(response))


class FakeSession:
    """A fake session class."""

    def __init__(self, connector=None, responses=(), websocket=None):
        self.connector = connector
        self.responses = list(responses)
        self.websocket = websocket
        self.calls = []

    async def request(
        self, method, path, params=None, headers=None, json=None, data=None
    ):
        content = json
        if data:
            content = data.read()
        self.calls.append((method, path, params, headers, content))
        response_content = self.responses.pop(0)
        if isinstance(response_content, ClientResponse):
            return response_content
        return make_http_response(method=method, url=path, content=response_content)

    def ws_connect(self, path):
        return self.websocket

    async def close(self):
        pass


class FakeWebSocket:
    """A fake websocket context manager."""

    closed = False

    def __init__(self, messages=()):
        self.messages = messages

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        pass

    def __aiter__(self):
        return AsyncIterator(self.messages)

    def close(self):
        self.closed = True


class FakeWSMessage:
    """A Fake websocket message."""

    def __init__(self, data, type="TEXT"):
        self.type = getattr(WSMsgType, type)
        self.data = data

    def json(self):
        return json_dumps(self.data)


class FakeStreamReader(ContentStream):
    """A fake StreamReader implementation."""

    def __init__(self, stream):
        self._stream = stream
        self._exception = None

    async def read(self):
        return self._stream.read()

    def iter_any(self):
        return FakeStreamIterator(self._stream)

    def exception(self):
        return self._exception

    def set_exception(self, exc):
        self._exception = exc


# register StringIO since it's used in tests
ContentStream.register(io.StringIO)


class FakeStreamIterator:
    """A fake stream iterator."""

    def __init__(self, stream):
        self._content = stream.read()

    def __aiter__(self):
        return self

    async def __anext__(self):
        if not self._content:
            raise StopAsyncIteration()

        content, self._content = self._content, None
        return content


def make_http_response(
    status=200, reason="OK", method="GET", url="/", headers=None, content=None
):
    """Return a minimal ClientResponse with fields used in tests."""
    url = URL(url)
    headers = CIMultiDict(headers or {})
    request_info = RequestInfo(url=url, method=method, headers=headers)
    response = ClientResponse(
        method,
        url,
        writer=None,
        continue100=None,
        timer=None,
        request_info=request_info,
        traces=(),
        loop=get_event_loop(),
        session=None,
    )
    response.status = status
    response.reason = reason
    response._headers = headers
    if isinstance(content, io.IOBase):
        response.content = FakeStreamReader(content)
    elif content is not None:
        response.content = FakeStreamReader(
            io.BytesIO(json_dumps(content).encode("utf8"))
        )
        response.headers["Content-Type"] = "application/json"
    return response


def make_error_response(error, code=400, http_status=None):
    """Return an API error with the specified message and code."""
    content = {"type": "error", "error": error, "error_code": code, "metadata": {}}
    if http_status is None:
        http_status = code
    return make_http_response(status=http_status, reason="Failure", content=content)


def make_response_content(metadata=None):
    """Return content for an API successful response."""
    return {
        "type": "sync",
        "status": "Success",
        "status_code": 200,
        "metadata": metadata or {},
    }


def make_resource(resource_class, uri="/resource", etag=None, details=None):
    """Return a resource instance with specified details."""
    resource = resource_class(FakeRemote(), uri)
    resource._last_etag = etag
    resource._details = details
    return resource
