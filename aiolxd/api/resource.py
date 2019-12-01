"""API resources base classes."""

import abc
from copy import deepcopy
from urllib.parse import (
    quote,
    unquote,
)


class Collection:
    """Property to wrap an ResourceCollection.

    :param ResourceCollection resource_collection: the resource collection
        to wrap.
    :param str name: the name of the collection in the API (if not specified,
        the name of the attribute for the Collection is used).

    """

    def __init__(self, resource_collection, name=""):
        self.resource_collection = resource_collection
        self.name = name

    def __set_name__(self, owner, name):
        if not self.name:
            # if the name is not set, use the attribute name
            self.name = name

    def __get__(self, instance, owner):
        base_uri = getattr(instance, "resource_uri", None)
        if not base_uri:
            base_uri = instance.uri
        uri = f"{base_uri}/{self.name}"
        return self.resource_collection(instance._remote, uri)


class ResourceCollection(metaclass=abc.ABCMeta):
    """A collection for API resources of a type."""

    resource_class = abc.abstractproperty(doc="Class for returned resources")

    def __init__(self, remote, uri, raw=False):
        self._remote = remote
        self.uri = uri
        self._raw = raw

    def __repr__(self):
        return f"{self.__class__.__name__}({repr(self.uri)})"

    def raw(self):
        """Return a copy of this collection which returns raw responses."""
        return self.__class__(self._remote, self.uri, raw=True)

    async def create(self, details):
        """Create a new resource in the collection."""
        response = await self._remote.request("POST", self.uri, content=details)
        if self._raw:
            return response.metadata
        if response.operation:
            # the creation operation is async
            return response.operation
        return self.resource_class(self._remote, response.location)

    def get_resource(self, id):
        """Return a resource with the specified ID."""
        return self.resource_class(self._remote, self._resource_uri(id))

    async def get(self, id):
        """Return a single resource in the collection.

        This performs a :data:`GET` call to fetch resource details.

        """
        resource = self.get_resource(id)
        await resource.read()
        return resource

    async def read(self, recursion=False):
        """Return resources for this collection.

        If recursion is True, details for resources are fetched in a single
        request.

        """
        params = {"recursion": 1} if recursion else None
        response = await self._remote.request("GET", self.uri, params=params)
        content = response.metadata
        if self._raw:
            return content

        content = self._process_content(content)
        if recursion:
            return [self.resource_from_details(details) for details in content]
        return [self.resource_class(self._remote, uri) for uri in content]

    def resource_from_details(self, details):
        """Return an instance of a resource for the collection from details."""
        resource_id = self.resource_class.id_from_details(details)
        resource = self.resource_class(self._remote, self._resource_uri(resource_id))
        resource.update_details(details)
        return resource

    def _process_content(self, content):
        """Process metadata content before creating resources.

        It should return a list of dicts with resources details.
        By default, it returns the content as it is.

        This can be overridden by subclasses.

        """
        return content

    def _resource_uri(self, resource_id):
        if resource_id.startswith(self.uri):
            # strip prefix
            resource_id = resource_id[len(self.uri) + 1 :]
        return f"{self.uri}/{quote(resource_id)}"


class Resource(metaclass=abc.ABCMeta):
    """An API resource."""

    #: Name of the attribute that uniquely identifies this resource
    id_attribute = abc.abstractproperty(
        doc="Attribute that uniquely identifies the resource"
    )

    #: If defined, a sequence of 2-tuples with a tuple of strings identifying a
    # key in resource details and a resource factory. The factory can be a
    # resource subclass (when details are just the resource URI) or a callable
    # which is called with the remote and resource details.  Values for the
    # keys are returned as instances of the resource class.
    related_resources = None

    _last_etag = None
    _details = None

    def __init__(self, remote, uri):
        self._remote = remote
        self.uri = uri

    def __repr__(self):
        return f"{self.__class__.__name__}({repr(self.uri)})"

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
        value = self.uri.split("/")[-1]
        if value:
            return unquote(value)

    @classmethod
    def id_from_details(cls, details):
        """Return the ID for a resource from details."""
        if not cls.id_attribute:
            raise ValueError("Resource has no ID attribute")
        return details[cls.id_attribute]

    def update_details(self, details):
        """Update deatils for the resource."""
        self._last_etag = None  # reset ETag
        self._details = deepcopy(details)
        self._set_related_resources(self._details)

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
        return await self._read()

    async def update(self, details, etag=True):
        """Update resource details.

        If `etag` is True, ETag header is set with value from last read() call,
        if available.

        """
        headers = self._get_headers(etag=etag)
        return await self._remote.request(
            "PATCH", self.uri, headers=headers, content=details
        )

    async def replace(self, details, etag=True):
        """Replace resource details.

        If `etag` is True, ETag header is set with value from last read() call,
        if available.

        """
        headers = self._get_headers(etag=etag)
        return await self._remote.request(
            "PUT", self.uri, headers=headers, content=details
        )

    async def delete(self):
        """Delete this resource."""
        return await self._remote.request("DELETE", self.uri)

    async def _read(self, params=None):
        """Return details for the resource.

        :param dict params: an optional dict with query string parameters for
            the request.

        """
        response = await self._remote.request("GET", self.uri, params=params)
        self._process_response(response)
        return response

    def _uri(self, path):
        """Return a URI below the resource URI."""
        return f"{self.uri}/{path}"

    def _get_headers(self, etag=False):
        """Return headers for a request."""
        headers = {}
        if etag and self._last_etag:
            headers["If-Match"] = self._last_etag
        return headers or None

    def _process_response(self, response):
        """Process response with resource details."""
        self._last_etag = response.etag
        self._set_related_resources(response.metadata)
        self._details = deepcopy(response.metadata)

    def _set_related_resources(self, metadata):
        """Convert related resoruces to resource instances."""
        if not self.related_resources or not metadata:
            return

        for keys, resource_factory in self.related_resources:
            parent_entry = entry = metadata
            # find the attriute in the response
            for key in keys:
                parent_entry = entry
                entry = entry.get(key)
                if not entry:
                    break
            if not entry:
                continue
            # replace with resource instances
            if isinstance(entry, list):
                for i, resource_entry in enumerate(entry):
                    entry[i] = resource_factory(self._remote, resource_entry)
            else:
                parent_entry[key] = resource_factory(self._remote, entry)


class NamedResource(Resource):
    """A resource with a name.

    Named resouces can be renamed via :func:`rename()` call.

    """

    id_attribute = "name"

    async def rename(self, name):
        """Rename an resource with the specified name.

        This updates the URI of this resource to the new one.

        """
        response = await self._remote.request("POST", self.uri, content={"name": name})
        self._process_response(response)
        # URI has changed
        self.uri = response.location
        return response
