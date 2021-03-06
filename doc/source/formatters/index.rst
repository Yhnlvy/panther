Panther Report Formatters
========================

Panther supports many different formatters to output various security issues in
Node.js code. These formatters are created as plugins and new ones can be
created to extend the functionality offered by panther today.

Example Formatter
-----------------

.. code-block:: python

    def report(manager, fileobj, sev_level, conf_level, lines=-1):
        result = bson.dumps(issues)
        with fileobj:
            fileobj.write(result)

To register your plugin, you have two options:

1. If you're using setuptools directly, add something like the following to
   your `setup` call::

        # If you have an imaginary bson formatter in the panther_bson module
        # and a function called `formatter`.
        entry_points={'panther.formatters': ['bson = panther_bson:formatter']}

2. If you're using pbr, add something like the following to your `setup.cfg`
   file::

        [entry_points]
        panther.formatters =
            bson = panther_bson:formatter


Complete Formatter Listing
----------------------------

.. toctree::
   :maxdepth: 1
   :glob:

   *
