from toolrack.testing.async import LoopTestCase

from ..images import Image
from ..operations import Operation
from ...http import Response
from ...testing import FakeRemote


class ImageTest(LoopTestCase):

    async def test_secret(self):
        """The secret() call returns an operation with a secret."""
        metadata = {'some': 'details'}
        response = Response(
            202, {'Location': '/operations/op'}, {'metadata': metadata})
        remote = FakeRemote(responses=[response])
        image = Image(remote, '/images/i')
        operation = await image.secret()
        self.assertIsInstance(operation, Operation)
        self.assertEqual(operation.uri, '/operations/op')
        self.assertEqual(operation.details(), {'some': 'details'})
