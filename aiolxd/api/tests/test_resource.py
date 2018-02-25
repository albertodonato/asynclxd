from unittest import TestCase

from toolrack.testing.async import LoopTestCase

from ..request import Response
from ..resource import (
    Collection,
    NamedResource,
    ResourceCollection,
    Resource,
)
from ..testing import (
    FakeRemote,
    make_resource,
)


class SampleResource(Resource):

    id_attribute = 'id'


class SampleResourceCollection(ResourceCollection):

    uri_name = 'sample-resource'
    resource_class = SampleResource


class CollectionTests(TestCase):

    def test_read(self):
        """Getting a collection returns an instance for the remote."""

        class SampleCollection:

            def __init__(self, remote):
                self.remote = remote

        class SampleRemote:

            collection = Collection(SampleCollection)

            def __init__(self):
                self._remote = self

        remote = SampleRemote()
        collection = remote.collection
        self.assertIsInstance(collection, SampleCollection)
        self.assertIs(collection.remote, remote)


class ResourceCollectionTests(LoopTestCase):

    def test_raw(self):
        """The raw method returns a collection with raw attribute set."""
        collection = SampleResourceCollection(FakeRemote())
        self.assertFalse(collection._raw)
        self.assertTrue(collection.raw()._raw)

    async def test_create(self):
        """The create method returns a new instance of resource."""
        response = Response(
            201, {'ETag': 'abcde', 'Location': '/resources/new'},
            {'resource': 'details'})
        remote = FakeRemote(responses=[response])
        collection = SampleResourceCollection(remote)
        resource = await collection.create({'some': 'data'})
        self.assertEqual(resource.uri, '/resources/new')

    async def test_read(self):
        """The read method returns instances of the resource object."""
        remote = FakeRemote(responses=[['/resources/one', '/resources/two']])
        collection = SampleResourceCollection(remote)
        self.assertEqual(
            await collection.read(),
            [SampleResource(remote, '/resources/one'),
             SampleResource(remote, '/resources/two')])

    async def test_recursion(self):
        """The read method returns resources with details if recursive."""
        remote = FakeRemote(
            responses=[[{'id': 'one', 'value': 1}, {'id': 'two', 'value': 2}]])
        collection = SampleResourceCollection(remote)
        resource1, resource2 = await collection.read(recursion=True)
        self.assertEqual(resource1.uri, '/1.0/sample-resource/one')
        self.assertEqual(resource1.details(), {'id': 'one', 'value': 1})
        self.assertEqual(resource2.uri, '/1.0/sample-resource/two')
        self.assertEqual(resource2.details(), {'id': 'two', 'value': 2})

    async def test_read_raw(self):
        """The read method returns the raw response if raw=True."""
        remote = FakeRemote(responses=[['/resources/one', '/resources/two']])
        collection = SampleResourceCollection(remote, raw=True)
        self.assertEqual(
            await collection.read(), ['/resources/one', '/resources/two'])

    async def test_get(self):
        """The get method returns a single resource, reading its details."""
        remote = FakeRemote(responses=[{'some': 'details'}])
        collection = SampleResourceCollection(remote)
        resource = await collection.get('a-resource')
        self.assertEqual(resource.uri, '/1.0/sample-resource/a-resource')
        self.assertEqual(resource.details(), {'some': 'details'})

    async def test_get_quoted_uri(self):
        """The get method quotes quotes special chars in the resource URI."""
        remote = FakeRemote(responses=[{'some': 'details'}])
        collection = SampleResourceCollection(remote)
        resource = await collection.get('a resource')
        self.assertEqual(resource.uri, '/1.0/sample-resource/a%20resource')


class ResourceTests(LoopTestCase):

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

    def test_details_no_cached(self):
        """If no details are cached, details() resutns None."""
        resource = SampleResource(FakeRemote(), '/resource')
        self.assertIsNone(resource.details())

    def test_details(self):
        """If details are cached, details() returns them.."""
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


class NamedResourceTests(LoopTestCase):

    async def test_rename(self):
        """A named resource can be renamed."""
        remote = FakeRemote(
            responses=[Response(204, {'Location': '/new-resource'}, {})])
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
