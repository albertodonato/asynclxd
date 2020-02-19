"""API resources for networks."""

from ..resource import (
    NamedResource,
    ResourceCollection,
)


class Network(NamedResource):
    """API resource for networks."""


class Networks(ResourceCollection):
    """Networks collection API methods."""

    resource_class = Network
