"""A LXD remote."""

import ssl
from urllib.parse import (
    ParseResult,
    urlparse,
)

from aiohttp import (
    ClientSession,
    TCPConnector,
    UnixConnector,
)

from .api import parse_response


DEFAULT_UNIX_SOCKET_PATH = '/var/lib/lxd/unix.socket'


class InvalidRemoteURI(Exception):
    """Invalid remote URI."""

    def __init__(self, uri):
        super().__init__('Invalid remote URI: {}'.format(uri))


class Remote:
    """LXD server remote."""

    _ssl_cert = None
    _ssl_key = None
    _session = None

    def __init__(self, uri, ssl_cert_pair=None):
        self.uri = parse_remote_uri(uri)
        if ssl_cert_pair:
            self._ssl_cert, self._ssl_key = ssl_cert_pair

    async def __aenter__(self):
        self._session = ClientSession(connector=self._connector())
        return self

    async def __aexit__(self, exc_type, exc, tb):
        await self._session.close()

    async def request(self, method, path, data=None):
        """Performa an API request."""
        assert self._session, 'Must be called in a session'
        path = self._request_path(path)
        headers = {'Content-Type': 'application/json'}
        resp = await self._session.request(method, path, headers=headers)
        return parse_response(await resp.json())

    def _connector(self):
        if self.uri.scheme == 'unix':
            return UnixConnector(path=self.uri.path)

        ssl_context = None
        if self._ssl_cert:
            ssl_context = ssl.create_default_context(
                purpose=ssl.Purpose.CLIENT_AUTH)
            ssl_context.load_cert_chain(self._ssl_cert, keyfile=self._ssl_key)

        return TCPConnector(ssl_context=ssl_context)

    def _request_path(self, path):
        if not path.startswith('/'):
            path = '/' + path

        if self.uri.scheme == 'unix':
            host = 'http://localhost'
        else:
            host = '{}://{}'.format(self.uri.scheme, self.uri.netloc)
        return host + path


def parse_remote_uri(uri):
    """Parse a remote URI."""
    parsed = urlparse(uri)
    if parsed.scheme not in ('https', 'unix'):
        raise InvalidRemoteURI(uri)
    if parsed.scheme == 'unix' and not parsed.path:
        frags = list(parsed)
        frags[2] = DEFAULT_UNIX_SOCKET_PATH
        parsed = ParseResult(*frags)
    return parsed
