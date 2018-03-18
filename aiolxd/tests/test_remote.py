from io import StringIO
from pathlib import Path

from aiohttp import (
    TCPConnector,
    UnixConnector,
)
from asynctest import TestCase
from fixtures import TestWithFixtures
from toolrack.testing import TempDirFixture

from ..api.testing import (
    FakeSession,
    make_http_response,
    make_response_content,
)
from ..remote import (
    Remote,
    SessionError,
)


class RemoteTests(TestCase, TestWithFixtures):

    def setUp(self):
        super().setUp()
        self.remote = Remote('https://example.com:8443')

    def test_repr(self):
        """The object repr includes the URI."""
        self.assertEqual(
            repr(self.remote), "Remote('https://example.com:8443/')")

    def test_resource_uri(self):
        """THe resource_uri property returns the base resource URI."""
        self.assertEqual(self.remote.resource_uri, '/1.0')

    async def test_context_manager(self):
        """A session is created when using the class as context manager."""
        self.remote._session_factory = FakeSession

        self.assertIsNone(self.remote._session)
        async with self.remote:
            self.assertIsInstance(self.remote._session, FakeSession)
        self.assertIsNone(self.remote._session)

    async def test_open(self):
        """The open method creates a session."""
        self.remote.open()
        self.assertIsNotNone(self.remote._session)
        await self.remote.close()

    async def test_open_already_in_session(self):
        """A SessionError is raised if already in a session."""
        self.remote.open()
        with self.assertRaises(SessionError) as cm:
            self.remote.open()
        self.assertEqual(str(cm.exception), 'Already in a session')
        await self.remote.close()

    async def test_close(self):
        """The close method ends a session."""
        self.remote.open()
        await self.remote.close()
        self.assertIsNone(self.remote._session)

    async def test_close_not_in_session(self):
        """A SessionError is raised if not a session."""
        with self.assertRaises(SessionError) as cm:
            await self.remote.close()
        self.assertEqual(str(cm.exception), 'Not in a session')

    async def test_request(self):
        """Requests can be performed with the server."""
        session = FakeSession(responses=[make_response_content(['response'])])
        self.remote._session_factory = lambda connector=None: session

        async with self.remote:
            response = await self.remote.request('GET', '/')
        self.assertEqual(
            session.calls,
            [('GET', 'https://example.com:8443', None, {}, None)])
        self.assertEqual(response.metadata, ['response'])

    async def test_request_with_content(self):
        """Requests can include content."""
        session = FakeSession(responses=[make_response_content(['response'])])
        self.remote._session_factory = lambda connector=None: session

        content = {'some': 'content'}
        async with self.remote:
            await self.remote.request('POST', '/', content=content)
        self.assertEqual(
            session.calls,
            [('POST', 'https://example.com:8443', None,
              {'Content-Type': 'application/json'}, content)])

    async def test_request_with_params(self):
        """Requests can include params."""
        session = FakeSession(responses=[make_response_content(['response'])])
        self.remote._session_factory = lambda connector=None: session

        params = {'a': 'param'}
        async with self.remote:
            await self.remote.request('POST', '/', params=params)
        self.assertEqual(
            session.calls,
            [('POST', 'https://example.com:8443', params, {}, None)])

    async def test_remote_with_upload(self):
        """Request can include a file to upload."""
        tempdir = self.useFixture(TempDirFixture())
        upload_file = Path(tempdir.mkfile(content='data'))
        session = FakeSession(responses=[make_response_content(['response'])])
        self.remote._session_factory = lambda connector=None: session

        async with self.remote:
            await self.remote.request('POST', '/', upload=upload_file)
        self.assertEqual(
            session.calls,
            [('POST', 'https://example.com:8443', None,
              {'Content-Type': 'application/octet-stream'}, 'data')])

    async def test_request_with_headers(self):
        """Requests can include content."""
        session = FakeSession(responses=[make_response_content(['response'])])
        self.remote._session_factory = lambda connector=None: session

        async with self.remote:
            await self.remote.request(
                'POST', '/', headers={'X-Sample': 'value'})
        self.assertEqual(
            session.calls,
            [('POST', 'https://example.com:8443', None,
              {'X-Sample': 'value'}, None)])

    async def test_request_binary_response(self):
        """Requests can include content."""
        content = StringIO('some content')
        session = FakeSession(responses=[make_http_response(content=content)])
        self.remote._session_factory = lambda connector=None: session

        out_stream = StringIO()
        async with self.remote:
            response = await self.remote.request('GET', '/')
            await response.write_content(out_stream)
        self.assertEqual(out_stream.getvalue(), 'some content')

    async def test_request_not_in_session(self):
        """A SessionError is raised if request is not called in a session."""
        with self.assertRaises(SessionError) as cm:
            await self.remote.request('GET', '/')
        self.assertEqual(str(cm.exception), 'Not in a session')

    async def test_request_relative_path(self):
        """If request path is relative, it's prefixed with the API version."""
        session = FakeSession(responses=[make_response_content()])
        self.remote._session_factory = lambda connector=None: session

        async with self.remote:
            await self.remote.request('GET', 'relative-path')
        self.assertEqual(
            session.calls,
            [('GET', 'https://example.com:8443/1.0/relative-path', None,
              {}, None)])

    async def test_connector_unix(self):
        """If the URI is for a UNIX socket, a UnixConnector is used."""
        remote = Remote('unix:///socket/path')
        remote._session_factory = FakeSession
        async with remote:
            self.assertIsInstance(remote._session.connector, UnixConnector)
            self.assertEqual(remote._session.connector._path, '/socket/path')

    async def test_connector_https(self):
        """If the URI is https, a TCPConnector is used."""
        self.remote._session_factory = FakeSession
        async with self.remote:
            self.assertIsInstance(
                self.remote._session.connector, TCPConnector)
            self.assertIsNone(self.remote._session.connector._ssl)

    async def test_api_versions(self):
        """It's possible to query for API versions."""
        session = FakeSession(
            responses=[make_response_content(['/1.0', '/2.0'])])
        self.remote._session_factory = lambda connector=None: session

        async with self.remote:
            response = await self.remote.api_versions()
        self.assertEqual(
            session.calls,
            [('GET', 'https://example.com:8443', None, {}, None)])
        self.assertEqual(response, ['1.0', '2.0'])

    async def test_info(self):
        """It's possible to query for server information."""
        info = {'api_extensions': ['ext1', 'ext2'], 'api_version': '1.0'}
        session = FakeSession(responses=[make_response_content(info)])
        self.remote._session_factory = lambda connector=None: session

        async with self.remote:
            response = await self.remote.info()
        self.assertEqual(
            session.calls,
            [('GET', 'https://example.com:8443/1.0', None, {}, None)])
        self.assertEqual(response, info)

    async def test_resources(self):
        """It's possible to query for server resources."""
        resources = {'memory': {'total': 100, 'used': 50}}
        session = FakeSession(responses=[make_response_content(resources)])
        self.remote._session_factory = lambda connector=None: session

        async with self.remote:
            response = await self.remote.resources()
        self.assertEqual(
            session.calls,
            [('GET', 'https://example.com:8443/1.0/resources', None, {},
              None)])
        self.assertEqual(response, resources)

    async def test_config_read(self):
        """It's possible to read the server configuration."""
        info = {
            'config': {'core.https_address': '[]:8443'},
            'api_version': '1.0'}
        session = FakeSession(responses=[make_response_content(info)])
        self.remote._session_factory = lambda connector=None: session

        async with self.remote:
            config = await self.remote.config()
        self.assertEqual(
            session.calls,
            [('GET', 'https://example.com:8443/1.0', None, {}, None)])
        self.assertEqual(config, info['config'])

    async def test_config_update(self):
        """It's possible to update the server configuration."""
        options = {'core.https_address': '[]:8443'}
        session = FakeSession(responses=[make_response_content({})])
        self.remote._session_factory = lambda connector=None: session
        async with self.remote:
            await self.remote.config(options=options)
        self.assertEqual(
            session.calls,
            [('PATCH', 'https://example.com:8443/1.0', None,
              {'Content-Type': 'application/json'}, {'config': options})])

    async def test_config_replace(self):
        """It's possible to replace the server configuration."""
        options = {'core.https_address': '[]:8443'}
        session = FakeSession(responses=[make_response_content({})])
        self.remote._session_factory = lambda connector=None: session
        async with self.remote:
            await self.remote.config(options=options, replace=True)
        self.assertEqual(
            session.calls,
            [('PUT', 'https://example.com:8443/1.0', None,
              {'Content-Type': 'application/json'}, {'config': options})])
