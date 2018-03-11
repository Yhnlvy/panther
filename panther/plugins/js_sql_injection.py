# -*- coding:utf-8 -*-

r"""
==========================================================================
P602: Test for SQL injection
==========================================================================

# TODO: Improve Documentation

An SQL injection attack consists of insertion or "injection" of a SQL query via
the input data given to an application. It is a very common attack vector. This
plugin test looks for strings that resemble SQL statements that are involved in
some form of string building operation. For example:

 - "SELECT %s FROM derp;" % var
 - "SELECT thing FROM " + tab
 - "SELECT " + val + " FROM " + tab + ...
 - "SELECT {} FROM derp;".format(var)

Unless care is taken to sanitize and control the input data when building such
SQL statement strings, an injection attack becomes possible. If strings of this
nature are discovered, a LOW confidence issue is reported. In order to boost
result confidence, this plugin test will also check to see if the discovered
string is in use with standard Python DBAPI calls `execute` or `executemany`.
If so, a MEDIUM issue is reported. For example:

 - cursor.execute("SELECT %s FROM derp;" % var)

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
import re
import panther
from panther.core import test_properties as test
from panther.core.visitor import Literal, MemberExpression, ArrayExpression


# var concat1 = str.concat(str1, str2); // with_two_identifier
# var concat2 = str.concat('SELECT Id FROM ', str2); // an identifier and a literal
# var concat3 = 'SELECT Id FROM ' + query + 'WHERE Id = 6'; // mixed literal & identifier
# var concat4 = 'SELECT Id FROM ' + query['one'] + 'ssdad' + 'ddd'; // mixed expression & literal
# var concat5 = "SELECT * FROM MyTable WHERE Id = " + connection.escape(id); // mixed expression & literal
# var concat6 = `SELECT Id FROM ${expression()} string text`; // template literal + expression
# var concat7 = ['SELECT Id FROM ',query].join('') // join operator
# var concat8 = 'ssdsda' + ('sdsd' + 'sdaasd') // complex literals
# var concat9 = "".concat(...queryList); // spread operator

# var safeString1 = 'SELECT Id FROM MyTable' + ' WHERE Id = ?'
# var safeString2 = 2+"3"
# var safeString3 = 7-2
# var safeString4 = 7+2


# Plan
# String construction types: str.concat, concatenate with +, arr.join(''), template literals

def _report(value):
    return panther.Issue(
        severity=panther.HIGH,
        confidence=panther.MEDIUM,
        text=("Possible SQL injection vector through string-based query construction: '%s'" % value)
    )


SIMPLE_SQL_RE = re.compile(
    r'(select\s.*from\s|'
    r'delete\s+from\s|'
    r'insert\s+into\s.*values\s|'
    r'update\s.*set\s)',
    re.IGNORECASE | re.DOTALL,
)

SIMPLE_CALL_RE = re.compile(
    r'push|join|append|concat'
    re.IGNORECASE
)

 def _is_dangerous_concatenation(node_list):
    
    string_list = []
    expression_node_list = []
    
    for node in node_list:
       is_literal = isinstance(node, Literal)
       raw_literal = node.raw
       is_string = raw_literal.startswith('"') or raw_literal.startswith("'")
       if is_string:
           string_list.append(node.value)
       else:
           expression_node_list.append(node)   

    if len(string_list) == 0:
        # TODO: Improve expression parsers.
        return False
    if len(expression_node_list) == 0:
        # All are strings there is no problem
        return False

    # Check whether we have any dangerous strings 
    contains_dangerous_strings = any(map(_is_dangerous_string, string_list))
    
    if not contains_dangerous_strings:
         return False
    
    # If one of the expression does not contain escape then mark as dangerous.
    all_contains_escape = all(map(_contains_escape, expression_node_list))

    if all_contains_escape:
        return False
    
    return True

def _contains_escape(node):
    return ('escape' in json.dumps(node))

def _is_dangerous_string(data):
     
    is_sql = SIMPLE_SQL_RE.search(data) is not None
    
    if is_sql:
        return False if ('?' in data) else True
    else
        return False

def _is_dangerous_call(data):
    return SIMPLE_CALL_RE.search(data) is not None

@test.checks('CallExpression')
@test.test_id('P602')
def hardcoded_sql_expressions_with_calls(context):
    try:
        node_list = []
        contains_dangerous_calls = False

        # Test for direct calls.
        if isinstance(context.node, Identifier):
            contains_dangerous_calls = _is_dangerous_call(context.node.callee.name) 
        # Test for property based calls.
        else if isinstance(context.node, MemberExpression):
            callee_property_name = context.node.callee.property.name
            contains_dangerous_calls = _is_dangerous_call(callee_property_name)
            callee_object = context.node.callee.object
            if isinstance(callee_object, ArrayExpression):
                node_list = node_list + callee_object.elements
            else:
                node_list.append(callee_object)
        
        if contains_dangerous_calls:
            node_list = node_list + context.node.arguments
            if _is_dangerous_concatenation(node_list):
                _report('Concatenation of an SQL statement using a function.')
    except:
        pass

@test.checks('BinaryExpression')
@test.test_id('P602')
def hardcoded_sql_expressions_with_plus(context):
    '''
        TODO: Write comments
    '''
    try:
        if context.node.operator == '+':
            left_node = context.node.left
            right_node = context.node.right
            if _is_dangerous_concatenation([left_node, right_node])
                _report('Concatenation with an SQL statement and an expression.')
    except:
        pass

    

@test.checks('TemplateLiteral')
@test.test_id('P602')
def hardcoded_sql_expressions_template_literal(context):
    # Loop over context.node.quasis for each element get value.raw or value.cooked
    pass

