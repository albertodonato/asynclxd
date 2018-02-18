"""Network-related entities for the API."""

from ..entity import (
    EntityCollection,
    NamedEntity,
)


class Network(NamedEntity):
    """API entity for networks."""


class Networks(EntityCollection):
    """Networks collection API methods."""

    uri_name = 'networks'
    entity_class = Network
