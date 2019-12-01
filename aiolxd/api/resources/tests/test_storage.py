import pytest

from ...testing import FakeRemote
from ..containers import (
    Container,
    Containers,
)
from ..images import (
    Image,
    Images,
)
from ..profiles import (
    Profile,
    Profiles,
)
from ..storage import StoragePool


class TestStoragePool:
    @pytest.mark.asyncio
    async def test_related_resources(self):
        """Related resources are returned as instances."""
        remote = FakeRemote()
        # add collections
        remote.containers = Containers(remote, "/containers")
        remote.images = Images(remote, "/images")
        remote.profiles = Profiles(remote, "/profiles")
        storage_pool = StoragePool(remote, "/storage-pools/s")
        storage_pool.update_details(
            {"used_by": ["/containers/c", "/images/i", "/profiles/p"]}
        )
        [container, image, profile] = storage_pool["used_by"]
        assert isinstance(container, Container)
        assert container.uri == "/containers/c"
        assert isinstance(image, Image)
        assert image.uri == "/images/i"
        assert isinstance(profile, Profile)
        assert profile.uri == "/profiles/p"

    @pytest.mark.asyncio
    async def test_related_resources_unknown_kind(self):
        """Related resources URI is returned if resource type is not known."""
        remote = FakeRemote()
        # add collections
        remote.containers = Containers(remote, "/containers")
        remote.images = Images(remote, "/images")
        remote.profiles = Profiles(remote, "/profiles")
        storage_pool = StoragePool(remote, "/storage-pools/s")
        storage_pool.update_details({"used_by": ["/unknown/foo"]})
        [unknown] = storage_pool["used_by"]
        assert unknown == "/unknown/foo"

    @pytest.mark.asyncio
    async def test_resources(self):
        """The resources() call returns details about pool resources."""
        remote = FakeRemote(responses=[{"some": "details"}])
        storage_pool = StoragePool(remote, "/storage-pools/s")
        resources = await storage_pool.resources()
        assert resources == {"some": "details"}
        assert remote.calls == [
            (("GET", "/storage-pools/s/resources", None, None, None, None))
        ]
