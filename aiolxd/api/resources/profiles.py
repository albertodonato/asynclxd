"""API resources for profiles."""

from .containers import Container
from ..resource import (
    ResourceCollection,
    NamedResource,
)


class Profile(NamedResource):
    """API resource for profiles."""

    related_resources = frozenset([
        (('used_by',), Container),
    ])


class Profiles(ResourceCollection):
    """Profiles collection API methods."""

    uri_name = 'profiles'
    resource_class = Profile
