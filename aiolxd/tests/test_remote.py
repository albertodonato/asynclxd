from aiohttp import (
    TCPConnector,
    UnixConnector,
)
from toolrack.testing.async import LoopTestCase

from ..api.testing import (
    FakeSession,
    make_sync_response,
)
from ..remote import (
    Remote,
    SessionError,
)


class TestRemote(LoopTestCase):

    def setUp(self):
        super().setUp()
        self.remote = Remote('https://example.com:8443')

    def test_repr(self):
        """The object repr includes the URI."""
        self.assertEqual(
            repr(self.remote), 'Remote(https://example.com:8443/)')

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
        self.addCleanup(self.remote.close())
        self.assertIsNotNone(self.remote._session)

    def test_open_already_in_session(self):
        """A SessionError is raised if already in a session."""
        self.remote.open()
        self.addCleanup(self.remote.close())
        with self.assertRaises(SessionError) as cm:
            self.remote.open()
        self.assertEqual(str(cm.exception), 'Already in a session')

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
        session = FakeSession(responses=[make_sync_response(['response'])])
        self.remote._session_factory = lambda connector=None: session

        async with self.remote:
            response = await self.remote.request('GET', '/')
        self.assertEqual(
            session.calls,
            [('GET', 'https://example.com:8443/', None,
              {'Accept': 'application/json'}, None)])
        self.assertEqual(response.metadata, ['response'])

    async def test_request_with_content(self):
        """Requests can include content."""
        session = FakeSession(responses=[make_sync_response(['response'])])
        self.remote._session_factory = lambda connector=None: session

        content = {'some': 'content'}
        async with self.remote:
            await self.remote.request('POST', '/', content=content)
        self.assertEqual(
            session.calls,
            [('POST', 'https://example.com:8443/', None,
              {'Accept': 'application/json',
               'Content-Type': 'application/json'},
              content)])

    async def test_request_with_params(self):
        """Requests can include params."""
        session = FakeSession(responses=[make_sync_response(['response'])])
        self.remote._session_factory = lambda connector=None: session

        params = {'a': 'param'}
        async with self.remote:
            await self.remote.request('POST', '/', params=params)
        self.assertEqual(
            session.calls,
            [('POST', 'https://example.com:8443/', params,
              {'Accept': 'application/json'}, None)])

    async def test_request_with_headers(self):
        """Requests can include content."""
        session = FakeSession(responses=[make_sync_response(['response'])])
        self.remote._session_factory = lambda connector=None: session

        async with self.remote:
            await self.remote.request(
                'POST', '/', headers={'X-Sample': 'value'})
        self.assertEqual(
            session.calls,
            [('POST', 'https://example.com:8443/', None,
              {'Accept': 'application/json', 'X-Sample': 'value'}, None)])

    async def test_request_not_in_session(self):
        """A SessionError is raised if request is not called in a session."""
        with self.assertRaises(SessionError) as cm:
            await self.remote.request('GET', '/')
        self.assertEqual(str(cm.exception), 'Not in a session')

    async def test_request_relative_path(self):
        """If request path is relative, it's prefixed with the API version."""
        session = FakeSession(responses=[make_sync_response()])
        self.remote._session_factory = lambda connector=None: session

        async with self.remote:
            await self.remote.request('GET', 'relative-path')
        self.assertEqual(
            session.calls,
            [('GET', 'https://example.com:8443/1.0/relative-path', None,
              {'Accept': 'application/json'}, None)])

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
            responses=[make_sync_response(['/1.0', '/2.0'])])
        self.remote._session_factory = lambda connector=None: session

        async with self.remote:
            response = await self.remote.api_versions()
        self.assertEqual(
            session.calls,
            [('GET', 'https://example.com:8443/', None,
              {'Accept': 'application/json'}, None)])
        self.assertEqual(response, ['1.0', '2.0'])

    async def test_info(self):
        """It's possible to query for server information."""
        info = {'api_extensions': ['ext1', 'ext2'], 'api_version': '1.0'}
        session = FakeSession(responses=[make_sync_response(info)])
        self.remote._session_factory = lambda connector=None: session

        async with self.remote:
            response = await self.remote.info()
        self.assertEqual(
            session.calls,
            [('GET', 'https://example.com:8443/1.0', None,
              {'Accept': 'application/json'}, None)])
        self.assertEqual(response, info)
