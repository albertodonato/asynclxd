"""API resources for containers."""

from ..resource import (
    Collection,
    ResourceCollection,
    NamedResource,
)


class Snapshot(NamedResource):
    """API resource for container snapshots."""


class Snapshots(ResourceCollection):
    """Snapshots collection API methods."""

    uri_name = 'snapshots'
    resource_class = Snapshot


class Container(NamedResource):
    """API resource for containers."""

    #: Collection property for accessing snapshots.
    snapshots = Collection(Snapshots)


class Containers(ResourceCollection):
    """Containers collection API methods."""

    resource_class = Container
