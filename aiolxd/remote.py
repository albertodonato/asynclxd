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
    resources,
)
from .uri import RemoteURI


# Certificates for SSL connection
SSLCerts = namedtuple('SSLCerts', ['server_cert', 'client_cert', 'client_key'])


class SessionError(Exception):
    """Remote session is invalid."""


class Remote(Loggable):
    """LXD server remote."""

    #: Collection for accessing certificates
    certificates = Collection(resources.Certificates)
    #: Collection for accessing containers
    containers = Collection(resources.Containers)
    #: Collection for accessing images
    images = Collection(resources.Images)
    #: Collection for accessing networks
    networks = Collection(resources.Networks)
    #: Collection for accessing profiles
    profiles = Collection(resources.Profiles)

    _session_factory = ClientSession  # for testing
    _session = None

    def __init__(self, uri, certs=None, version='1.0'):
        self.uri = RemoteURI(uri)
        self.certs = certs
        self.version = version
        self._remote = self

    def __repr__(self):
        return '{cls}({uri!r})'.format(
            cls=self.__class__.__name__, uri=self.uri)

    async def __aenter__(self):
        self.open()
        return self

    async def __aexit__(self, exc_type, exc, tb):
        await self.close()

    def open(self):
        """Start a session with the remote."""
        if self._session:
            raise SessionError('Already in a session')
        self._session = self._session_factory(connector=self._connector())

    async def close(self):
        """Terminate the session with the remote."""
        if not self._session:
            raise SessionError('Not in a session')
        await self._session.close()
        self._session = None

    async def api_versions(self):
        """Return a list of available API versions."""
        # use absolute URI so that the version is not included
        response = await self.request('GET', '/')
        return [version.lstrip('/') for version in response.metadata]

    async def info(self):
        """Return a dict with information about the server configuration."""
        response = await self.request('GET', '')
        return response.metadata

    async def request(self, method, path, params=None, headers=None,
                      content=None, upload=None):
        """Perform an API request within the session.

        Parameters:
          - method: the HTTP method
          - path: the request path
          - params: dict with query string parameters
          - headers: additional request headers
          - content: JSON-serializable object for the request content.
          - upload: a :class:`pathlib.Path` or file descriptor for file upload

        """
        if not self._session:
            raise SessionError('Not in a session')

        path = self._full_path(path)
        self.logger.debug('{method} {path}'.format(
            method=method, path=self._full_path(path, params=params)))
        return await request(
            self._session, method, path, params=params, headers=headers,
            content=content, upload=upload)

    def _full_path(self, path, params=None):
        """Return the full path for a request."""
        if not path:
            path = '/' + self.version
        elif not path.startswith('/'):
            path = '/{version}/{path}'.format(version=self.version, path=path)
        return self.uri.request_path(path, params=params)

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
