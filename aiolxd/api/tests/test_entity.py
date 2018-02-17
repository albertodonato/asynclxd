from unittest import (
    TestCase,
    mock,
)

from ..entity import Collection


class TestCollection(TestCase):

    @mock.patch('aiolxd.api.entities')
    def test_get(self, mock_entities):
        """Getting a collection returns an instance for the remote."""

        class SampleCollection:

            def __init__(self, remote):
                self.remote = remote

        mock_entities.SampleCollection = SampleCollection

        class SampleRemote:

            collection = Collection('SampleCollection')

        remote = SampleRemote()
        collection = remote.collection
        self.assertIsInstance(collection, SampleCollection)
        self.assertIs(collection.remote, remote)
