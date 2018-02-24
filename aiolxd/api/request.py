"""Perform requests to the API."""

import os
from pathlib import Path
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
                  content=None, upload=None):
    """Perform an API request with a session

    Parameters:
      - session: the :class:`aiohttp.Session` to perform the request
      - method: the HTTP method
      - path: the request path
      - params: dict with query string parameters
      - headers: additional request headers
      - content: JSON-serializable object for the request content.
      - upload: a :class:`pathlib.Path` or file descriptor for file upload

    """
    if not headers:
        headers = {}
    if content:
        headers['Content-Type'] = 'application/json'
    if upload:
        headers['Content-Type'] = 'application/octet-stream'
        if isinstance(upload, os.PathLike):
            upload = Path(upload).open()
    response = await session.request(
        method, path, params=params, headers=headers, json=content,
        data=upload)
    if upload:
        upload.close()
    content = await response.json()
    error_code = content.get('error_code')
    if error_code:
        raise ResponseError(error_code, content.get('error'))

    return Response(response.status, response.headers, content)
