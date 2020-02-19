import pytest

from ...http import Response
from ...testing import FakeRemote
from ..images import (
    Image,
    ImageAlias,
    Images,
)
from ..operations import Operation


class TestImageAlias:
    @pytest.mark.asyncio
    async def test_related_resources(self):
        """Related resources are returned as instances."""
        remote = FakeRemote()
        # add the images collection
        remote.images = Images(remote, "/images")
        alias = ImageAlias(remote, "/images/aliases/a")
        alias.update_details({"name": "a", "target": "img"})
        image = alias["target"]
        assert isinstance(image, Image)
        assert image.uri == "/images/img"


@pytest.mark.asyncio
class TestImage:
    async def test_related_resources(self):
        """Related resources are returned as instances."""
        alias_details = {"name": "a", "description": "an alias"}
        details = {"aliases": [alias_details]}
        remote = FakeRemote()
        # add the images collection
        remote.images = Images(remote, "/images")
        image = Image(remote, "/images/i")
        image.update_details(details)
        [alias] = image["aliases"]
        assert isinstance(alias, ImageAlias)
        assert alias.uri == "/images/aliases/a"
        assert alias.details() == alias_details

    async def test_read_with_secret(self):
        """It's possible to pass a secret to the read operation."""
        remote = FakeRemote(responses=[{"some": "details"}])
        image = Image(remote, "/images/i")
        await image.read(secret="abc")
        assert remote.calls == [
            (("GET", "/images/i", {"secret": "abc"}, None, None, None))
        ]

    async def test_secret(self):
        """The secret() call returns an operation with a secret."""
        remote = FakeRemote()
        metadata = {"some": "details"}
        remote.responses.append(
            Response(
                remote,
                202,
                {"Location": "/operations/op"},
                {"type": "async", "metadata": metadata},
            )
        )
        image = Image(remote, "/images/i")
        operation = await image.secret()
        assert isinstance(operation, Operation)
        assert operation.uri == "/operations/op"
        assert operation.details() == {"some": "details"}
        assert remote.calls == [(("POST", "/images/i/secret", None, None, None, None))]

    async def test_refresh(self):
        """The refresh() call returns an operation for updating an image."""
        remote = FakeRemote()
        metadata = {"some": "details"}
        remote.responses.append(
            Response(
                remote,
                202,
                {"Location": "/operations/op"},
                {"type": "async", "metadata": metadata},
            )
        )
        image = Image(remote, "/images/i")
        operation = await image.refresh()
        assert isinstance(operation, Operation)
        assert operation.uri == "/operations/op"
        assert operation.details() == {"some": "details"}
        assert remote.calls == [(("POST", "/images/i/refresh", None, None, None, None))]


class TestImages:
    @pytest.mark.asyncio
    async def test_aliases(self):
        """The aliases collection returns image aliases."""
        remote = FakeRemote(responses=[["/images/aliases/a/one", "/images/aliases/b"]])
        collection = Images(remote, "/images")
        [alias1, alias2] = await collection.aliases.read()
        assert isinstance(alias1, ImageAlias)
        assert alias1.uri == "/images/aliases/a/one"
        assert isinstance(alias2, ImageAlias)
        assert alias2.uri == "/images/aliases/b"
        assert remote.calls == [(("GET", "/images/aliases", None, None, None, None))]
