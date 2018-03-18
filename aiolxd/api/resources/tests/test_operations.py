from asynctest import TestCase

from ..containers import Container
from ..images import Image
from ..operations import (
    Operation,
    Operations,
)
from ...testing import FakeRemote


class OperationTest(TestCase):

    def test_related_resources(self):
        """Related resources are returned as instances.."""
        details = {
            'resources': {
                'containers': ['/containers/c'],
                'images': ['/images/i']}}
        operation = Operation(FakeRemote(), '/operations/op')
        operation.update_details(details)
        [container] = operation['resources']['containers']
        self.assertIsInstance(container, Container)
        self.assertEqual(container.uri, '/containers/c')
        [image] = operation['resources']['images']
        self.assertIsInstance(image, Image)
        self.assertEqual(image.uri, '/images/i')

    async def test_wait(self):
        """The wait() method waits for operation completion."""
        status = {'id': 'foo', 'status': 'Completed'}
        remote = FakeRemote(responses=[status])
        operation = Operation(remote, '/operations/op')
        response = await operation.wait()
        self.assertEqual(response.metadata, status)
        self.assertEqual(
            remote.calls,
            [(('GET', '/operations/op/wait', None, None, None, None))])
        # the operation status is updated
        self.assertEqual(operation.details(), status)

    async def test_wait_timeout(self):
        """It's possible to pass a timeout for the wait."""
        status = {'id': 'foo', 'status': 'Completed'}
        remote = FakeRemote(responses=[status])
        operation = Operation(remote, '/operations/op')
        await operation.wait(timeout=20)
        self.assertEqual(
            remote.calls,
            [(('GET', '/operations/op/wait', {'timeout': 20}, None, None,
               None))])


class OperationsTests(TestCase):

    async def test_read(self):
        """The read method returns opreations in all statuses."""
        remote = FakeRemote(responses=[
            {'running': ['/operations/one', '/operations/two'],
             'queued': ['/operations/three']}])
        collection = Operations(remote, '/operations')
        self.assertEqual(
            await collection.read(),
            [Operation(remote, '/operations/one'),
             Operation(remote, '/operations/two'),
             Operation(remote, '/operations/three')])
