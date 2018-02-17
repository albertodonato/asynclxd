"""Images-related entities for the API."""

from ..entity import (
    Entity,
    EntityCollection,
)


class Image(Entity):
    """API entity for images."""


class Images(EntityCollection):
    """Images collection API methods."""

    uri_name = 'images'
    entity_class = Image
