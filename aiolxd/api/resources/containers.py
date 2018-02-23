"""API resources for containers."""

from ..resource import (
    ResourceCollection,
    NamedResource,
)


class Container(NamedResource):
    """API resource for containers."""


class Containers(ResourceCollection):
    """Containers collection API methods."""

    uri_name = 'containers'
    resource_class = Container
