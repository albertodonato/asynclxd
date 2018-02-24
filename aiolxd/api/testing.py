"""API testing helpers"""

from .request import Response


class FakeRemote:
    """A fake Remote class"""

    version = '1.0'

    def __init__(self, responses=None):
        self.responses = responses or []
        self.calls = []

    async def request(self, method, path, params=None, headers=None,
                      content=None, upload=None):
        self.calls.append((method, path, params, headers, content, upload))
        response = self.responses.pop(0)
        if isinstance(response, Response):
            return response
        return Response(200, {}, make_sync_response(response))


class FakeSession:
    """A fake session class."""

    def __init__(self, connector=None, responses=None):
        self.connector = connector
        self.responses = responses or []
        self.calls = []

    async def request(self, method, path, params=None, headers=None,
                      json=None, data=None):
        content = json
        if data:
            content = data.read()
        self.calls.append((method, path, params, headers, content))
        return FakeHTTPResponse(self.responses.pop(0))

    async def close(self):
        pass


class FakeHTTPResponse:
    """A fake HTTP response."""

    def __init__(self, content, status=200, headers=None):
        self.status = status
        self.headers = headers or {}
        self.content = content

    async def json(self):
        return self.content


def make_resource(resource_class, uri='/resource', etag=None, details=None):
    """Return a resource instance with specified details."""
    resource = resource_class(FakeRemote(), uri)
    resource._last_etag = etag
    resource._details = details
    return resource


def make_sync_response(metadata=None):
    """Return a response for a synchronous operation."""
    return {
        'type': 'sync',
        'status': 'Success',
        'status_code': 200,
        'metadata': metadata or {}}


def make_error_response(error, code=400):
    """Return an API error with the specified message and code."""
    return {
        'type': 'error',
        'error': error,
        'error_code': code,
        'metadata': {}}
