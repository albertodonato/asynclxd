from unittest import (
    TestCase,
    mock,
)

from toolrack.testing.async import LoopTestCase

from ..resource import (
    Collection,
    NamedResource,
    ResourceCollection,
    Resource,
)
from ..request import Response
from ..testing import FakeRemote


class SampleResourceCollection(ResourceCollection):

    uri_name = 'sample-resource'
    resource_class = Resource


class TestCollection(TestCase):

    @mock.patch('aiolxd.api.resources')
    def test_read(self, mock_resources):
        """Getting a collection returns an instance for the remote."""

        class SampleCollection:

            def __init__(self, remote):
                self.remote = remote

        mock_resources.SampleCollection = SampleCollection

        class SampleRemote:

            collection = Collection('SampleCollection')

            def __init__(self):
                self._remote = self

        remote = SampleRemote()
        collection = remote.collection
        self.assertIsInstance(collection, SampleCollection)
        self.assertIs(collection.remote, remote)


class TestResourceCollection(LoopTestCase):

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
            [Resource(remote, '/resources/one'),
             Resource(remote, '/resources/two')])

    async def test_read_raw(self):
        """The read method returns the raw response if raw=True."""
        remote = FakeRemote(responses=[['/resources/one', '/resources/two']])
        collection = SampleResourceCollection(remote, raw=True)
        self.assertEqual(
            await collection.read(), ['/resources/one', '/resources/two'])

    def test_get(self):
        """The get method returns a single resource."""
        collection = SampleResourceCollection(FakeRemote())
        resource = collection.get('a-resource')
        self.assertEqual(resource.uri, '/1.0/sample-resource/a-resource')


class TestResource(LoopTestCase):

    def test_repr(self):
        """The object repr contains the URI."""
        resource = Resource(FakeRemote(), '/resource')
        self.assertEqual(repr(resource), 'Resource(/resource)')

    def test_eq(self):
        """Two resources are equal if they have the same remote and URI."""
        remote = FakeRemote()
        self.assertEqual(
            Resource(remote, '/resource'), Resource(remote, '/resource'))

    def test_eq_false(self):
        """Resources are not equal with different remotes or URI."""
        self.assertNotEqual(
            Resource(FakeRemote(), '/resource1'),
            Resource(FakeRemote, '/resource1'))
        remote = FakeRemote()
        self.assertNotEqual(
            Resource(remote, '/resource1'), Resource(remote, '/resource2'))

    async def test_read(self):
        """The read method makes a GET request for the resource."""
        remote = FakeRemote(responses=['some text'])
        resource = Resource(remote, '/resource')
        response = await resource.read()
        self.assertEqual(response.http_code, 200)
        self.assertEqual(response.metadata, 'some text')
        self.assertEqual(
            remote.calls, [(('GET', '/resource', None, None, None))])

    async def test_read_caches_response(self):
        """The read method caches the response."""
        remote = FakeRemote(responses=['some text'])
        resource = Resource(remote, '/resource')
        self.assertIsNone(resource._response)
        response = await resource.read()
        self.assertIs(resource._response, response)

    async def test_update(self):
        """The update method makes a PATCH request for the resource."""
        remote = FakeRemote(responses=['some text'])
        resource = Resource(remote, '/resource')
        content = {'key': 'value'}
        response = await resource.update(content)
        self.assertEqual(response.http_code, 200)
        self.assertEqual(response.metadata, 'some text')
        self.assertEqual(
            remote.calls, [(('PATCH', '/resource', None, None, content))])

    async def test_update_with_etag(self):
        """The update method includes the ETag if cached."""
        remote = FakeRemote(responses=[{}])
        resource = Resource(remote, '/resource')
        resource._response = Response(200, {'ETag': 'abcde'}, {'key': 'old'})
        content = {'key': 'value'}
        await resource.update(content)
        self.assertEqual(
            remote.calls,
            [(('PATCH', '/resource', None, {'ETag': 'abcde'}, content))])

    async def test_update_with_etag_false(self):
        """The update method doesn't the ETag if not requested."""
        remote = FakeRemote(responses=[{}])
        resource = Resource(remote, '/resource')
        resource._response = Response(200, {'ETag': 'abcde'}, {'key': 'old'})
        content = {'key': 'value'}
        await resource.update(content, etag=False)
        self.assertEqual(
            remote.calls,
            [(('PATCH', '/resource', None, None, content))])

    async def test_replace(self):
        """The replace method makes a PUT request for the resource."""
        remote = FakeRemote(responses=['some text'])
        resource = Resource(remote, '/resource')
        content = {'key': 'value'}
        response = await resource.replace(content)
        self.assertEqual(response.http_code, 200)
        self.assertEqual(response.metadata, 'some text')
        self.assertEqual(
            remote.calls, [(('PUT', '/resource', None, None, content))])

    async def test_replace_with_etag(self):
        """The replace method includes the ETag if cached."""
        remote = FakeRemote(responses=[{}])
        resource = Resource(remote, '/resource')
        resource._response = Response(200, {'ETag': 'abcde'}, {'key': 'old'})
        content = {'key': 'value'}
        await resource.replace(content)
        self.assertEqual(
            remote.calls,
            [(('PUT', '/resource', None, {'ETag': 'abcde'}, content))])

    async def test_replace_with_etag_false(self):
        """The replace method doesn't include the ETag if not requested."""
        remote = FakeRemote(responses=[{}])
        resource = Resource(remote, '/resource')
        resource._response = Response(200, {'ETag': 'abcde'}, {'key': 'old'})
        content = {'key': 'value'}
        await resource.replace(content, etag=False)
        self.assertEqual(
            remote.calls, [(('PUT', '/resource', None, None, content))])

    async def test_delete(self):
        """The delete method makes a DELETE request for the resource."""
        remote = FakeRemote(responses=[{}])
        resource = Resource(remote, '/resource')
        response = await resource.delete()
        self.assertEqual(response.http_code, 200)
        self.assertEqual(response.metadata, {})
        self.assertEqual(
            remote.calls, [(('DELETE', '/resource', None, None, None))])


class TestNamedResource(LoopTestCase):

    async def test_rename(self):
        """A named resource can be renamed."""
        remote = FakeRemote(
            responses=[Response(204, {'Location': '/new-resource'}, {})])
        resource = NamedResource(remote, '/resource')
        response = await resource.rename('new-resource')
        self.assertEqual(response.http_code, 204)
        self.assertEqual(response.metadata, {})
        self.assertEqual(
            remote.calls,
            [(('POST', '/resource', None, None, {'name': 'new-resource'}))])
        self.assertEqual(resource.uri, '/new-resource')