from aiohttp import (
    TCPConnector,
    UnixConnector,
)
from toolrack.testing.async import LoopTestCase

from ..api.testing import (
    FakeSession,
    make_sync_response,
)
from ..remote import Remote


class TestRemote(LoopTestCase):

    def test_repr(self):
        """The object repr includes the URI."""
        remote = Remote('https://example.com:8443')
        self.assertEqual(repr(remote), 'Remote(https://example.com:8443/)')

    async def test_context_manager(self):
        """A session is created when using the class as context manager."""
        remote = Remote('https://example.com:8443')
        remote._session_factory = FakeSession

        self.assertIsNone(remote._session)
        async with remote:
            self.assertIsInstance(remote._session, FakeSession)
        self.assertIsNone(remote._session)

    async def test_request(self):
        """Requests can be performed with the server."""
        session = FakeSession(responses=[make_sync_response(['response'])])
        remote = Remote('https://example.com:8443')
        remote._session_factory = lambda connector=None: session

        async with remote:
            response = await remote.request('GET', '/')
        self.assertEqual(
            session.calls,
            [('GET', 'https://example.com:8443/',
              {'Content-Type': 'application/json'})])
        self.assertEqual(response.metadata, ['response'])

    async def test_request_relative_path(self):
        """If request path is relative, it's prefixed with the API version."""
        session = FakeSession(responses=[make_sync_response()])
        remote = Remote('https://example.com:8443')
        remote._session_factory = lambda connector=None: session

        async with remote:
            await remote.request('GET', 'relative-path')
        self.assertEqual(
            session.calls,
            [('GET', 'https://example.com:8443/1.0/relative-path',
              {'Content-Type': 'application/json'})])

    async def test_connector_unix(self):
        """If the URI is for a UNIX socket, a UnixConnector is used."""
        remote = Remote('unix:///socket/path')
        remote._session_factory = FakeSession
        async with remote:
            self.assertIsInstance(remote._session.connector, UnixConnector)
            self.assertEqual(remote._session.connector._path, '/socket/path')

    async def test_connector_https(self):
        """If the URI is https, a TCPConnector is used."""
        remote = Remote('https://example.com:8443')
        remote._session_factory = FakeSession
        async with remote:
            self.assertIsInstance(remote._session.connector, TCPConnector)
            self.assertIsNone(remote._session.connector._ssl)

    async def test_api_versions(self):
        """It's possibel to query for API versions."""
        session = FakeSession(
            responses=[make_sync_response(['/1.0', '/2.0'])])
        remote = Remote('https://example.com:8443')
        remote._session_factory = lambda connector=None: session

        async with remote:
            response = await remote.api_versions()
        self.assertEqual(
            session.calls,
            [('GET', 'https://example.com:8443/',
              {'Content-Type': 'application/json'})])
        self.assertEqual(response, ['1.0', '2.0'])
