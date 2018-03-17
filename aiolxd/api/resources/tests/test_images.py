from toolrack.testing.async import LoopTestCase

from ..images import Image
from ..operations import Operation
from ...http import Response
from ...testing import FakeRemote


class ImageTest(LoopTestCase):

    async def test_read_with_secret(self):
        """It's possible to pass a secret to the read operation."""
        remote = FakeRemote(responses=['some response'])
        image = Image(remote, '/images/i')
        await image.read(secret='abc')
        self.assertEqual(
            remote.calls,
            [(('GET', '/images/i', {'secret': 'abc'}, None, None, None))])

    async def test_secret(self):
        """The secret() call returns an operation with a secret."""
        remote = FakeRemote()
        metadata = {'some': 'details'}
        remote.responses.append(
            Response(
                remote, 202, {'Location': '/operations/op'},
                {'metadata': metadata}))
        image = Image(remote, '/images/i')
        operation = await image.secret()
        self.assertIsInstance(operation, Operation)
        self.assertEqual(operation.uri, '/operations/op')
        self.assertEqual(operation.details(), {'some': 'details'})
        self.assertEqual(
            remote.calls,
            [(('POST', '/images/i/secret', None, None, None, None))])

    async def test_refresh(self):
        """The refresh() call returns an operation for updating an image."""
        remote = FakeRemote()
        metadata = {'some': 'details'}
        remote.responses.append(
            Response(
                remote, 202, {'Location': '/operations/op'},
                {'metadata': metadata}))
        image = Image(remote, '/images/i')
        operation = await image.refresh()
        self.assertIsInstance(operation, Operation)
        self.assertEqual(operation.uri, '/operations/op')
        self.assertEqual(operation.details(), {'some': 'details'})
        self.assertEqual(
            remote.calls,
            [(('POST', '/images/i/refresh', None, None, None, None))])
