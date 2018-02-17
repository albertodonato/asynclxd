"""Images-related entities for the API."""


class Image:
    """API entity for images."""

    def __init__(self, remote, uri):
        self._remote = remote
        self.uri = uri

    def __repr__(self):
        return 'Image({})'.format(self.uri)

    async def get(self):
        return await self._remote.request('GET', self.uri)


class Images:
    """Images collection API methods."""

    name = 'images'

    def __init__(self, remote, raw=False):
        self._remote = remote
        self._raw = raw

    def raw(self):
        """Return a copy of this collection which returns raw responses."""
        return Images(self._remote, raw=True)

    async def get(self):
        response = await self._remote.request('GET', self._uri())
        if self._raw:
            return response
        return [Image(self._remote, uri) for uri in response]

    def _uri(self):
        return '/{version}/{name}'.format(
            version=self._remote.version, name=self.name)
