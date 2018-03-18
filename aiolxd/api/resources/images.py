"""API resources for images."""

from ..resource import (
    Resource,
    ResourceCollection,
)


class Image(Resource):
    """API resouce for images."""

    id_attribute = 'fingerprint'

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
