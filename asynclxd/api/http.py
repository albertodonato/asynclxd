"""Perform requests to the API."""

from abc import ABC
from pathlib import Path
from pprint import pformat

from aiohttp import (
    ClientResponseError,
    StreamReader,
)

from .resources.operations import Operation


class ContentStream(ABC):
    """Abstract base class for classes providing streaming content."""


ContentStream.register(StreamReader)


class UploadFilePath(ABC):
    """Abstract base class for classes providing an upload path."""


UploadFilePath.register(str)
UploadFilePath.register(Path)


class Response:
    """An response to an API request.

    :param asynclxd.remote.Remote remote: the remote that returned the response.
    :param int http_code: the HTTP response code.
    :param dict headers: headers from the HTTP response.
    :param content: the JSON-decoded response content or a stream with the
        binary response content.

    """

    metadata = None

    _content = None

    def __init__(self, remote, http_code, headers, content):
        self._remote = remote
        self.http_code = http_code
        self.etag = headers.get("ETag")
        self.location = headers.get("Location")
        if isinstance(content, ContentStream):
            self._content = content
            self.type = "raw"
        else:
            self.type = content.get("type")
            self.metadata = content.get("metadata", {})

    @property
    def operation(self):
        """Return the background operation from this response, if async."""
        if self.type != "async":
            return None

        operation = Operation(self._remote, self.location)
        operation.update_details(self.metadata)
        return operation

    async def write_content(self, stream):
        """Write the response payload to the specified stream.

        The stream should be open in binary mode.

        """
        if not self._content:
            raise ValueError("No binary payload")

        async for data in self._content.iter_any():
            stream.write(data)

    def pprint(self):
        """Pretty-print the response.

        Return a nicely formatted string with response data for debugging.

        """
        data = {
            "http-code": self.http_code,
            "etag": self.etag,
            "location": self.location,
            "type": self.type,
            "metadata": self.metadata,
        }
        return pformat(data)


class ResponseError(Exception):
    """An API response error.

    :param int code: the response error code.
    :param str message: the response error message.

    """

    def __init__(self, code, message):
        self.code = code
        self.message = message
        super().__init__(f"API request failed with {self.code}: {self.message}")


async def request(
    session, method, path, params=None, headers=None, content=None, upload=None
):
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
        headers["Content-Type"] = "application/json"
    if upload:
        headers["Content-Type"] = "application/octet-stream"
        if isinstance(upload, UploadFilePath):
            upload = Path(upload).open()
    response = await session.request(
        method, path, params=params, headers=headers, json=content, data=upload
    )
    if upload:
        upload.close()

    # check if the request failed
    try:
        response.raise_for_status()
    except ClientResponseError as error:
        error_code = error.status
        error_mesg = error.message
        if error.headers.get("Content-Type") == "application/json":
            content = await response.json()
            error_code = content["error_code"]
            error_mesg = content["error"]
        raise ResponseError(error_code, error_mesg)

    return response
