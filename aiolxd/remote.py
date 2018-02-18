"""A LXD remote."""

from collections import namedtuple
import ssl

from aiohttp import (
    ClientSession,
    TCPConnector,
    UnixConnector,
)
from toolrack.log import Loggable

from .api import (
    Collection,
    request,
)
from .uri import RemoteURI


# Certificates for SSL connection
SSLCerts = namedtuple('SSLCerts', ['server_cert', 'client_cert', 'client_key'])


class Remote(Loggable):
    """LXD server remote."""

    # collection accessors
    containers = Collection('Containers')
    images = Collection('Images')
    networks = Collection('Networks')

    _session_factory = ClientSession  # for testing
    _session = None

    def __init__(self, uri, certs=None, version='1.0'):
        self.uri = RemoteURI(uri)
        self.certs = certs
        self.version = version

    def __repr__(self):
        return '{cls}({uri})'.format(cls=self.__class__.__name__, uri=self.uri)

    async def __aenter__(self):
        self._session = self._session_factory(connector=self._connector())
        return self

    async def __aexit__(self, exc_type, exc, tb):
        await self._session.close()
        self._session = None

    async def api_versions(self):
        """Return a list of available API versions."""
        response = await self.request('GET', '/')
        return [version.lstrip('/') for version in response.metadata]

    async def request(self, method, path):
        """Perform an API request within the session."""
        assert self._session, 'Must be called in a session'
        path = self._full_path(path)
        self.logger.debug('{method} {path}'.format(method=method, path=path))
        return await request(self._session, method, path)

    def _full_path(self, path):
        if not path.startswith('/'):
            path = '/{version}/{path}'.format(version=self.version, path=path)
        return self.uri.request_path(path)

    def _connector(self):
        """Return a connector for the HTTP session."""
        if self.uri.scheme == 'unix':
            return UnixConnector(path=self.uri.path)

        ssl_context = None
        if self.certs:  # pragma: no cover
            ssl_context = ssl.create_default_context(
                purpose=ssl.Purpose.CLIENT_AUTH)
            ssl_context.load_verify_locations(cafile=self.certs.server_cert)
            ssl_context.load_cert_chain(
                self.certs.client_cert, keyfile=self.certs.client_key)
        return TCPConnector(ssl=ssl_context)
