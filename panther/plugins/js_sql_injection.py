# -*- coding:utf-8 -*-

r"""
==========================================================================
P602: Test for SQL injection
==========================================================================

An SQL injection attack consists of insertion or "injection" of a SQL query via
the input data given to an application. It is a very common attack vector. This
plugin test looks for strings that resemble SQL statements that are involved in
some form of string building operation. For example:

 - 'SELECT Id FROM ' + query + 'WHERE Id = 6';
 - concat('SELECT Id FROM ', a, b);
 - ['SELECT Id FROM ', query].join('');
 - `SELECT Id FROM MyTable WHERE Id = ${a() + 2 + 4}`;
 - dangerous_with_plus_equal_identifier += 'SELECT Id FROM ';

Unless care is taken to sanitize and control the input data when building such
SQL statement strings, an injection attack becomes possible. If strings of this
nature are discovered, an issue is reported.

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
import json
import panther
from panther.core import test_properties as test
from panther.core.visitor import ArrayExpression
from panther.core.visitor import Identifier
from panther.core.visitor import Literal
from panther.core.visitor import MemberExpression
from panther.core.visitor import TemplateElement
import re


def _report(value):
    issue_text = "Possible SQL injection vector \
    through string-based query construction: '%s'"

    return panther.Issue(
        severity=panther.HIGH,
        confidence=panther.MEDIUM,
        text=(issue_text % value)
    )


# Regex to match SQL expressions
SQL_RE = re.compile(
    r'(select\s.*from\s|'
    r'delete\s+from\s|'
    r'insert\s+into\s.*values\s|'
    r'update\s.*set\s)',
    re.IGNORECASE | re.DOTALL,
)

# Regex to match concatenation calls
CALL_RE = re.compile(
    r'join|append|concat',
    re.IGNORECASE
)


def _extract_string_value(node):

    '''Tries to extract a string from a node. Supported types
    are TemplateElement and Literal.
    '''

    found_string = None

    # If it is a TemplateElement get cooked value.
    # If it is a Literal, check whether raw node starts
    # with either (') or ("").

    if isinstance(node, TemplateElement):
        found_string = node.value['cooked']
    elif isinstance(node, Literal):
        raw_literal = node.raw
        is_string = raw_literal.startswith('"') or raw_literal.startswith("'")
        if is_string:
            found_string = node.value

    return found_string


def _contains_escape(node):

    '''Checks whether an expression is escaped.'''

    return ('escape' in json.dumps(node.dict()))


def _is_dangerous_sql(data):

    '''Check whether an SQL string is present for SQL injection.
    If the string includes question marks then do not categorize
    as dangerous.
    '''

    is_sql = SQL_RE.search(data) is not None

    if is_sql:
        return False if ('?' in data) else True
    else:
        return False


def _is_dangerous_concatenation(node_list):

    '''Checks whether a node list contains both SQL strings and expressions.'''

    string_list = []
    expression_node_list = []

    # Loop over node list and extract all strings from list of nodes.
    # If it is not a string then put it into expression list.
    for node in node_list:

        found_string = _extract_string_value(node)

        if found_string is None:
            expression_node_list.append(node)
        else:
            string_list.append(found_string)

    if len(string_list) == 0:
        # If it only contains expressions we cannot judge whether
        # we are mixing a string and a variable.

        # TODO(Izel): Implement expression parsers: Backtrace variable assignments
        # to detect whether an expression is actually a string.

        return False

    if len(expression_node_list) == 0:
        # All are strings so there is no mix of expressions and strings.
        return False

    # Check whether we have any dangerous strings in our list.
    contains_dangerous_strings = any(map(_is_dangerous_sql, string_list))

    # If we do not have a suspicious SQL string simply return
    if not contains_dangerous_strings:
        return False

    # It is valid to mix strings with escaped variables. So if all
    # our expressions are escaped then do not create an issue.

    all_contains_escape = all(map(_contains_escape, expression_node_list))
    if all_contains_escape:
        return False

    return True


def _is_dangerous_call(data):

    '''Checks whether a function name is suspicious for string concatenation.'''

    return CALL_RE.search(data) is not None


@test.checks('CallExpression')
@test.test_id('P602')
def hardcoded_sql_expressions_merge_function(context):

    '''Checks whether an sql query is mixed with an expression using a
    function. It looks for the functions that contains the words
    'join', 'append' or 'concat' and if the callee of a function
    and its arguments contains both dangerous SQL strings and expressions
    an issue is created.

    See examples below:

    var dangerous_merge_function_direct = concat('SELECT Id FROM ', a, b);
    var dangerous_merge_function_join = ['SELECT Id FROM ', query].join('');
    '''

    try:
        node_list = []
        contains_dangerous_calls = False
        callee = context.node.callee
        arguments = context.node.arguments
        issue_text = 'Concatenation of an SQL statement using a function.'

        # Test for calls to a function registered in global context,
        # e.g: concatString('...', str)

        if isinstance(callee, Identifier):
            contains_dangerous_calls = _is_dangerous_call(callee.name)

        # Test for member expression based calls like:
        # str.concat(str2, '...') or ['...', str, str2].join('')
        elif isinstance(callee, MemberExpression):

            contains_dangerous_calls = _is_dangerous_call(callee.property.name)

            # If the callee object is an array expression then all elements
            # of it should be investigated.
            if isinstance(callee.object, ArrayExpression):
                node_list = node_list + callee.object.elements
            else:
                node_list.append(callee.object)

        # In any case add function arguments to node list for checking
        if contains_dangerous_calls:
            node_list = node_list + arguments
            if _is_dangerous_concatenation(node_list):
                return _report(issue_text)

    except Exception as e:
        print(e)


@test.checks('BinaryExpression')
@test.test_id('P602')
def hardcoded_sql_expressions_with_plus(context):

    '''Checks whether an sql query is mixed with an expression
    using a plus operator. It scans for (+) operators that
    combines some strings and if there is concatenation
    of a dangerous SQL string with an expression an issue is
    created.

    See example below:

    var dangerous_with_plus_mixed_identifier_literal = 'SELECT Id FROM ' + query + 'WHERE Id = 6';

    '''

    issue_text = 'Concatenation with an SQL statement \
    and an expression using (+).'

    try:
        if context.node.operator == '+':
            left_node = context.node.left
            right_node = context.node.right
            if _is_dangerous_concatenation([left_node, right_node]):
                return _report(issue_text)

    except Exception as e:
        print(e)


@test.checks('TemplateLiteral')
@test.test_id('P602')
def hardcoded_sql_expressions_with_template_literal(context):

    '''Checks whether an sql query is mixed with an expression
    in a template literal. It checks {...} literals inside a
    string and if there is concatenation of a dangerous SQL
    string with an expression inside curly braces an issue
    is created.

    See example below:

    var dangerous_with_template_literal_expression  = `SELECT Id FROM MyTable WHERE Id = ${a() + 2 + 4}`;

    '''

    issue_text = 'Concatenation with an SQL statement \
    using a template literal.'

    # Quasis property gives string parts in a template literal and expression property
    # gives the expressions inside curly braces as an array.

    node_list = context.node.quasis + context.node.expressions

    try:
        if _is_dangerous_concatenation(node_list):
            return _report(issue_text)

    except Exception as e:
        print(e)


@test.checks('AssignmentExpression')
@test.test_id('P602')
def hardcoded_sql_expressions_with_plus_equal(context):

    '''Checks whether an sql query is mixed with an expression. It tracks (+=)
    signs and if there is an assignment to a variable using a dangerous SQL string,
    an issue is created.

    See example below:

    var dangerous_with_plus_equal_identifier  = '';
    dangerous_with_plus_equal_identifier += 'SELECT Id FROM ';
    dangerous_with_plus_equal_identifier += 'MyTable WHERE Id = ';
    dangerous_with_plus_equal_identifier += req.body.id;

    '''

    issue_text = 'Concatenation with an SQL statement \
    and an expression using (+=)'

    try:
        if context.node.operator == '+=':
            left_node = context.node.left
            right_node = context.node.right
            if _is_dangerous_concatenation([left_node, right_node]):
                return _report(issue_text)

    except Exception as e:
        print(e)
