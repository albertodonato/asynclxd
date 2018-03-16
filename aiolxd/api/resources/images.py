"""API resources for images."""

from ..resource import (
    Resource,
    ResourceCollection,
)


class Image(Resource):
    """API resouce for images."""

    id_attribute = 'fingerprint'

    async def secret(self):
        """Create a secret for this image."""
        response = await self._remote.request('POST', self._uri('secret'))
        from .operations import Operation
        return Operation.from_response(self._remote, response)


class Images(ResourceCollection):
    """Images collection API methods."""

    uri_name = 'images'
    resource_class = Image
