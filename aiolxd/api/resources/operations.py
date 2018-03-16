"""API resources for asynchronous operations.."""

from itertools import chain

from .containers import Container
from .images import Image
from ..resource import (
    Resource,
    ResourceCollection,
)


class Operation(Resource):
    """API resouce for operations."""

    id_attribute = 'id'

    related_resources = frozenset([
        (('resources', 'containers'), Container),
        (('resources', 'images'), Image)
        # XXX add "cluster" once resources is supported
    ])

    @classmethod
    def from_response(cls, remote, response):
        operation = cls(remote, response.location)
        operation.update_details(response.metadata)
        return operation

    async def wait(self, timeout=None):
        params = {'timeout': timeout} if timeout else None
        response = await self._remote.request(
            'GET', self._uri('wait'), params=params)
        self._process_response(response)
        return response


class Operations(ResourceCollection):
    """Operations collection API methods."""

    uri_name = 'operations'
    resource_class = Operation

    def _process_content(self, content):
        # Operations listing returns a dict keyed by operation status.
        return list(chain(*content.values()))
