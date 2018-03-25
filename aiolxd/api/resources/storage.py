"""API resources for storage."""

from .containers import Container
from ..resource import (
    NamedResource,
    ResourceCollection,
)


class StoragePool(NamedResource):
    """API resources for storage pools"""

    related_resources = frozenset([
        (('used_by',), Container),
    ])


class StoragePools(ResourceCollection):
    """Storage pools collection API methods."""

    resource_class = StoragePool
