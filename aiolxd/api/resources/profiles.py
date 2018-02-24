"""API resources for profiles."""

from ..resource import (
    ResourceCollection,
    NamedResource,
)


class Profile(NamedResource):
    """API resource for profiles."""


class Profiles(ResourceCollection):
    """Profiles collection API methods."""

    uri_name = 'profiles'
    resource_class = Profile
