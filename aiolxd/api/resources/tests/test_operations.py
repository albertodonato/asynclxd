import pytest

from ...testing import FakeRemote
from ..containers import Container
from ..images import Image
from ..operations import (
    Operation,
    Operations,
)


class TestOperation:
    def test_related_resources(self):
        """Related resources are returned as instances."""
        details = {
            "resources": {"containers": ["/containers/c"], "images": ["/images/i"]}
        }
        operation = Operation(FakeRemote(), "/operations/op")
        operation.update_details(details)
        [container] = operation["resources"]["containers"]
        assert isinstance(container, Container)
        assert container.uri == "/containers/c"
        [image] = operation["resources"]["images"]
        assert isinstance(image, Image)
        assert image.uri == "/images/i"

    @pytest.mark.asyncio
    async def test_wait(self):
        """The wait() method waits for operation completion."""
        status = {"id": "foo", "status": "Completed"}
        remote = FakeRemote(responses=[status])
        operation = Operation(remote, "/operations/op")
        response = await operation.wait()
        assert response.metadata == status
        assert remote.calls == [
            (("GET", "/operations/op/wait", None, None, None, None))
        ]
        # the operation status is updated
        assert operation.details() == status

    @pytest.mark.asyncio
    async def test_wait_timeout(self):
        """It's possible to pass a timeout for the wait."""
        status = {"id": "foo", "status": "Completed"}
        remote = FakeRemote(responses=[status])
        operation = Operation(remote, "/operations/op")
        await operation.wait(timeout=20)
        assert remote.calls == [
            (("GET", "/operations/op/wait", {"timeout": 20}, None, None, None))
        ]


class TestOperations:
    @pytest.mark.asyncio
    async def test_read(self):
        """The read method returns opreations in all statuses."""
        remote = FakeRemote(
            responses=[
                {
                    "running": ["/operations/one", "/operations/two"],
                    "queued": ["/operations/three"],
                }
            ]
        )
        collection = Operations(remote, "/operations")
        assert await collection.read() == [
            Operation(remote, "/operations/one"),
            Operation(remote, "/operations/two"),
            Operation(remote, "/operations/three"),
        ]
