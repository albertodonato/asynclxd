"""API resources for container snapshots."""

from ..resource import (
    ResourceCollection,
    NamedResource,
)


class Snapshot(NamedResource):
    """API resource for container snapshots."""


class Snapshots(ResourceCollection):
    """Snapshots collection API methods."""

    uri_name = 'snapshots'
    resource_class = Snapshot
