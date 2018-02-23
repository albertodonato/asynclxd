"""API resources For certificates."""

from ..resource import (
    Resource,
    ResourceCollection,
)


class Certificate(Resource):
    """API resouce for certificates."""

    id_attribute = 'fingerprint'


class Certificates(ResourceCollection):
    """Certificates collection API methods."""

    uri_name = 'certificates'
    resource_class = Certificate
