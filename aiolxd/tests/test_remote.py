from io import StringIO
from pathlib import Path

from aiohttp import (
    TCPConnector,
    UnixConnector,
)

import pytest

from ..api.resources import Events
from ..api.testing import (
    FakeSession,
    FakeWebSocket,
    FakeWSMessage,
    make_http_response,
    make_response_content,
)
from ..api.websocket import WebsocketHandler
from ..remote import (
    Remote,
    SessionError,
)


@pytest.fixture
def remote(event_loop):
    yield Remote("https://example.com:8443", loop=event_loop)


@pytest.fixture
def make_fake_session(remote):
    def fake_session(_remote=remote, **kwargs):
        session = FakeSession(**kwargs)
        _remote._session_factory = lambda connector=None: session
        return session

    yield fake_session


class TestRemote:
    def test_repr(self, remote):
        """The object repr includes the URI."""
        assert repr(remote) == "Remote('https://example.com:8443/')"

    def test_resource_uri(self, remote):
        """THe resource_uri property returns the base resource URI."""
        assert remote.resource_uri == "/1.0"

    @pytest.mark.asyncio
    async def test_context_manager(self, remote, make_fake_session):
        """A session is created when using the class as context manager."""
        make_fake_session()

        assert remote._session is None
        async with remote:
            assert isinstance(remote._session, FakeSession)
        assert remote._session is None

    @pytest.mark.asyncio
    async def test_open(self, remote):
        """The open method creates a session."""
        remote.open()
        assert remote._session is not None
        await remote.close()

    @pytest.mark.asyncio
    async def test_open_already_in_session(self, remote):
        """A SessionError is raised if already in a session."""
        remote.open()
        with pytest.raises(SessionError) as error:
            remote.open()
        assert str(error.value) == "Already in a session"
        await remote.close()

    @pytest.mark.asyncio
    async def test_close(self, remote):
        """The close method ends a session."""
        remote.open()
        await remote.close()
        assert remote._session is None

    @pytest.mark.asyncio
    async def test_close_not_in_session(self, remote):
        """A SessionError is raised if not a session."""
        with pytest.raises(SessionError) as error:
            await remote.close()
        assert str(error.value) == "Not in a session"

    def test_events(self, remote):
        """The events method returns an Events instance."""
        assert isinstance(remote.events, Events)

    @pytest.mark.asyncio
    async def test_request(self, remote, make_fake_session):
        """Requests can be performed with the server."""
        session = make_fake_session(responses=[make_response_content(["response"])])
        async with remote:
            response = await remote.request("GET", "/")

        assert session.calls == [("GET", "https://example.com:8443", None, {}, None)]
        assert response.metadata == ["response"]

    @pytest.mark.asyncio
    async def test_request_with_content(self, remote, make_fake_session):
        """Requests can include content."""
        session = make_fake_session(responses=[make_response_content(["response"])])
        content = {"some": "content"}
        async with remote:
            await remote.request("POST", "/", content=content)
        assert session.calls == [
            (
                "POST",
                "https://example.com:8443",
                None,
                {"Content-Type": "application/json"},
                content,
            )
        ]

    @pytest.mark.asyncio
    async def test_request_with_params(self, remote, make_fake_session):
        """Requests can include params."""
        session = make_fake_session(responses=[make_response_content(["response"])])
        params = {"a": "param"}
        async with remote:
            await remote.request("POST", "/", params=params)
        assert session.calls == [("POST", "https://example.com:8443", params, {}, None)]

    @pytest.mark.asyncio
    async def test_remote_with_upload(self, tmpdir, remote, make_fake_session):
        """Request can include a file to upload."""
        upload_file = Path(tmpdir / "upload")
        upload_file.write_text("data")
        session = make_fake_session(responses=[make_response_content(["response"])])
        async with remote:
            await remote.request("POST", "/", upload=upload_file)
        assert session.calls == [
            (
                "POST",
                "https://example.com:8443",
                None,
                {"Content-Type": "application/octet-stream"},
                "data",
            )
        ]

    @pytest.mark.asyncio
    async def test_request_with_headers(self, remote, make_fake_session):
        """Requests can include content."""
        session = make_fake_session(responses=[make_response_content(["response"])])
        async with remote:
            await remote.request("POST", "/", headers={"X-Sample": "value"})
        assert session.calls == [
            ("POST", "https://example.com:8443", None, {"X-Sample": "value"}, None)
        ]

    @pytest.mark.asyncio
    async def test_request_binary_response(self, remote, make_fake_session):
        """Requests can include content."""
        content = StringIO("some content")
        make_fake_session(responses=[make_http_response(content=content)])
        out_stream = StringIO()
        async with remote:
            response = await remote.request("GET", "/")
            await response.write_content(out_stream)
        assert out_stream.getvalue() == "some content"

    @pytest.mark.asyncio
    async def test_request_not_in_session(self, remote):
        """A SessionError is raised if request is not called in a session."""
        with pytest.raises(SessionError) as error:
            await remote.request("GET", "/")
        assert str(error.value) == "Not in a session"

    @pytest.mark.asyncio
    async def test_request_relative_path(self, remote, make_fake_session):
        """If request path is relative, it's prefixed with the API version."""
        session = make_fake_session(responses=[make_response_content()])
        async with remote:
            await remote.request("GET", "relative-path")
        assert session.calls == [
            ("GET", "https://example.com:8443/1.0/relative-path", None, {}, None)
        ]

    @pytest.mark.asyncio
    async def test_websocket(self, remote, make_fake_session):
        """Websocket connections can be performed with the server."""
        messages = [FakeWSMessage("foo"), FakeWSMessage("bar")]
        make_fake_session(websocket=FakeWebSocket(messages=messages))

        class SampleHandler(WebsocketHandler):
            def __init__(self):
                self.messages = []

            async def handle_message(self, message):
                self.messages.append(message)

        handler = SampleHandler()
        async with remote:
            await remote.websocket(handler, "/")

        assert handler.messages == ['"foo"', '"bar"']

    @pytest.mark.asyncio
    async def test_websocket_not_in_session(self, remote):
        """A SessionError is raised if websocket is not called in a session."""
        with pytest.raises(SessionError) as error:
            await remote.websocket(object, "/")
        assert str(error.value) == "Not in a session"

    @pytest.mark.asyncio
    async def test_connector_unix(self, make_fake_session):
        """If the URI is for a UNIX socket, a UnixConnector is used."""
        remote = Remote("unix:///socket/path")
        make_fake_session(_remote=remote)
        remote._session_factory = FakeSession
        async with remote:
            assert isinstance(remote._session.connector, UnixConnector)
            assert remote._session.connector._path == "/socket/path"

    @pytest.mark.asyncio
    async def test_connector_https(self, remote):
        """If the URI is https, a TCPConnector is used."""
        async with remote:
            assert isinstance(remote._session.connector, TCPConnector)
            assert remote._session.connector._ssl is None

    @pytest.mark.asyncio
    async def test_api_versions(self, remote, make_fake_session):
        """It's possible to query for API versions."""
        session = make_fake_session(responses=[make_response_content(["/1.0", "/2.0"])])
        async with remote:
            response = await remote.api_versions()
        assert session.calls == [("GET", "https://example.com:8443", None, {}, None)]
        assert response == ["1.0", "2.0"]

    @pytest.mark.asyncio
    async def test_info(self, remote, make_fake_session):
        """It's possible to query for server information."""
        info = {"api_extensions": ["ext1", "ext2"], "api_version": "1.0"}
        session = make_fake_session(responses=[make_response_content(info)])
        async with remote:
            response = await remote.info()
        assert session.calls == [
            ("GET", "https://example.com:8443/1.0", None, {}, None)
        ]
        assert response == info

    @pytest.mark.asyncio
    async def test_resources(self, remote, make_fake_session):
        """It's possible to query for server resources."""
        resources = {"memory": {"total": 100, "used": 50}}
        session = make_fake_session(responses=[make_response_content(resources)])
        async with remote:
            response = await remote.resources()
        assert session.calls == [
            ("GET", "https://example.com:8443/1.0/resources", None, {}, None)
        ]
        assert response == resources

    @pytest.mark.asyncio
    async def test_config_read(self, remote, make_fake_session):
        """It's possible to read the server configuration."""
        info = {"config": {"core.https_address": "[]:8443"}, "api_version": "1.0"}
        session = make_fake_session(responses=[make_response_content(info)])
        async with remote:
            config = await remote.config()
        assert session.calls == [
            ("GET", "https://example.com:8443/1.0", None, {}, None)
        ]
        assert config == info["config"]

    @pytest.mark.asyncio
    async def test_config_update(self, remote, make_fake_session):
        """It's possible to update the server configuration."""
        options = {"core.https_address": "[]:8443"}
        session = make_fake_session(responses=[make_response_content({})])
        async with remote:
            await remote.config(options=options)
        assert session.calls == [
            (
                "PATCH",
                "https://example.com:8443/1.0",
                None,
                {"Content-Type": "application/json"},
                {"config": options},
            )
        ]

    @pytest.mark.asyncio
    async def test_config_replace(self, remote, make_fake_session):
        """It's possible to replace the server configuration."""
        options = {"core.https_address": "[]:8443"}
        session = make_fake_session(responses=[make_response_content({})])
        async with remote:
            await remote.config(options=options, replace=True)
        assert session.calls == [
            (
                "PUT",
                "https://example.com:8443/1.0",
                None,
                {"Content-Type": "application/json"},
                {"config": options},
            )
        ]
