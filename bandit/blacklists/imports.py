# -*- coding:utf-8 -*-

r"""
======================================================
Blacklist various Python imports known to be dangerous
======================================================

This blacklist data checks for a number of Python modules known to have
possible security implications. The following blacklist tests are run against
any import statements or calls encountered in the scanned code base.

Note that the XML rules listed here are mostly based off of Christian Heimes'
work on defusedxml: https://pypi.python.org/pypi/defusedxml

B401: import_telnetlib
----------------------

A telnet-related module is being imported. Telnet is considered insecure. Use
SSH or some other encrypted protocol.

+------+---------------------+------------------------------------+-----------+
| ID   |  Name               |  Imports                           |  Severity |
+======+=====================+====================================+===========+
| B401 | import_telnetlib    | - telnetlib                        | high      |
+------+---------------------+------------------------------------+-----------+


"""

from bandit.blacklists import utils


def gen_blacklist():
    """Generate a list of items to blacklist.

    Methods of this type, "bandit.blacklist" plugins, are used to build a list
    of items that bandit's built in blacklisting tests will use to trigger
    issues. They replace the older blacklist* test plugins and allow
    blacklisted items to have a unique bandit ID for filtering and profile
    usage.

    :return: a dictionary mapping node types to a list of blacklist data
    """

    sets = []
    sets.append(utils.build_conf_dict(
        'import_telnetlib', 'B401', ['telnetlib'],
        'A telnet-related module is being imported.  Telnet is '
        'considered insecure. Use SSH or some other encrypted protocol.' + '{name} module.',
        'HIGH'
        ))

    return {'Import': sets, 'ImportFrom': sets, 'Call': sets}
