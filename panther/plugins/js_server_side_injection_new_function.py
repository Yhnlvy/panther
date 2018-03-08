# -*- coding:utf-8 -*-

r"""
==========================================================================
P602: Test for use of Function() 
==========================================================================

Web applications using the JavaScript new Function() calls for creating a function
using the incoming data without any type of input validation are vulnerable to this
attack. An attacker can inject arbitrary JavaScript code to be executed on the server
since new Function() calls can take any code in string format as the last argument.

This plugin checks for the patterns below :

new Function ([arg1[, arg2[, ...argN]],] code);


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
from bandit.core.visitor import Identifier


def _report(value):
    return bandit.Issue(
        severity=bandit.HIGH,
        confidence=bandit.MEDIUM,
        text=("Potential server side code injection detected: '%s'" % value))

@test.checks('NewExpression') 
@test.test_id('P602')
def new_function_used(context):
    ''' Try detecting use of new Function() calls. Match below patterns:
        1) new Function(...)
        2) new global.Function(...)
    '''
    try:
        if context.node.callee.name == 'Function':
            return _report("Use of Function(...)")
    except:
        pass

    try:
        callee_object = context.node.callee.object

        if context.node.callee.property.name == 'Function' and isinstance(callee_object, Identifier) and callee_object.name == 'global':
            return _report("Use of global.Function(...)")
    except:
        pass
    



