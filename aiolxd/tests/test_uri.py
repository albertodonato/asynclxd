from unittest import TestCase

from ..uri import (
    InvalidRemoteURI,
    RemoteURI,
)


class RemoteURITests(TestCase):

    def test_uri(self):
        uri = RemoteURI('https://example.com:1234/some/path')
        self.assertEqual(uri.scheme, 'https')
        self.assertEqual(uri.host, 'example.com')
        self.assertEqual(uri.port, 1234)
        self.assertEqual(uri.path, '/some/path')

    def test_unix_socket_default(self):
        """If a path is not specified for UNIX type, default one is used."""
        uri = RemoteURI('unix://')
        self.assertEqual(uri.scheme, 'unix')
        self.assertEqual(uri.host, None)
        self.assertEqual(uri.path, '/var/lib/lxd/unix.socket')

    def test_invalid_uri(self):
        """An invalid URI raises an error."""
        with self.assertRaises(InvalidRemoteURI) as cm:
            RemoteURI('https://example.com:not-a-port')
        self.assertIn('invalid literal for int', str(cm.exception))

    def test_invalid_scheme(self):
        """Host can't be specified for UNIX socket type."""
        with self.assertRaises(InvalidRemoteURI) as cm:
            RemoteURI('ftp://example.com')
        self.assertIn('Unsupported scheme', str(cm.exception))

    def test_uri_unix_socket_host_invalid(self):
        """Host can't be specified for UNIX socket type."""
        with self.assertRaises(InvalidRemoteURI) as cm:
            RemoteURI('unix://hostname/path')
        self.assertIn(
            'Hostname not allowed for UNIX sockets', str(cm.exception))

    def test_str(self):
        """A RemoteURI can be printed as string."""
        uri = RemoteURI('https://example.com:8443')
        self.assertEqual(str(uri), 'https://example.com:8443/')

    def test_getattr_invalid_attr(self):
        """Accessing an invalid attribute raises an AttributeError."""
        uri = RemoteURI('https://example.com:8443')
        self.assertRaises(AttributeError, getattr, uri, 'unknown')

    def test_request_path_https(self):
        """Request path is returned for an HTTPS URI."""
        uri = RemoteURI('https://example.com:8443')
        self.assertEqual(
            uri.request_path('/some/url'), 'https://example.com:8443/some/url')

    def test_request_path_unix(self):
        """Request path is returned for a UNIX URI."""
        uri = RemoteURI('unix://')
        self.assertEqual(
            uri.request_path('/some/url'), 'http://local/some/url')

    def test_request_uri_no_slash(self):
        """Leading slash is added to the path if not present."""
        uri = RemoteURI('https://example.com:8443')
        self.assertEqual(
            uri.request_path('some/url'), 'https://example.com:8443/some/url')

    def test_request_uri_with_params(self):
        """If params are provided, they're used in the query string."""
        uri = RemoteURI('https://example.com:8443')
        self.assertEqual(
            uri.request_path('some/url', params={'foo': 'bar', 'baz': 'x y'}),
            'https://example.com:8443/some/url?foo=bar&baz=x+y')
