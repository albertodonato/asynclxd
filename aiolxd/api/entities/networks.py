"""Network-related entities for the API."""

from ..entity import (
    Entity,
    EntityCollection,
)


class Network(Entity):
    """API entity for networks."""


class Networks(EntityCollection):
    """Networks collection API methods."""

    uri_name = 'networks'
    entity_class = Network
