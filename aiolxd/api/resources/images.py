"""API resources for images."""

from ..resource import (
    Collection,
    NamedResource,
    Resource,
    ResourceCollection,
)


class ImageAlias(NamedResource):
    """API resource for image aliases."""


class ImageAliases(ResourceCollection):
    """Image aliases collection API methods."""

    resource_class = ImageAlias


def related_aliases(remote, details):
    """Factory returning ImageAlias instance from details."""
    return remote.images.aliases.resource_from_details(details)


class Image(Resource):
    """API resouce for images."""

    id_attribute = 'fingerprint'

    related_resources = frozenset([
        (('aliases',), related_aliases),
    ])

    async def read(self, secret=None):
        """Return image details.

        :param str secret: an optional secret in case the client is not
            trusted.

        """
        params = {'secret': secret} if secret else None
        return await self._read(params=params)

    async def secret(self):
        """Create a secret for this image."""
        response = await self._remote.request('POST', self._uri('secret'))
        return response.operation

    async def refresh(self):
        """Refresh a image."""
        response = await self._remote.request('POST', self._uri('refresh'))
        return response.operation


class Images(ResourceCollection):
    """Images collection API methods."""

    resource_class = Image

    #: Collection property for accessing image aliases.
    aliases = Collection(ImageAliases)
