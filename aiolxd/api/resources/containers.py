"""API resources for containers."""

from .snapshots import Snapshots
from ..resource import (
    Collection,
    ResourceCollection,
    NamedResource,
)


class Container(NamedResource):
    """API resource for containers."""

    #: Collection property for accessing snapshots.
    snapshots = Collection(Snapshots)


class Containers(ResourceCollection):
    """Containers collection API methods."""

    resource_class = Container
