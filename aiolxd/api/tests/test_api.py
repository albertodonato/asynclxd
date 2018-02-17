from unittest import TestCase

from toolrack.testing.async import LoopTestCase

from .. import (
    Collection,
    request,
    ResponseError,
)
from .testing import (
    FakeSession,
    make_error_response,
    make_sync_response,
)


class TestCollection(TestCase):

    def test_get(self):
        """Getting a collection returns an instance for the remote."""

        class SampleCollection:

            def __init__(self, remote):
                self.remote = remote

        class SampleRemote:

            collection = Collection(SampleCollection)

        remote = SampleRemote()
        collection = remote.collection
        self.assertIsInstance(collection, SampleCollection)
        self.assertIs(collection.remote, remote)


class TestRequest(LoopTestCase):

    def setUp(self):
        super().setUp()
        self.session = FakeSession()

    async def test_request(self):
        response = make_sync_response(metadata=['/1.0'])
        self.session.responses.append(response)
        self.assertEqual(
            await request(self.session, 'GET', '/'),
            ['/1.0'])
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
