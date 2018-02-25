"""Perform requests to the API."""

import os
from pathlib import Path
from pprint import pformat


class Response:
    """An API response.

    :param int http_code: the HTTP response code.
    :param str etag: if included in the response, the Etag header.
    :param str location: if included in the response, the Location header.
    :param content: the JSON-decoded response content.

    """

    def __init__(self, http_code, http_headers, content):
        self.http_code = http_code
        self.etag = http_headers.get('ETag')
        self.location = http_headers.get('Location')
        self.type = content.get('type')
        self.metadata = content.get('metadata', {})

    def pprint(self):
        """Pretty-print the response.

        Return a nicely formatted string with response data for debugging.

        """
        data = {
            'http-code': self.http_code,
            'etag': self.etag,
            'location': self.location,
            'type': self.type,
            'metadata': self.metadata}
        return pformat(data)


class ResponseError(Exception):
    """An API response error.

    :param int code: the response error code.
    :param str message: the response error message.

    """

    def __init__(self, code, message):
        self.code = code
        self.message = message
        super().__init__(
            'API request failed with {code}: {message}'.format(
                code=self.code, message=self.message))


async def request(session, method, path, params=None, headers=None,
                  content=None, upload=None):
    """Perform an API request with a session.

    The Content-Type of the request is set based on whether :data:`content` or
    :data:`upload` are provided.

    :param aiohttp.Session session: the session to perform the request.
    :param str method: the HTTP method.
    :param str path: the request path.
    :param dict params: optional query string parameters.
    :param dict headers: additional request headers.
    :param content: JSON-serializable object for the request content.
    :param upload: a :class:`pathlib.Path` or open file descriptor for file
        upload.

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
