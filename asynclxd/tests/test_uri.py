import pytest

from ..uri import (
    InvalidRemoteURI,
    RemoteURI,
)


class TestRemoteURI:
    def test_uri(self):
        uri = RemoteURI("https://example.com:1234/some/path")
        assert uri.scheme == "https"
        assert uri.host == "example.com"
        assert uri.port == 1234
        assert uri.path == "/some/path"

    def test_unix_socket_default(self):
        """If a path is not specified for UNIX type, default one is used."""
        uri = RemoteURI("unix://")
        assert uri.scheme == "unix"
        assert uri.host is None
        assert uri.path == "/var/lib/lxd/unix.socket"

    @pytest.mark.parametrize(
        "uri,error_message",
        [
            ("https://example.com:not-a-port", "port can't be converted to integer"),
            ("ftp://example.com", "Unsupported scheme"),
            ("unix://hostname/path", "Hostname not allowed for UNIX sockets"),
        ],
    )
    def test_malformed_uri(self, uri, error_message):
        """If URI is malformed an appropriate error is raised."""
        with pytest.raises(InvalidRemoteURI) as error:
            RemoteURI(uri)
        assert error_message in str(error.value)

    def test_str(self):
        """A RemoteURI can be printed as string."""
        uri = RemoteURI("https://example.com:8443")
        assert str(uri) == "https://example.com:8443/"

    def test_repr(self):
        """A RemoteURI can be repr'd."""
        uri = RemoteURI("https://example.com:8443")
        assert repr(uri) == "'https://example.com:8443/'"

    def test_getattr_invalid_attr(self):
        """Accessing an invalid attribute raises an AttributeError."""
        uri = RemoteURI("https://example.com:8443")
        with pytest.raises(AttributeError):
            uri.unknown

    @pytest.mark.parametrize(
        "uri,path,result",
        [
            (
                "https://example.com:8443",
                "/some/url",
                "https://example.com:8443/some/url",
            ),
            ("unix://", "/some/url", "http://local/some/url"),
            (
                "https://example.com:8443",
                "some/url",
                "https://example.com:8443/some/url",
            ),
        ],
    )
    def test_request_path(self, uri, path, result):
        """Request path is returned for an HTTPS URI."""
        assert RemoteURI(uri).request_path(path) == result

    def test_request_uri_with_params(self):
        """If params are provided, they're used in the query string."""
        uri = RemoteURI("https://example.com:8443")
        params = {"foo": "bar", "baz": "x y"}
        assert (
            uri.request_path("some/url", params=params)
            == "https://example.com:8443/some/url?foo=bar&baz=x+y"
        )
