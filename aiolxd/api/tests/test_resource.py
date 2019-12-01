from copy import deepcopy

import pytest

from ..http import Response
from ..resource import (
    Collection,
    NamedResource,
    Resource,
    ResourceCollection,
)
from ..resources.operations import Operation
from ..testing import (
    FakeRemote,
    make_resource,
)


class SampleResource(Resource):

    id_attribute = "id"


class SampleResourceWithRelated(SampleResource):

    related_resources = frozenset([(("foo", "sample"), SampleResource)])


class SampleResourceCollection(ResourceCollection):

    resource_class = SampleResource


class TestCollection:
    def test_read(self):
        """Getting a collection returns an instance for the remote."""

        class SampleCollection:
            def __init__(self, remote, uri):
                self.remote = remote
                self.uri = uri

        class SampleRemote:

            collection = Collection(SampleCollection)

            def __init__(self):
                self.resource_uri = "/1.0"
                self._remote = self

        remote = SampleRemote()
        collection = remote.collection
        assert isinstance(collection, SampleCollection)
        assert collection.remote is remote
        assert collection.uri == "/1.0/collection"

    def test_read_uri(self):
        """If the owner doesn't define `resource_uri`, `uri` is used."""

        class SampleCollection:
            def __init__(self, remote, uri):
                self.remote = remote
                self.uri = uri

        class SampleRemote:

            collection = Collection(SampleCollection)

            def __init__(self):
                self.uri = "/1.0"
                self._remote = self

        remote = SampleRemote()
        collection = remote.collection
        assert isinstance(collection, SampleCollection)
        assert collection.remote is remote
        assert collection.uri == "/1.0/collection"

    def test_uri_with_specified_name(self):
        """The uri is build based on Collection name, if provided."""

        class SampleCollection:
            def __init__(self, remote, uri):
                self.remote = remote
                self.uri = uri

        class SampleRemote:

            collection = Collection(SampleCollection, name="c")

            def __init__(self):
                self.resource_uri = "/1.0"
                self._remote = self

        collection = SampleRemote().collection
        assert collection.uri == "/1.0/c"


class TestResourceCollection:
    def test_repr(self):
        """The object repr contains the URI."""
        resource = SampleResourceCollection(FakeRemote(), "/resources")
        assert repr(resource) == "SampleResourceCollection('/resources')"

    def test_raw(self):
        """The raw method returns a collection with raw attribute set."""
        collection = SampleResourceCollection(FakeRemote(), "/resources")
        assert not collection._raw
        assert collection.raw()._raw

    @pytest.mark.asyncio
    async def test_create(self):
        """The create method returns a new instance of resource."""
        remote = FakeRemote()
        response = Response(
            remote,
            201,
            {"ETag": "abcde", "Location": "/resources/new"},
            {"type": "sync", "metadata": {"resource": "details"}},
        )
        remote.responses.append(response)
        collection = SampleResourceCollection(remote, "/resources")
        resource = await collection.create({"some": "data"})
        assert isinstance(resource, SampleResource)
        assert resource.uri == "/resources/new"

    @pytest.mark.asyncio
    async def test_create_raw(self):
        """The create method returns raw response metadata if raw=True."""
        metadata = {"resource": "details"}
        remote = FakeRemote()
        response = Response(
            remote,
            201,
            {"ETag": "abcde", "Location": "/resources/new"},
            {"type": "sync", "metadata": metadata},
        )
        remote.responses.append(response)
        collection = SampleResourceCollection(remote, "/resources", raw=True)
        assert await collection.create({"some": "data"}) == metadata

    @pytest.mark.asyncio
    async def test_create_async(self):
        """If the create response is async, the operation is returned."""
        metadata = {"resource": "details"}
        remote = FakeRemote()
        response = Response(
            remote,
            201,
            {"ETag": "abcde", "Location": "/operations/op"},
            {"type": "async", "metadata": metadata},
        )
        remote.responses.append(response)
        collection = SampleResourceCollection(remote, "/resources")
        operation = await collection.create({"some": "data"})
        assert isinstance(operation, Operation)
        assert operation.uri == "/operations/op"
        assert operation.details() == metadata

    @pytest.mark.asyncio
    async def test_read(self):
        """The read method returns instances of the resource object."""
        remote = FakeRemote(responses=[["/resources/one", "/resources/two"]])
        collection = SampleResourceCollection(remote, "/resources")
        assert await collection.read() == [
            SampleResource(remote, "/resources/one"),
            SampleResource(remote, "/resources/two"),
        ]

    @pytest.mark.asyncio
    async def test_read_process_content_override(self):
        """It's possible to further process details from the call result."""
        remote = FakeRemote(responses=[["/resources/one", "/resources/two"]])
        collection = SampleResourceCollection(remote, "/resources")

        def process_content(content):
            return ["/new" + entry for entry in content]

        collection._process_content = process_content
        assert await collection.read() == [
            SampleResource(remote, "/new/resources/one"),
            SampleResource(remote, "/new/resources/two"),
        ]

    @pytest.mark.asyncio
    async def test_recursion(self):
        """The read method returns resources with details if recursive."""
        remote = FakeRemote(
            responses=[[{"id": "one", "value": 1}, {"id": "two", "value": 2}]]
        )
        collection = SampleResourceCollection(remote, "/resources")
        resource1, resource2 = await collection.read(recursion=True)
        assert resource1.uri == "/resources/one"
        assert resource1.details() == {"id": "one", "value": 1}
        assert resource2.uri == "/resources/two"
        assert resource2.details() == {"id": "two", "value": 2}

    @pytest.mark.asyncio
    async def test_read_raw(self):
        """The read method returns the raw response if raw=True."""
        remote = FakeRemote(responses=[["/resources/one", "/resources/two"]])
        collection = SampleResourceCollection(remote, "/resources", raw=True)
        assert await collection.read() == ["/resources/one", "/resources/two"]

    def test_get_resource(self):
        """The get_resource method returns a single resource."""
        remote = FakeRemote()
        collection = SampleResourceCollection(remote, "/resources")
        resource = collection.get_resource("a-resource")
        assert resource.uri == "/resources/a-resource"
        # details have not been read
        assert resource.details() is None
        assert remote.calls == []

    def test_get_resource_full_uri(self):
        """If the full resource URI is passed, prefix is stripped."""
        remote = FakeRemote()
        collection = SampleResourceCollection(remote, "/resources")
        resource = collection.get_resource("/resources/a-resource")
        assert resource.uri == "/resources/a-resource"

    @pytest.mark.asyncio
    async def test_get(self):
        """The get method returns a single resource, reading its details."""
        remote = FakeRemote(responses=[{"some": "details"}])
        collection = SampleResourceCollection(remote, "/resources")
        resource = await collection.get("a-resource")
        assert resource.uri == "/resources/a-resource"
        # details have been read
        assert resource.details() == {"some": "details"}
        assert remote.calls == [
            ("GET", "/resources/a-resource", None, None, None, None)
        ]

    @pytest.mark.asyncio
    async def test_get_quoted_uri(self):
        """The get method quotes quotes special chars in the resource URI."""
        remote = FakeRemote(responses=[{"some": "details"}])
        collection = SampleResourceCollection(remote, "/resources")
        resource = await collection.get("a resource")
        assert resource.uri == "/resources/a%20resource"

    def test_resource_from_details(self):
        """A resource instance can be returned from its details."""
        details = {"id": "res", "some": "detail"}
        collection = SampleResourceCollection(FakeRemote(), "/resources")
        resource = collection.resource_from_details(details)
        assert isinstance(resource, SampleResource)
        assert resource.uri == "/resources/res"
        assert resource.details() == details


class TestResource:
    def test_repr(self):
        """The object repr contains the URI."""
        resource = SampleResource(FakeRemote(), "/resource")
        assert repr(resource) == "SampleResource('/resource')"

    def test_eq(self):
        """Two resources are equal if they have the same remote and URI."""
        remote = FakeRemote()
        assert SampleResource(remote, "/resource") == SampleResource(
            remote, "/resource"
        )

    def test_eq_false(self):
        """Resources are not equal with different remotes or URI."""
        assert SampleResource(FakeRemote(), "/resource1") != SampleResource(
            FakeRemote(), "/resource1"
        )
        remote = FakeRemote()
        assert SampleResource(remote, "/resource1") != SampleResource(
            remote, "/resource2"
        )

    def test_getitem_no_response(self):
        """__getitem__ raises KeyError if no response is cached."""
        resource = SampleResource(FakeRemote(), "/resource")
        with pytest.raises(KeyError):
            resource["foo"]

    def test_getitem_with_details(self):
        """__getitem__ raises KeyError if no details are cached."""
        resource = make_resource(SampleResource, details={"some": "detail"})
        assert resource["some"] == "detail"

    def test_getitem_unknown_attribute(self):
        """__getitem__ raises KeyError if an unknown attribute is requeted."""
        resource = make_resource(SampleResource, details={"key": "value"})
        with pytest.raises(KeyError):
            resource["unknown"]

    @pytest.mark.asyncio
    async def test_getitem_returns_copy(self):
        """__getitem__ returns a copy of the details."""
        resource = make_resource(SampleResource, details={"key": ["foo"]})
        # modify returned details
        details = resource["key"]
        details.append("bar")
        # details in the resource are unchanged
        assert resource["key"] == ["foo"]

    def test_deepcopy(self):
        """deepcopy returns a copy of the object."""
        resource = make_resource(
            SampleResource, uri="/res", etag="abcde", details={"some": "detail"}
        )
        copy = deepcopy(resource)
        assert copy.uri == "/res"
        assert copy._last_etag == "abcde"
        assert copy._details == {"some": "detail"}
        # details are different objects
        assert copy._details is not resource._details

    @pytest.mark.parametrize(
        "path,resource_id",
        [
            ("/resource/myresource", "myresource"),
            ("/", None),
            ("/resource/my%20resource", "my resource"),
        ],
    )
    def test_id(self, path, resource_id):
        """The id attribute returns the unique identifier of the resource."""
        resource = SampleResource(FakeRemote(), path)
        assert resource.id == resource_id

    def test_id_from_details(self):
        """The id_from_details method returns the ID of the resource."""
        details = {"id": "res", "other": "details"}
        assert SampleResource.id_from_details(details) == "res"

    def test_id_from_details_null_id_attribute(self):
        """If id_attribute=None, id_from_details() raises an error."""

        class SampleResourceWithNullIDAttribute(Resource):

            id_attribute = None

        with pytest.raises(ValueError):
            SampleResourceWithNullIDAttribute.id_from_details({"some": "details"})

    def test_uri(self):
        """The _uri() method returns a URI below the resource."""
        resource = SampleResource(FakeRemote(), "/resource/myresource")
        assert resource._uri("details") == "/resource/myresource/details"

    def test_update_details(self):
        """The update_details() method updates resource details."""
        resource = SampleResource(FakeRemote(), "/resource/myresource")
        details = {"some": "detail"}
        resource.update_details(details)
        assert resource.details() == details
        # resource details are copied
        resource._details["some"] = "other"
        assert details["some"] == "detail"

    def test_update_details_sets_related(self):
        """The update_details() method sets related resources."""
        details = {"id": "res", "foo": {"sample": ["/resource/one", "/resource/two"]}}
        remote = FakeRemote(responses=[details])
        resource = SampleResourceWithRelated(remote, "/resource-with-related")
        resource.update_details(details)
        related1, related2 = resource["foo"]["sample"]
        assert isinstance(related1, SampleResource)
        assert related1.uri == "/resource/one"
        assert isinstance(related2, SampleResource)
        assert related2.uri == "/resource/two"

    def test_update_details_reset_etag(self):
        """The update_details() reset last ETag."""
        resource = SampleResource(FakeRemote(), "/resource/myresource")
        resource._last_etag = "abc"
        resource.update_details({"some": "detail"})
        assert resource._last_etag is None

    def test_details_no_cached(self):
        """If no details are cached, details() resutns None."""
        resource = SampleResource(FakeRemote(), "/resource")
        assert resource.details() is None

    def test_details(self):
        """If details are cached, details() returns them."""
        resource = make_resource(SampleResource, details={"some": "detail"})
        assert resource.details() == {"some": "detail"}

    def test_details_returns_copy(self):
        """A copy of the details is returned."""
        resource = make_resource(SampleResource, details={"some": "detail"})
        # modify returned details
        details = resource.details()
        details["another-key"] = "another value"
        # details in the resource are unchanged
        assert resource.details() == {"some": "detail"}

    @pytest.mark.asyncio
    async def test_read(self):
        """The read method makes a GET request for the resource."""
        remote = FakeRemote(responses=["some text"])
        resource = SampleResource(remote, "/resource")
        response = await resource.read()
        assert response.http_code == 200
        assert response.metadata == "some text"
        assert remote.calls == [(("GET", "/resource", None, None, None, None))]

    @pytest.mark.asyncio
    async def test_read_caches_response_details(self):
        """The read method caches response details."""
        remote = FakeRemote(responses=["some text"])
        resource = SampleResource(remote, "/resource")
        assert resource._details is None
        response = await resource.read()
        assert resource._details == response.metadata

    @pytest.mark.asyncio
    async def test_read_related_resources(self):
        """Related resources are expanded."""
        details = {
            "id": "res",
            "foo": {"bar": "baz", "sample": ["/resource/one", "/resource/two"]},
        }
        remote = FakeRemote(responses=[details])
        resource = SampleResourceWithRelated(remote, "/resource-with-related")
        await resource.read()
        related1, related2 = resource["foo"]["sample"]
        assert isinstance(related1, SampleResource)
        assert related1.uri == "/resource/one"
        assert isinstance(related2, SampleResource)
        assert related2.uri == "/resource/two"

    @pytest.mark.asyncio
    async def test_read_related_resources_not_found(self):
        """If the attribute for related resources is found, it's ignored."""
        details = {"id": "res"}
        remote = FakeRemote(responses=[details])
        resource = SampleResourceWithRelated(remote, "/resource-with-related")
        await resource.read()
        assert resource.details() == details

    @pytest.mark.asyncio
    async def test_read_related_resources_leaf_not_found(self):
        """If leaf attr for related resources is not found, it's ignored."""
        details = {"id": "res", "foo": {"bar": "baz"}}
        remote = FakeRemote(responses=[details])
        resource = SampleResourceWithRelated(remote, "/resource-with-related")
        await resource.read()
        assert resource.details() == details

    @pytest.mark.asyncio
    async def test_update(self):
        """The update method makes a PATCH request for the resource."""
        remote = FakeRemote(responses=["some text"])
        resource = SampleResource(remote, "/resource")
        content = {"key": "value"}
        response = await resource.update(content)
        assert response.http_code == 200
        assert response.metadata == "some text"
        assert remote.calls == [(("PATCH", "/resource", None, None, content, None))]

    @pytest.mark.asyncio
    async def test_update_with_etag(self):
        """The update method includes the ETag if cached."""
        remote = FakeRemote(responses=[{}])
        resource = SampleResource(remote, "/resource")
        resource._last_etag = "abcde"
        resource._details = {"some": "value"}
        content = {"key": "value"}
        await resource.update(content)
        assert remote.calls == [
            (("PATCH", "/resource", None, {"If-Match": "abcde"}, content, None))
        ]

    @pytest.mark.asyncio
    async def test_update_with_etag_false(self):
        """The update method  doesn't use the ETag if not requested."""
        remote = FakeRemote(responses=[{}])
        resource = SampleResource(remote, "/resource")
        resource._last_etag = "abcde"
        resource._details = {"key": "old"}
        content = {"key": "value"}
        await resource.update(content, etag=False)
        assert remote.calls == [(("PATCH", "/resource", None, None, content, None))]

    @pytest.mark.asyncio
    async def test_replace(self):
        """The replace method makes a PUT request for the resource."""
        remote = FakeRemote(responses=["some text"])
        resource = SampleResource(remote, "/resource")
        content = {"key": "value"}
        response = await resource.replace(content)
        assert response.http_code == 200
        assert response.metadata == "some text"
        assert remote.calls == [(("PUT", "/resource", None, None, content, None))]

    @pytest.mark.asyncio
    async def test_replace_with_etag(self):
        """The replace method includes the ETag if cached."""
        remote = FakeRemote(responses=[{}])
        resource = SampleResource(remote, "/resource")
        resource._last_etag = "abcde"
        resource._details = {"key": "old"}
        content = {"key": "value"}
        await resource.replace(content)
        assert remote.calls == [
            (("PUT", "/resource", None, {"If-Match": "abcde"}, content, None))
        ]

    @pytest.mark.asyncio
    async def test_replace_with_etag_false(self):
        """The replace method doesn't include the ETag if not requested."""
        remote = FakeRemote(responses=[{}])
        resource = SampleResource(remote, "/resource")
        resource._last_etag = "abcde"
        resource._details = {"key": "old"}
        content = {"key": "value"}
        await resource.replace(content, etag=False)
        assert remote.calls == [(("PUT", "/resource", None, None, content, None))]

    @pytest.mark.asyncio
    async def test_delete(self):
        """The delete method makes a DELETE request for the resource."""
        remote = FakeRemote(responses=[{}])
        resource = SampleResource(remote, "/resource")
        response = await resource.delete()
        assert response.http_code == 200
        assert response.metadata == {}
        assert remote.calls == [(("DELETE", "/resource", None, None, None, None))]


class TestNamedResource:
    @pytest.mark.asyncio
    async def test_rename(self):
        """A named resource can be renamed."""
        remote = FakeRemote()
        response = Response(remote, 204, {"Location": "/new-resource"}, {})
        remote.responses.append(response)
        resource = NamedResource(remote, "/resource")
        resource._details = {"some": "detail"}
        response = await resource.rename("new-resource")
        assert response.http_code == 204
        assert response.metadata == {}
        assert remote.calls == [
            (("POST", "/resource", None, None, {"name": "new-resource"}, None))
        ]
        assert resource.uri == "/new-resource"
        # cached details are cleared
        assert resource._details == {}
