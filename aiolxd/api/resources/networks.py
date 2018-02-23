"""API resources for networks."""

from ..resource import (
    ResourceCollection,
    NamedResource,
)


class Network(NamedResource):
    """API resource for networks."""


class Networks(ResourceCollection):
    """Networks collection API methods."""

    uri_name = 'networks'
    resource_class = Network
