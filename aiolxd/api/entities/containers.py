"""Container-related entities for the API."""

from ..entity import (
    EntityCollection,
    NamedEntity,
)


class Container(NamedEntity):
    """API entity for containers."""


class Containers(EntityCollection):
    """Containers collection API methods."""

    uri_name = 'containers'
    entity_class = Container
