"""API entities base classes."""

import abc


class Collection:
    """Property to wrap an EntityCollection."""

    def __init__(self, collection_name):
        from . import entities
        self.collection = getattr(entities, collection_name)

    def __get__(self, obj, cls=None):
        return self.collection(obj._remote)


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

    _response = None

    def __init__(self, remote, uri):
        self._remote = remote
        self.uri = uri

    def __repr__(self):
        return '{cls}({uri})'.format(cls=self.__class__.__name__, uri=self.uri)

    def __eq__(self, other):
        return (self._remote, self.uri) == (other._remote, other.uri)

    async def read(self):
        """Return details for this entity."""
        self._response = await self._remote.request('GET', self.uri)
        return self._response

    async def update(self, details, etag=True):
        """Update entity details.

        If `etag` is True, Etag header is set with value from last read() call,
        if available.

        """
        headers = self._get_headers(etag=etag)
        return await self._remote.request(
            'PATCH', self.uri, headers=headers, content=details)

    async def replace(self, details, etag=True):
        """Replace entity details.

        If `etag` is True, Etag header is set with value from last read() call,
        if available.

        """
        headers = self._get_headers(etag=etag)
        return await self._remote.request(
            'PUT', self.uri, headers=headers, content=details)

    async def delete(self):
        """Delete this entity."""
        return await self._remote.request('DELETE', self.uri)

    def _get_headers(self, etag=False):
        headers = {}
        if etag and self._response and self._response.etag:
            headers['Etag'] = self._response.etag
        return headers or None
