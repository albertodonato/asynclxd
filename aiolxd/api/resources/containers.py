"""API resources for containers."""

from ..resource import (
    Collection,
    NamedResource,
    Resource,
    ResourceCollection,
)


class Logfile(Resource):
    """API resource for container log files."""

    id_attribute = None


class Logfiles(ResourceCollection):
    """Logfiles collection API methods."""

    resource_class = Logfile

    async def read(self):
        """Return log files for the container."""
        # redefine methos without the recursion parameter, since recursion is
        # not supported here.
        return await super().read()


class Snapshot(NamedResource):
    """API resource for container snapshots."""


class Snapshots(ResourceCollection):
    """Snapshots collection API methods."""

    resource_class = Snapshot


class Container(NamedResource):
    """API resource for containers."""

    #: Collection property for accessing log files.
    logs = Collection(Logfiles)
    #: Collection property for accessing snapshots.
    snapshots = Collection(Snapshots)


class Containers(ResourceCollection):
    """Containers collection API methods."""

    resource_class = Container
