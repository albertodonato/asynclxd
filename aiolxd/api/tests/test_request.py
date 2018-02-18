from unittest import TestCase

from toolrack.testing.async import LoopTestCase

from ..request import (
    request,
    Response,
    ResponseError,
)
from ..testing import (
    FakeSession,
    make_error_response,
    make_sync_response,
)


class TestRequest(LoopTestCase):

    def setUp(self):
        super().setUp()
        self.session = FakeSession()

    async def test_request(self):
        response = make_sync_response(metadata=['/1.0'])
        self.session.responses.append(response)
        resp = await request(self.session, 'GET', '/')
        self.assertEqual(resp.http_code, 200)
        self.assertEqual(resp.metadata, ['/1.0'])
        self.assertEqual(
            self.session.calls,
            [('GET', '/', {'Content-Type': 'application/json'})])

    async def test_request_error(self):
        response = make_error_response(error='Something went wrong')
        self.session.responses.append(response)
        with self.assertRaises(ResponseError) as cm:
            await request(self.session, 'GET', '/'),
        self.assertEqual(cm.exception.code, 400)
        self.assertEqual(cm.exception.message, 'Something went wrong')
        self.assertEqual(
            str(cm.exception),
            'API request failed with 400: Something went wrong')


class TestResponse(TestCase):

    def test_instantiate(self):
        """A Response can be instantiated."""
        headers = {'Etag': 'abcde'}
        content = {
            'type': 'sync',
            'metadata': {'some': 'content'}}
        response = Response(200, headers, content)
        self.assertEqual(response.http_code, 200)
        self.assertEqual(response.etag, 'abcde')
        self.assertEqual(response.type, 'sync')
        self.assertEqual(response.metadata, {'some': 'content'})
