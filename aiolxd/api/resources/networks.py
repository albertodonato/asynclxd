"""API resources for networks."""

from ..resource import (
    ResourceCollection,
    NamedResource,
)


class Network(NamedResource):
    """API resource for networks."""


class Networks(ResourceCollection):
    """Networks collection API methods."""

    resource_class = Network
