from asynctest import TestCase

from ..containers import (
    Container,
    Snapshot,
)
from ...testing import FakeRemote


class ContainerTest(TestCase):

    async def test_snapshots(self):
        """The snapshots collection returns snapshots for the container."""
        remote = FakeRemote(responses=[['/containers/c/snapshots/s1']])
        container = Container(remote, '/containers/c')
        [snapshot] = await container.snapshots.read()
        self.assertIsInstance(snapshot, Snapshot)
        self.assertEqual(snapshot.uri, '/containers/c/snapshots/s1')
        self.assertEqual(
            remote.calls,
            [(('GET', '/containers/c/snapshots', None, None, None, None))])
