======================================================
asyncLXD - Asynchronous client library for the LXD API
======================================================

|Latest Version| |Build Status| |Coverage Status|

asyncLXD is an asyncio-based client library for the the LXD_ REST API.

It provides an high level API to interact with resources on LXD servers, such
as containers, images, networks, profiles and storage.

LXD servers are accessible through the `asynclxd.remote.Remote` class, which
exposes server details and configuration, as well as access to resource
collections.

Collections (such as `containers`, `images`, `profiles`, `networks`, ...) allow
creating and fetching resources, which can be modified, updated or deleted.

For example:

.. code:: python

    from pprint import pprint

    from asynclxd import lxc

    # get all remotes defined in the client config
    remotes = lxc.get_remotes()
    async with remotes['local'] as remote:
        # fetch all images and print their details
        resp = await remote.images.read()
        for image in resp:
            resp = await image.read()
            pprint(resp.metadata)
            # image details have been read, now they're also cached (same
            # output as above)
            pprint(image.details())

        # fetch a single container by name
        container = await remote.containers.get('c')
        pprint(container.details())
        # rename it
        await container.rename('new-c')
        # change some details
        await container.update({'description': 'foo'})
        # and now delete it
        await container.delete()


.. _LXD: https://linuxcontainers.org/lxd/

.. |Latest Version| image:: https://img.shields.io/pypi/v/asynclxd.svg
   :target: https://pypi.python.org/pypi/asynclxd
.. |Build Status| image:: https://img.shields.io/travis/albertodonato/asynclxd.svg
   :target: https://travis-ci.org/albertodonato/asynclxd
.. |Coverage Status| image:: https://img.shields.io/codecov/c/github/albertodonato/asynclxd/master.svg
   :target: https://codecov.io/gh/albertodonato/asynclxd
.. |Documentation Status| image:: https://readthedocs.org/projects/asynclxd/badge/?version=stable
   :target: https://asynclxd.readthedocs.io/en/stable/?badge=stable
