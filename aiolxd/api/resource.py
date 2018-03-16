"""API resources base classes."""

import abc
from copy import deepcopy
from urllib.parse import (
    quote,
    unquote,
)


class Collection:
    """Property to wrap an ResourceCollection."""

    def __init__(self, resource_collection):
        self.resource_collection = resource_collection

    def __get__(self, obj, cls=None):
        return self.resource_collection(obj._remote)


class ResourceCollection(metaclass=abc.ABCMeta):
    """A collection for API resources of a type."""

    uri_name = abc.abstractproperty(doc='Name of the collection in the API')
    resource_class = abc.abstractproperty(doc='Class for returned resources')

    def __init__(self, remote, raw=False):
        self._remote = remote
        self._raw = raw

    def raw(self):
        """Return a copy of this collection which returns raw responses."""
        return self.__class__(self._remote, raw=True)

    async def create(self, details):
        """Create a new resource in the collection."""
        response = await self._remote.request(
            'POST', self._uri(), content=details)
        return self.resource_class(self._remote, response.location)

    async def get(self, id):
        """Return a single resource in the collection.

        This performs a :data:`GET` call to fetch resource details.

        """
        resource = self.resource_class(self._remote, self._uri(id=id))
        await resource.read()
        return resource

    async def read(self, recursion=False):
        """Return resources for this collection.

        If recursion is True, details for resources are fetched in a single
        request.

        """
        params = {'recursion': 1} if recursion else None
        response = await self._remote.request(
            'GET', self._uri(), params=params)
        content = response.metadata
        if self._raw:
            return content

        content = self._process_content(content)
        if recursion:
            return [
                self._resource_from_details(details) for details in content]
        return [self.resource_class(self._remote, uri) for uri in content]

    def _process_content(self, content):
        """Process metadata content before creating resources.

        It should return a list of dicts with resources details.
        By default, it returns the content as it is.

        This can be overridden by subclasses.

        """
        return content

    def _resource_from_details(self, details):
        """Return a resource instance from its details."""
        resource_id = details[self.resource_class.id_attribute]
        resource = self.resource_class(self._remote, self._uri(id=resource_id))
        resource._details = details
        return resource

    def _uri(self, id=None):
        uri = '/{version}/{uri_name}'.format(
            version=self._remote.version, uri_name=self.uri_name)
        if id:
            uri += '/{id}'.format(id=quote(id))
        return uri


class Resource(metaclass=abc.ABCMeta):
    """An API resource."""

    #: Name of the attribute that uniquely identifies this resource
    id_attribute = abc.abstractproperty(
        doc='Attribute that uniquely identifies the resource')

    #: If defined, a sequence of 2-tuples with a tuple of strings identifying a
    # key in resource details and a resource class. Values for the keys are
    # returned as instances of the resource class.
    related_resources = None

    _last_etag = None
    _details = None

    def __init__(self, remote, uri):
        self._remote = remote
        self.uri = uri

    def __repr__(self):
        return '{cls}({uri!r})'.format(
            cls=self.__class__.__name__, uri=self.uri)

    def __eq__(self, other):
        return (self._remote, self.uri) == (other._remote, other.uri)

    def __getitem__(self, item):
        if not self._details:
            raise KeyError(repr(item))
        return deepcopy(self._details[item])

    def __deepcopy__(self, memo):
        copy = self.__class__(self._remote, self.uri)
        copy._last_etag = self._last_etag
        copy._details = deepcopy(self._details, memo)
        return copy

    @property
    def id(self):
        """Return the unique identifier for a resource."""
        value = self.uri.split('/')[-1]
        if value:
            return unquote(value)

    def details(self):
        """Return details about this resource.

        If a previous read() operation has been performed for this resouce,
        details from the response are returned, otherwise :data:`None` is
        returned.

        """
        if not self._details:
            return None

        return deepcopy(self._details)

    async def read(self):
        """Return details for this resource."""
        response = await self._remote.request('GET', self.uri)
        self._set_related_resources(response)
        self._update_cache(response)
        return response

    async def update(self, details, etag=True):
        """Update resource details.

        If `etag` is True, ETag header is set with value from last read() call,
        if available.

        """
        headers = self._get_headers(etag=etag)
        return await self._remote.request(
            'PATCH', self.uri, headers=headers, content=details)

    async def replace(self, details, etag=True):
        """Replace resource details.

        If `etag` is True, ETag header is set with value from last read() call,
        if available.

        """
        headers = self._get_headers(etag=etag)
        return await self._remote.request(
            'PUT', self.uri, headers=headers, content=details)

    async def delete(self):
        """Delete this resource."""
        return await self._remote.request('DELETE', self.uri)

    def _uri(self, path):
        """Return a URI below the resource URI."""
        return '{}/{}'.format(self.uri, path)

    def _get_headers(self, etag=False):
        """Return headers for a request."""
        headers = {}
        if etag and self._last_etag:
            headers['If-Match'] = self._last_etag
        return headers or None

    def _update_cache(self, response):
        """Update cached information from response."""
        self._last_etag = response.etag
        self._details = response.metadata

    def _set_related_resources(self, response):
        """Convert related resoruces URIs to resource instances."""
        if not self.related_resources:
            return

        for keys, resource_class in self.related_resources:
            entry = response.metadata
            # find the attriute in the response
            for key in keys:
                entry = entry.get(key)
                if not entry:
                    break
            if not entry:
                continue
            # replace with resource instances
            for i, resource_uri in enumerate(entry):
                entry[i] = resource_class(self._remote, resource_uri)


class NamedResource(Resource):
    """A resource with a name.

    Named resouces can be renamed via :func:`rename()` call.

    """

    id_attribute = 'name'

    async def rename(self, name):
        """Rename an resource with the specified name.

        This updates the URI of this resource to the new one.

        """
        response = await self._remote.request(
            'POST', self.uri, content={'name': name})
        self._set_related_resources(response)
        self._update_cache(response)
        # URI has changed
        self.uri = response.location
        return response
