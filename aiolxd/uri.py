"""API URI class."""

from yarl import URL


DEFAULT_UNIX_SOCKET_PATH = '/var/lib/lxd/unix.socket'


class InvalidRemoteURI(Exception):
    """Invalid remote URI."""

    def __init__(self, uri, message):
        super().__init__(
            'Invalid URI {uri}: {message}'.format(uri=uri, message=message))


class RemoteURI:
    """A remote URI.

    Supported URI formats are
     - unix://[socket-path] (default /var/lib/lxd/unix.socket)
     - https://<host>[:port]

    """

    def __init__(self, remote_uri):
        try:
            uri = URL(remote_uri)
        except ValueError as e:
            raise InvalidRemoteURI(remote_uri, str(e))

        if uri.scheme not in ('https', 'unix'):
            raise InvalidRemoteURI(uri, 'Unsupported scheme')
        if uri.scheme == 'unix':
            if uri.host:
                raise InvalidRemoteURI(
                    uri, 'Hostname not allowed for UNIX sockets')
            if not uri.path:
                uri = uri.with_path(DEFAULT_UNIX_SOCKET_PATH)
        self._uri = uri

    def __str__(self):
        loc = 'unix://' if self._uri.scheme == 'unix' else str(self._uri)
        return loc + self._uri.path

    def __repr__(self):
        return repr(str(self))

    def __getattr__(self, attr):
        if attr in ('scheme', 'host', 'port', 'path'):
            return getattr(self._uri, attr)
        raise AttributeError(attr)

    def request_path(self, path, params=None):
        """Return a string suitable for a request."""
        if path.startswith('/'):
            path = path[1:]

        url = URL('http://local') if self.scheme == 'unix' else self._uri
        url = url.with_path(path)
        if params:
            url = url.with_query(params)
        return str(url)
