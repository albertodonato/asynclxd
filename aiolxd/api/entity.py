"""API entities base classes."""

import abc


class Collection:
    """Property to wrap an EntityCollection."""

    def __init__(self, collection_name):
        from . import entities
        self.collection = getattr(entities, collection_name)

    def __get__(self, obj, cls=None):
        return self.collection(obj)


class EntityCollection(metaclass=abc.ABCMeta):
    """A collection for API entities of a type."""

    uri_name = abc.abstractproperty(doc='Name of the collection in the API')
    entity_class = abc.abstractproperty(doc='Class for returned entities')

    def __init__(self, remote, raw=False):
        self._remote = remote
        self._raw = raw

    def raw(self):
        """Return a copy of this collection which returns raw responses."""
        return self.__class__(self._remote, raw=True)

    def get(self, id):
        """Return a single entity in the collection."""
        return self.entity_class(self._remote, self._uri(id=id))

    async def read(self):
        """Return entities for this collection."""
        response = await self._remote.request('GET', self._uri())
        content = response.metadata
        if self._raw:
            return content
        return [self.entity_class(self._remote, uri) for uri in content]

    def _uri(self, id=None):
        uri = '/{version}/{uri_name}'.format(
            version=self._remote.version, uri_name=self.uri_name)
        if id:
            uri += '/{id}'.format(id=id)
        return uri


class Entity:
    """An API entity."""

    def __init__(self, remote, uri):
        self._remote = remote
        self.uri = uri

    def __repr__(self):
        return '{cls}({uri})'.format(cls=self.__class__.__name__, uri=self.uri)

    def __eq__(self, other):
        return (self._remote, self.uri) == (other._remote, other.uri)

    async def read(self):
        """Return details for this entity."""
        return await self._remote.request('GET', self.uri)

    async def delete(self):
        """Delete this entity."""
        return await self._remote.request('DELETE', self.uri)
