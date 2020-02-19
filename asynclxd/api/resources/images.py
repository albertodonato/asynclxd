"""API resources for images."""

from ..resource import (
    Collection,
    NamedResource,
    Resource,
    ResourceCollection,
)


def _related_image(remote, fingerprint):
    """Factory returning an Image instance from fingerprint."""
    return remote.images.get_resource(fingerprint)


class ImageAlias(NamedResource):
    """API resource for image aliases."""

    related_resources = frozenset([(("target",), _related_image)])


class ImageAliases(ResourceCollection):
    """Image aliases collection API methods."""

    resource_class = ImageAlias


def _related_alias(remote, details):
    """Factory returning an ImageAlias instance from details."""
    return remote.images.aliases.resource_from_details(details)


class Image(Resource):
    """API resouce for images."""

    id_attribute = "fingerprint"

    related_resources = frozenset([(("aliases",), _related_alias)])

    async def read(self, secret=None):
        """Return image details.

        :param str secret: an optional secret in case the client is not
            trusted.

        """
        params = {"secret": secret} if secret else None
        return await self._read(params=params)

    async def secret(self):
        """Create a secret for this image."""
        response = await self._remote.request("POST", self._uri("secret"))
        return response.operation

    async def refresh(self):
        """Refresh a image."""
        response = await self._remote.request("POST", self._uri("refresh"))
        return response.operation


class Images(ResourceCollection):
    """Images collection API methods."""

    resource_class = Image

    #: Collection property for accessing image aliases.
    aliases = Collection(ImageAliases)
