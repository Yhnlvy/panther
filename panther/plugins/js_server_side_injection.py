# -*- coding:utf-8 -*-

r"""
==========================================================================
P601: Test for use of eval and Function()
==========================================================================

Web applications using the JavaScript eval()function to parse the incoming
data without any type of input validation are vulnerable to this attack. 
An attacker can inject arbitrary JavaScript code to be executed on the server.
Similarly new Function() calls can take code in string format as a last argument
causing same issues as eval().

:Example:

    >> Issue: [P601:eval_used] Potential server side code injection detected: 'Use of eval(...)'
    Severity: High   Confidence: Medium
    Location: examples/server_side_injection.js:2
    1	eval('2*2')
    2	eval('2*2',22, 22, 34)
    3	
    4	global.eval('2*2')

--------------------------------------------------

    >> Issue: [P601:new_function_used] Potential server side code injection detected: 'Use of Function(...)'
    Severity: High   Confidence: Medium
    Location: examples/server_side_injection.js:7
    6	
    7	var sum = new Function('a', 'b', 'return a + b');
    8	var multiply = new Function('x', 'y', 'z', 'return x * y * z');
    9

"""

import panther
from panther.core import test_properties as test
from panther.core.visitor import Identifier


def _report(value):
    return panther.Issue(
        severity=panther.HIGH,
        confidence=panther.MEDIUM,
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
        callee_object = context.node.callee.object
        if context.node.callee.property.name == 'eval' and isinstance(callee_object, Identifier) and callee_object.name == 'global':
            return _report("Use of global.eval(...)")
    except:
        pass

@test.checks('NewExpression') 
@test.test_id('P601')
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
    




