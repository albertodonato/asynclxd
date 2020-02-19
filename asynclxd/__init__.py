"""asyncLXD - asynchronous client library for LXD REST API."""

from distutils.version import LooseVersion

import pkg_resources

__all__ = ["__version__"]

__version__ = LooseVersion(pkg_resources.require("asynclxd")[0].version)
