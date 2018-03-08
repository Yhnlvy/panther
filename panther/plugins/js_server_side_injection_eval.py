# -*- coding:utf-8 -*-

r"""
==========================================================================
P601: Test for use of eval
==========================================================================

Web applications using the JavaScript eval() function to parse the incoming data
without any type of input validation are vulnerable to this attack. An attacker
can inject arbitrary JavaScript code to be executed on the server.


:Example:

    >> Issue: [B324:hashlib_new] Use of insecure MD4 or MD5 hash function.
       Severity: Medium   Confidence: High
       Location: examples/hashlib_new_insecure_funcs.py:3
    2
    3  md5_hash = hashlib.new('md5', string='test')
    4  print(md5_hash)


.. versionadded:: 1.5.0

"""

import bandit
from bandit.core import test_properties as test


def _report(value):
    return bandit.Issue(
        severity=bandit.HIGH,
        confidence=bandit.MEDIUM,
        text=("Potential server side code injection detected: '%s'" % value))

@test.test_id('P601')
@test.checks('CallExpression')
def eval_used(context):
    ''' Try detecting use of eval. Match below patterns:
        1) eval(code)
        2) global.eval(code)
    '''

    try:
        if context.node.callee.name == 'eval':
            return _report("Use of eval(...)")
    except:
        pass

    try:
        if context.node.callee.property.name == 'eval':
            return _report("Use of global.eval(...)")
    except:
        pass




