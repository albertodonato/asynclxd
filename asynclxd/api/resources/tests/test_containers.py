import pytest

from ...testing import FakeRemote
from ..containers import (
    Container,
    Logfile,
    Snapshot,
)


@pytest.mark.asyncio
class TestContainer:
    async def test_logs(self):
        """The logs collection returns log files for the container."""
        remote = FakeRemote(responses=[["/containers/c/logs/l.txt"]])
        container = Container(remote, "/containers/c")
        [logfile] = await container.logs.read()
        assert isinstance(logfile, Logfile)
        assert logfile.uri == "/containers/c/logs/l.txt"
        assert remote.calls == [(("GET", "/containers/c/logs", None, None, None, None))]

    async def test_snapshots(self):
        """The snapshots collection returns snapshots for the container."""
        remote = FakeRemote(responses=[["/containers/c/snapshots/s1"]])
        container = Container(remote, "/containers/c")
        [snapshot] = await container.snapshots.read()
        assert isinstance(snapshot, Snapshot)
        assert snapshot.uri == "/containers/c/snapshots/s1"
        assert remote.calls == [
            (("GET", "/containers/c/snapshots", None, None, None, None))
        ]


class TestSnapshot:
    def test_id_from_details_strips_container_name(self):
        """The container name prefix is stripped from the snapshot ID."""
        details = {"name": "container1/snapshot1", "other": "details"}
        assert Snapshot.id_from_details(details) == "snapshot1"
