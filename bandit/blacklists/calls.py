# -*- coding:utf-8 -*-

r"""
====================================================
Blacklist various Python calls known to be dangerous
====================================================

This blacklist data checks for a number of Python calls known to have possible
security implications. The following blacklist tests are run against any
function calls encoutered in the scanned code base, triggered by encoutering
ast.Call nodes.

B301: pickle
------------

Pickle library appears to be in use, possible security issue.

+------+---------------------+------------------------------------+-----------+
| ID   |  Name               |  Calls                             |  Severity |
+======+=====================+====================================+===========+
| B301 | pickle              | - pickle.loads                     | Medium    |
|      |                     | - pickle.load                      |           |
|      |                     | - pickle.Unpickler                 |           |
|      |                     | - cPickle.loads                    |           |
|      |                     | - cPickle.load                     |           |
|      |                     | - cPickle.Unpickler                |           |
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
    #build_conf_dict(name, bid, qualnames, message, level='MEDIUM')
    sets.append(utils.build_conf_dict(
        'pickle',
        'B301',
        ['pickle.loads',
         'pickle.load',
         'pickle.Unpickler',
         'cPickle.loads',
         'cPickle.load',
         'cPickle.Unpickler'],
        'Pickle library appears to be in use, possible security issue.' + 'Use of insecure cipher {name}. Replace with a known secure'
        ))

    return {'Call': sets}
