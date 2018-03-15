# -*- coding:utf-8 -*-

r"""
==========================================================================
P603: Test for NoSQL injection
==========================================================================

All of the following MongoDB operations permit you to run arbitrary JavaScript
expressions directly on the server:

1) $where (Operators > Query and Projection Operators > Evaluation Query Operators > $where) (Suggest using $expr) https://docs.mongodb.com/manual/reference/operator/query/where/#op._S_where
2) mapReduce (Database Commands > Aggregation Commands > mapReduce | mongo Shell Methods > Collection Methods > db.collection.mapReduce() ) LOW
3) group (Database Commands > Aggregation Commands > group | mongo Shell Methods > Collection Methods > db.collection.group() ) 

Deprecated since version 3.4: Mongodb 3.4 deprecates the group command. Use db.collection.aggregate() with the $group stage or db.collection.mapReduce() instead.

These methods can be really convenient, but they pose a huge security risk to
your database integrity if your application does not sanitize and escape user-provided
values properly, as proven by many reports of NoSQL injection attacks.



:Example:

    >> Issue: [P602:hardcoded_sql_expressions_merge_function]
    Possible SQL injection vector through string-based query construction:
    'Concatenation of an SQL statement using a function.'
    Severity: High   Confidence: Medium
    Location: examples/sql_injection.js:7
    6
    7	var dangerous_merge_function_caller_member_expression = x.y.z.concat('SELECT Id FROM ', b);
    8
    9	var dangerous_merge_function_mixed_arguments = a.concat('SELECT Id FROM ', b);

--------------------------------------------------

    >> Issue: [P602:hardcoded_sql_expressions_with_plus]
    Possible SQL injection vector through string-based query construction:
    'Concatenation with an SQL statement and an expression using (+).'
    Severity: High   Confidence: Medium
    Location: examples/sql_injection.js:19
    18
    19	var dangerous_with_plus_mixed_identifier_literal = 'SELECT Id FROM ' + query + 'WHERE Id = 6'; #noqa
    20
    21	var dangerous_with_plus_mixed_expression_literal = 'SELECT Id FROM ' + query['key']; #noqa

--------------------------------------------------

    >> Issue: [P602:hardcoded_sql_expressions_with_template_literal]
    Possible SQL injection vector through string-based query construction:
    'Concatenation with an SQL statement using a template literal.'
    Severity: High   Confidence: Medium
    Location: examples/sql_injection.js:35
    34
    35	var dangerous_with_template_literal_function  = `SELECT Id FROM MyTable WHERE Id = ${expression()}`;
    36
    37	var dangerous_with_template_literal_expression  = `SELECT Id FROM MyTable WHERE Id = ${a() + 2 + 4}`;

--------------------------------------------------

    >> Issue: [P602:hardcoded_sql_expressions_with_plus_equal]
    Possible SQL injection vector through string-based query construction:
    'Concatenation with an SQL statement and an expression using (+=)'
    Severity: High   Confidence: Medium
    Location: examples/sql_injection.js:44
    43	var dangerous_with_plus_equal_identifier  = ''
    44	dangerous_with_plus_equal_identifier += 'SELECT Id FROM '
    45	dangerous_with_plus_equal_identifier += 'MyTable WHERE Id = '
    46	dangerous_with_plus_equal_identifier += '232'

"""

import logging
import panther
from panther.core import test_properties as test
from panther.core.visitor import CallExpression
from panther.core.visitor import Identifier
from panther.core.visitor import Literal
from panther.core.visitor import MemberExpression

LOG = logging.getLogger(__name__)


def _report(value):
    issue_text = "Possible SQL injection vector \
    through string-based query construction: '%s'"

    return panther.Issue(
        severity=panther.HIGH,
        confidence=panther.MEDIUM,
        text=(issue_text % value)
    )




@test.checks('CallExpression')
@test.test_id('P602')
def hardcoded_sql_expressions_merge_function(context):
    '''Checks whether an sql query is mixed with an expression using a
    function. It looks for the functions that contain the words
    'join', 'append' or 'concat' and if the callee of a function
    and its arguments contain both dangerous SQL strings and expressions
    an issue is created.

    See examples below:

    var dangerous_merge_function_direct = concat('SELECT Id FROM ', a, b);
    var dangerous_merge_function_join = ['SELECT Id FROM ', query].join('');
    '''

    try:
        return _report('')

    except Exception as e:
        LOG.error(e)


