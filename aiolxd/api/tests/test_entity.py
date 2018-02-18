from unittest import (
    TestCase,
    mock,
)

from toolrack.testing.async import LoopTestCase

from ..entity import (
    Collection,
    EntityCollection,
    Entity,
)
from ..testing import FakeRemote


class SampleEntityCollection(EntityCollection):

    uri_name = 'sample-entity'
    entity_class = Entity


class TestCollection(TestCase):

    @mock.patch('aiolxd.api.entities')
    def test_read(self, mock_entities):
        """Getting a collection returns an instance for the remote."""

        class SampleCollection:

            def __init__(self, remote):
                self.remote = remote

        mock_entities.SampleCollection = SampleCollection

        class SampleRemote:

            collection = Collection('SampleCollection')

            def __init__(self):
                self._remote = self

        remote = SampleRemote()
        collection = remote.collection
        self.assertIsInstance(collection, SampleCollection)
        self.assertIs(collection.remote, remote)


class TestEntityCollection(LoopTestCase):

    def test_raw(self):
        """The raw method returns a collection with raw attribute set."""
        collection = SampleEntityCollection(FakeRemote())
        self.assertFalse(collection._raw)
        self.assertTrue(collection.raw()._raw)

    async def test_read(self):
        """The read method returns instances of the entity object."""
        remote = FakeRemote(responses=[['/entities/one', '/entities/two']])
        collection = SampleEntityCollection(remote)
        self.assertEqual(
            await collection.read(),
            [Entity(remote, '/entities/one'), Entity(remote, '/entities/two')])

    async def test_read_raw(self):
        """The read method returns the raw response if raw=True."""
        remote = FakeRemote(responses=[['/entities/one', '/entities/two']])
        collection = SampleEntityCollection(remote, raw=True)
        self.assertEqual(
            await collection.read(), ['/entities/one', '/entities/two'])

    def test_get(self):
        """The get method returns a single entity."""
        collection = SampleEntityCollection(FakeRemote())
        entity = collection.get('a-entity')
        self.assertEqual(entity.uri, '/1.0/sample-entity/a-entity')


class TestEntity(LoopTestCase):

    def test_repr(self):
        """The object repr contains the URI."""
        entity = Entity(FakeRemote(), '/entity')
        self.assertEqual(repr(entity), 'Entity(/entity)')

    def test_eq(self):
        """Two entities are equal if they have the same remote and URI."""
        remote = FakeRemote()
        self.assertEqual(Entity(remote, '/entity'), Entity(remote, '/entity'))

    def test_eq_false(self):
        """Entities are not equal if they have the different remotes or URI."""
        self.assertNotEqual(
            Entity(FakeRemote(), '/entity1'), Entity(FakeRemote, '/entity1'))
        remote = FakeRemote()
        self.assertNotEqual(
            Entity(remote, '/entity1'), Entity(remote, '/entity2'))

    async def test_read(self):
        """The read method makes a GET request for the entity."""
        remote = FakeRemote(responses=['some text'])
        entity = Entity(remote, '/entity')
        response = await entity.read()
        self.assertEqual(response.http_code, 200)
        self.assertEqual(response.metadata, 'some text')
        self.assertEqual(remote.calls, [(('GET', '/entity'))])

    async def test_delete(self):
        """The delete method makes a DELETE request for the entity."""
        remote = FakeRemote(responses=[{}])
        entity = Entity(remote, '/entity')
        response = await entity.delete()
        self.assertEqual(response.http_code, 200)
        self.assertEqual(response.metadata, {})
        self.assertEqual(remote.calls, [(('DELETE', '/entity'))])
