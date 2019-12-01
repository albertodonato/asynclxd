"""API resources for profiles."""

from ..resource import (
    NamedResource,
    ResourceCollection,
)
from .containers import Container


class Profile(NamedResource):
    """API resource for profiles."""

    related_resources = frozenset([(("used_by",), Container)])


class Profiles(ResourceCollection):
    """Profiles collection API methods."""

    resource_class = Profile
