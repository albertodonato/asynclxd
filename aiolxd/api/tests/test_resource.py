from copy import deepcopy
from unittest import TestCase

from asynctest import TestCase as AsyncTestCase

from ..http import Response
from ..resource import (
    Collection,
    NamedResource,
    ResourceCollection,
    Resource,
)
from ..resources.operations import Operation
from ..testing import (
    FakeRemote,
    make_resource,
)


class SampleResource(Resource):

    id_attribute = 'id'


class SampleResourceWithRelated(SampleResource):

    related_resources = frozenset([
        (('foo', 'sample'), SampleResource)
    ])


class SampleResourceCollection(ResourceCollection):

    resource_class = SampleResource


class CollectionTests(TestCase):

    def test_read(self):
        """Getting a collection returns an instance for the remote."""

        class SampleCollection:

            def __init__(self, remote, uri):
                self.remote = remote
                self.uri = uri

        class SampleRemote:

            collection = Collection(SampleCollection)

            def __init__(self):
                self.resource_uri = '/1.0'
                self._remote = self

        remote = SampleRemote()
        collection = remote.collection
        self.assertIsInstance(collection, SampleCollection)
        self.assertIs(collection.remote, remote)
        self.assertEqual(collection.uri, '/1.0/collection')

    def test_read_uri(self):
        """If the  owner doesn't define `resource_uri`, `uri` is used."""

        class SampleCollection:

            def __init__(self, remote, uri):
                self.remote = remote
                self.uri = uri

        class SampleRemote:

            collection = Collection(SampleCollection)

            def __init__(self):
                self.uri = '/1.0'
                self._remote = self

        remote = SampleRemote()
        collection = remote.collection
        self.assertIsInstance(collection, SampleCollection)
        self.assertIs(collection.remote, remote)
        self.assertEqual(collection.uri, '/1.0/collection')


class ResourceCollectionTests(AsyncTestCase):

    def test_repr(self):
        """The object repr contains the URI."""
        resource = SampleResourceCollection(FakeRemote(), '/resources')
        self.assertEqual(
            repr(resource), "SampleResourceCollection('/resources')")

    def test_raw(self):
        """The raw method returns a collection with raw attribute set."""
        collection = SampleResourceCollection(FakeRemote(), '/resources')
        self.assertFalse(collection._raw)
        self.assertTrue(collection.raw()._raw)

    async def test_create(self):
        """The create method returns a new instance of resource."""
        remote = FakeRemote()
        response = Response(
            remote, 201, {'ETag': 'abcde', 'Location': '/resources/new'},
            {'type': 'sync', 'metadata': {'resource': 'details'}})
        remote.responses.append(response)
        collection = SampleResourceCollection(remote, '/resources')
        resource = await collection.create({'some': 'data'})
        self.assertIsInstance(resource, SampleResource)
        self.assertEqual(resource.uri, '/resources/new')

    async def test_create_raw(self):
        """The create method returns raw response metadata if raw=True."""
        metadata = {'resource': 'details'}
        remote = FakeRemote()
        response = Response(
            remote, 201, {'ETag': 'abcde', 'Location': '/resources/new'},
            {'type': 'sync', 'metadata': metadata})
        remote.responses.append(response)
        collection = SampleResourceCollection(remote, '/resources', raw=True)
        result = await collection.create({'some': 'data'})
        self.assertEqual(result, metadata)

    async def test_create_async(self):
        """If the create response is async, the operation is returned."""
        metadata = {'resource': 'details'}
        remote = FakeRemote()
        response = Response(
            remote, 201, {'ETag': 'abcde', 'Location': '/operations/op'},
            {'type': 'async', 'metadata': metadata})
        remote.responses.append(response)
        collection = SampleResourceCollection(remote, '/resources')
        operation = await collection.create({'some': 'data'})
        self.assertIsInstance(operation, Operation)
        self.assertEqual(operation.uri, '/operations/op')
        self.assertEqual(operation.details(), metadata)

    async def test_read(self):
        """The read method returns instances of the resource object."""
        remote = FakeRemote(responses=[['/resources/one', '/resources/two']])
        collection = SampleResourceCollection(remote, '/resources')
        self.assertEqual(
            await collection.read(),
            [SampleResource(remote, '/resources/one'),
             SampleResource(remote, '/resources/two')])

    async def test_read_process_content_override(self):
        """It's possible to further process details from the call result."""
        remote = FakeRemote(responses=[['/resources/one', '/resources/two']])
        collection = SampleResourceCollection(remote, '/resources')

        def process_content(content):
            return ['/new' + entry for entry in content]

        collection._process_content = process_content
        self.assertEqual(
            await collection.read(),
            [SampleResource(remote, '/new/resources/one'),
             SampleResource(remote, '/new/resources/two')])

    async def test_recursion(self):
        """The read method returns resources with details if recursive."""
        remote = FakeRemote(
            responses=[[{'id': 'one', 'value': 1}, {'id': 'two', 'value': 2}]])
        collection = SampleResourceCollection(remote, '/resources')
        resource1, resource2 = await collection.read(recursion=True)
        self.assertEqual(resource1.uri, '/resources/one')
        self.assertEqual(resource1.details(), {'id': 'one', 'value': 1})
        self.assertEqual(resource2.uri, '/resources/two')
        self.assertEqual(resource2.details(), {'id': 'two', 'value': 2})

    async def test_read_raw(self):
        """The read method returns the raw response if raw=True."""
        remote = FakeRemote(responses=[['/resources/one', '/resources/two']])
        collection = SampleResourceCollection(remote, '/resources', raw=True)
        self.assertEqual(
            await collection.read(), ['/resources/one', '/resources/two'])

    def test_get_resource(self):
        """The get_resource method returns a single resource."""
        remote = FakeRemote()
        collection = SampleResourceCollection(remote, '/resources')
        resource = collection.get_resource('a-resource')
        self.assertEqual(resource.uri, '/resources/a-resource')
        # details have not been read
        self.assertIsNone(resource.details())
        self.assertEqual(remote.calls, [])

    async def test_get(self):
        """The get method returns a single resource, reading its details."""
        remote = FakeRemote(responses=[{'some': 'details'}])
        collection = SampleResourceCollection(remote, '/resources')
        resource = await collection.get('a-resource')
        self.assertEqual(resource.uri, '/resources/a-resource')
        # details have been read
        self.assertEqual(resource.details(), {'some': 'details'})
        self.assertEqual(
            remote.calls,
            [('GET', '/resources/a-resource', None, None, None, None)])

    async def test_get_quoted_uri(self):
        """The get method quotes quotes special chars in the resource URI."""
        remote = FakeRemote(responses=[{'some': 'details'}])
        collection = SampleResourceCollection(remote, '/resources')
        resource = await collection.get('a resource')
        self.assertEqual(resource.uri, '/resources/a%20resource')

    def test_resource_from_details(self):
        """A resource instance can be returned from its details."""
        details = {'id': 'res', 'some': 'detail'}
        collection = SampleResourceCollection(FakeRemote(), '/resources')
        resource = collection.resource_from_details(details)
        self.assertIsInstance(resource, SampleResource)
        self.assertEqual(resource.uri, '/resources/res')
        self.assertEqual(resource.details(), details)


class ResourceTests(AsyncTestCase):

    def test_repr(self):
        """The object repr contains the URI."""
        resource = SampleResource(FakeRemote(), '/resource')
        self.assertEqual(repr(resource), "SampleResource('/resource')")

    def test_eq(self):
        """Two resources are equal if they have the same remote and URI."""
        remote = FakeRemote()
        self.assertEqual(
            SampleResource(remote, '/resource'),
            SampleResource(remote, '/resource'))

    def test_eq_false(self):
        """Resources are not equal with different remotes or URI."""
        self.assertNotEqual(
            SampleResource(FakeRemote(), '/resource1'),
            SampleResource(FakeRemote(), '/resource1'))
        remote = FakeRemote()
        self.assertNotEqual(
            SampleResource(remote, '/resource1'),
            SampleResource(remote, '/resource2'))

    def test_getitem_no_response(self):
        """__getitem__ raises KeyError if no response is cached."""
        resource = SampleResource(FakeRemote(), '/resource')
        with self.assertRaises(KeyError):
            resource['foo']

    def test_getitem_with_details(self):
        """__getitem__ raises KeyError if no details are cached."""
        resource = make_resource(SampleResource, details={'some': 'detail'})
        self.assertEqual(resource['some'], 'detail')

    def test_getitem_unknown_attribute(self):
        """__getitem__ raises KeyError if an unknown attribute is requeted."""
        resource = make_resource(SampleResource, details={'key': 'value'})
        with self.assertRaises(KeyError):
            resource['unknown']

    async def test_getitem_returns_copy(self):
        """__getitem__ returns a copy of the details."""
        resource = make_resource(SampleResource, details={'key': ['foo']})
        # modify returned details
        details = resource['key']
        details.append('bar')
        # details in the resource are unchanged
        self.assertEqual(resource['key'], ['foo'])

    def test_deepcopy(self):
        """deepcopy returns a copy of the object."""
        resource = make_resource(
            SampleResource, uri='/res', etag='abcde',
            details={'some': 'detail'})
        copy = deepcopy(resource)
        self.assertEqual(copy.uri, '/res')
        self.assertEqual(copy._last_etag, 'abcde')
        self.assertEqual(copy._details, {'some': 'detail'})
        # details are different objects
        self.assertIsNot(copy._details, resource._details)

    def test_id(self):
        """The id attribute returns the unique identifier of the resource."""
        resource = SampleResource(FakeRemote(), '/resource/myresource')
        self.assertEqual(resource.id, 'myresource')

    def test_id_none(self):
        """If the URI is empty, the ID is None."""
        resource = SampleResource(FakeRemote(), '/')
        self.assertIsNone(resource.id)

    def test_id_with_quoted_chars(self):
        """If the URI contains quoted chars, it's unquoted."""
        resource = SampleResource(FakeRemote(), '/resource/my%20resource')
        self.assertEqual(resource.id, 'my resource')

    def test_id_from_details(self):
        """The id_from_details method returns the ID of the resource."""
        details = {'id': 'res', 'other': 'details'}
        self.assertEqual(SampleResource.id_from_details(details), 'res')

    def test_id_from_details_null_id_attribute(self):
        """If id_attribute=None, id_from_details() raises an error."""

        class SampleResourceWithNullIDAttribute(Resource):

            id_attribute = None

        self.assertRaises(
            ValueError, SampleResourceWithNullIDAttribute.id_from_details,
            {'some': 'details'})

    def test_uri(self):
        """The _uri() method returns a URI below the resource."""
        resource = SampleResource(FakeRemote(), '/resource/myresource')
        self.assertEqual(
            resource._uri('details'), '/resource/myresource/details')

    def test_update_details(self):
        """The update_details() method updates resource details."""
        resource = SampleResource(FakeRemote(), '/resource/myresource')
        details = {'some': 'detail'}
        resource.update_details(details)
        self.assertEqual(resource.details(), details)
        # resource details are copied
        resource._details['some'] = 'other'
        self.assertEqual(details['some'], 'detail')

    def test_update_details_sets_related(self):
        """The update_details() method sets related resources."""
        details = {
            'id': 'res',
            'foo': {'sample': ['/resource/one', '/resource/two']}}
        remote = FakeRemote(responses=[details])
        resource = SampleResourceWithRelated(remote, '/resource-with-related')
        resource.update_details(details)
        related1, related2 = resource['foo']['sample']
        self.assertIsInstance(related1, SampleResource)
        self.assertEqual(related1.uri, '/resource/one')
        self.assertIsInstance(related2, SampleResource)
        self.assertEqual(related2.uri, '/resource/two')

    def test_update_details_reset_etag(self):
        """The update_details() reset last ETag."""
        resource = SampleResource(FakeRemote(), '/resource/myresource')
        resource._last_etag = 'abc'
        resource.update_details({'some': 'detail'})
        self.assertIsNone(resource._last_etag)

    def test_details_no_cached(self):
        """If no details are cached, details() resutns None."""
        resource = SampleResource(FakeRemote(), '/resource')
        self.assertIsNone(resource.details())

    def test_details(self):
        """If details are cached, details() returns them."""
        resource = make_resource(SampleResource, details={'some': 'detail'})
        self.assertEqual(resource.details(), {'some': 'detail'})

    def test_details_returns_copy(self):
        """A copy of the details is returned."""
        resource = make_resource(SampleResource, details={'some': 'detail'})
        # modify returned details
        details = resource.details()
        details['another-key'] = 'another value'
        # details in the resource are unchanged
        self.assertEqual(resource.details(), {'some': 'detail'})

    async def test_read(self):
        """The read method makes a GET request for the resource."""
        remote = FakeRemote(responses=['some text'])
        resource = SampleResource(remote, '/resource')
        response = await resource.read()
        self.assertEqual(response.http_code, 200)
        self.assertEqual(response.metadata, 'some text')
        self.assertEqual(
            remote.calls, [(('GET', '/resource', None, None, None, None))])

    async def test_read_caches_response_details(self):
        """The read method caches response details."""
        remote = FakeRemote(responses=['some text'])
        resource = SampleResource(remote, '/resource')
        self.assertIsNone(resource._details)
        response = await resource.read()
        self.assertEqual(resource._details, response.metadata)

    async def test_read_related_resources(self):
        """Related resources are expanded."""
        details = {
            'id': 'res',
            'foo': {
                'bar': 'baz',
                'sample': ['/resource/one', '/resource/two']}}
        remote = FakeRemote(responses=[details])
        resource = SampleResourceWithRelated(remote, '/resource-with-related')
        await resource.read()
        related1, related2 = resource['foo']['sample']
        self.assertIsInstance(related1, SampleResource)
        self.assertEqual(related1.uri, '/resource/one')
        self.assertIsInstance(related2, SampleResource)
        self.assertEqual(related2.uri, '/resource/two')

    async def test_read_related_resources_not_found(self):
        """If the attribute for related resources is found, it's ignored."""
        details = {'id': 'res'}
        remote = FakeRemote(responses=[details])
        resource = SampleResourceWithRelated(remote, '/resource-with-related')
        await resource.read()
        self.assertEqual(resource.details(), details)

    async def test_read_related_resources_leaf_not_found(self):
        """If leaf attr for related resources is not found, it's ignored."""
        details = {'id': 'res', 'foo': {'bar': 'baz'}}
        remote = FakeRemote(responses=[details])
        resource = SampleResourceWithRelated(remote, '/resource-with-related')
        await resource.read()
        self.assertEqual(resource.details(), details)

    async def test_update(self):
        """The update method makes a PATCH request for the resource."""
        remote = FakeRemote(responses=['some text'])
        resource = SampleResource(remote, '/resource')
        content = {'key': 'value'}
        response = await resource.update(content)
        self.assertEqual(response.http_code, 200)
        self.assertEqual(response.metadata, 'some text')
        self.assertEqual(
            remote.calls,
            [(('PATCH', '/resource', None, None, content, None))])

    async def test_update_with_etag(self):
        """The update method includes the ETag if cached."""
        remote = FakeRemote(responses=[{}])
        resource = SampleResource(remote, '/resource')
        resource._last_etag = 'abcde'
        resource._details = {'some': 'value'}
        content = {'key': 'value'}
        await resource.update(content)
        self.assertEqual(
            remote.calls,
            [(('PATCH', '/resource', None, {'If-Match': 'abcde'},
               content, None))])

    async def test_update_with_etag_false(self):
        """The update method  doesn't use the ETag if not requested."""
        remote = FakeRemote(responses=[{}])
        resource = SampleResource(remote, '/resource')
        resource._last_etag = 'abcde'
        resource._details = {'key': 'old'}
        content = {'key': 'value'}
        await resource.update(content, etag=False)
        self.assertEqual(
            remote.calls,
            [(('PATCH', '/resource', None, None, content, None))])

    async def test_replace(self):
        """The replace method makes a PUT request for the resource."""
        remote = FakeRemote(responses=['some text'])
        resource = SampleResource(remote, '/resource')
        content = {'key': 'value'}
        response = await resource.replace(content)
        self.assertEqual(response.http_code, 200)
        self.assertEqual(response.metadata, 'some text')
        self.assertEqual(
            remote.calls,
            [(('PUT', '/resource', None, None, content, None))])

    async def test_replace_with_etag(self):
        """The replace method includes the ETag if cached."""
        remote = FakeRemote(responses=[{}])
        resource = SampleResource(remote, '/resource')
        resource._last_etag = 'abcde'
        resource._details = {'key': 'old'}
        content = {'key': 'value'}
        await resource.replace(content)
        self.assertEqual(
            remote.calls,
            [(('PUT', '/resource', None, {'If-Match': 'abcde'},
               content, None))])

    async def test_replace_with_etag_false(self):
        """The replace method doesn't include the ETag if not requested."""
        remote = FakeRemote(responses=[{}])
        resource = SampleResource(remote, '/resource')
        resource._last_etag = 'abcde'
        resource._details = {'key': 'old'}
        content = {'key': 'value'}
        await resource.replace(content, etag=False)
        self.assertEqual(
            remote.calls, [(('PUT', '/resource', None, None, content, None))])

    async def test_delete(self):
        """The delete method makes a DELETE request for the resource."""
        remote = FakeRemote(responses=[{}])
        resource = SampleResource(remote, '/resource')
        response = await resource.delete()
        self.assertEqual(response.http_code, 200)
        self.assertEqual(response.metadata, {})
        self.assertEqual(
            remote.calls, [(('DELETE', '/resource', None, None, None, None))])


class NamedResourceTests(AsyncTestCase):

    async def test_rename(self):
        """A named resource can be renamed."""
        remote = FakeRemote()
        response = Response(remote, 204, {'Location': '/new-resource'}, {})
        remote.responses.append(response)
        resource = NamedResource(remote, '/resource')
        resource._details = {'some': 'detail'}
        response = await resource.rename('new-resource')
        self.assertEqual(response.http_code, 204)
        self.assertEqual(response.metadata, {})
        self.assertEqual(
            remote.calls,
            [(('POST', '/resource', None, None,
               {'name': 'new-resource'}, None))])
        self.assertEqual(resource.uri, '/new-resource')
        # cached details are cleared
        self.assertEqual(resource._details, {})
