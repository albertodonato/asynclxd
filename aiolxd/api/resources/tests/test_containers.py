from unittest import TestCase

from asynctest import TestCase as AsyncTestCase

from ...testing import FakeRemote
from ..containers import (
    Container,
    Logfile,
    Snapshot,
)


class ContainerTests(AsyncTestCase):

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


class SnapshotTests(TestCase):

    def test_id_from_details_strips_container_name(self):
        """The container name prefix is stripped from the snapshot ID."""
        details = {'name': 'container1/snapshot1', 'other': 'details'}
        self.assertEqual(Snapshot.id_from_details(details), 'snapshot1')
