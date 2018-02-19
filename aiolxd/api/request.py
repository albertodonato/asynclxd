"""Perform requests to the API."""

from pprint import pformat


class Response:
    """An API response."""

    def __init__(self, http_code, http_headers, content):
        self.http_code = http_code
        self.etag = http_headers.get('ETag')
        self.location = http_headers.get('Location')
        self.type = content.get('type')
        self.metadata = content.get('metadata', {})

    def pprint(self):
        """Pretty-print the response."""
        data = {
            'http-code': self.http_code,
            'etag': self.etag,
            'location': self.location,
            'type': self.type,
            'metadata': self.metadata}
        return pformat(data)


class ResponseError(Exception):
    """An API response error."""

    def __init__(self, code, message):
        self.code = code
        self.message = message
        super().__init__(
            'API request failed with {code}: {message}'.format(
                code=self.code, message=self.message))


async def request(session, method, path, params=None, headers=None,
                  content=None):
    """Perform an API request with the session."""
    if not headers:
        headers = {}
    headers['Accept'] = 'application/json'
    if content:
        headers['Content-Type'] = 'application/json'
    response = await session.request(
        method, path, params=params, headers=headers, json=content)
    content = await response.json()
    error_code = content.get('error_code')
    if error_code:
        raise ResponseError(error_code, content.get('error'))

    return Response(response.status, response.headers, content)
