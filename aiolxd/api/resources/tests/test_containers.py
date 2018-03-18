from asynctest import TestCase

from ..containers import (
    Container,
    Logfile,
    Snapshot,
)
from ...testing import FakeRemote


class ContainerTest(TestCase):

    async def test_logs(self):
        """The logs collection returns log files for the container."""
        remote = FakeRemote(responses=[['/containers/c/logs/l.txt']])
        container = Container(remote, '/containers/c')
        [logfile] = await container.logs.read()
        self.assertIsInstance(logfile, Logfile)
        self.assertEqual(logfile.uri, '/containers/c/logs/l.txt')
        self.assertEqual(
            remote.calls,
            [(('GET', '/containers/c/logs', None, None, None, None))])

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
