"""API resources for storage."""

from ..resource import (
    NamedResource,
    ResourceCollection,
)


def _related_used_by(remote, entry):
    """Factory returning related storage resources for `used_by`."""
    collections = (remote.containers, remote.images, remote.profiles)
    for collection in collections:
        if entry.startswith(collection.uri):
            return collection.get_resource(entry)
    return entry  # in case the corresponding resource type is not supported


class StoragePool(NamedResource):
    """API resources for storage pools"""

    related_resources = frozenset([(("used_by",), _related_used_by)])

    async def resources(self):
        """Return resources for the storage pool."""
        response = await self._remote.request("GET", self._uri("resources"))
        return response.metadata


class StoragePools(ResourceCollection):
    """Storage pools collection API methods."""

    resource_class = StoragePool
