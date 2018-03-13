# -*- coding:utf-8 -*-

import panther
from panther.core import test_properties as test


def _report(value):
    return panther.Issue(
        severity=panther.LOW,
        confidence=panther.MEDIUM,
        text=("How dare you? eval()? Really?: '%s'" % value))


@test.checks('CallExpression')
@test.test_id('P106')
def never_ever_ever_use_eval(context):
    """*P106: To be removed"""
    # looks for "function(candidate='some_string')"
    try:
        if context.node.callee.name == 'eval':
            return _report("eval()")
    except Exception:
        pass
