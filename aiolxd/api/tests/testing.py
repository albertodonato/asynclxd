"""API testing helpers"""


class FakeSession:
    """A fake session class."""

    def __init__(self, responses=None):
        self.responses = responses or []
        self.calls = []

    async def request(self, method, path, headers=None):
        self.calls.append((method, path, headers))
        return FakeResponse(self.responses.pop(0))


class FakeResponse:
    """A fake HTTP response."""

    def __init__(self, content):
        self.content = content

    async def json(self):
        return self.content


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
