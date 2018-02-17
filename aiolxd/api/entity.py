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
        return self.entity_class(self._remote, raw=True)

    async def get(self):
        response = await self._remote.request('GET', self._uri())
        if self._raw:
            return response
        return [self.entity_class(self._remote, uri) for uri in response]

    def _uri(self):
        return '/{version}/{uri_name}'.format(
            version=self._remote.version, uri_name=self.uri_name)


class Entity:
    """An API entity."""

    def __init__(self, remote, uri):
        self._remote = remote
        self.uri = uri

    def __repr__(self):
        return '{cls}({uri})'.format(cls=self.__class__.__name__, uri=self.uri)

    async def get(self):
        return await self._remote.request('GET', self.uri)
