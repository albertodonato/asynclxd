"""API testing helpers."""

import io

from aiohttp import ClientResponse
from json import dumps as json_dumps
from multidict import CIMultiDict
from yarl import URL

from .http import Response


class FakeRemote:
    """A fake Remote class."""

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
        return Response(self, 200, {}, make_sync_response(response))


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
        response_content = self.responses.pop(0)
        if isinstance(response_content, ClientResponse):
            return response_content
        return make_http_response(
            method=method, url=path, content=response_content)

    async def close(self):
        pass


def make_http_response(status=200, reason='OK', method='GET', url='/',
                       content=None):
    response = ClientResponse(method, URL(url))
    response.status = status
    response.reason = reason
    response.headers = CIMultiDict()
    if isinstance(content, io.IOBase):
        response._content = content.read()
    elif content is not None:
        response._content = json_dumps(content).encode('utf8')
        response.headers['Content-Type'] = 'application/json'
    return response


def make_error_response(error, code=400, http_status=None):
    """Return an API error with the specified message and code."""
    content = {
        'type': 'error',
        'error': error,
        'error_code': code,
        'metadata': {}}
    if http_status is None:
        http_status = code
    return make_http_response(
        status=http_status, reason='Failure', content=content)


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
