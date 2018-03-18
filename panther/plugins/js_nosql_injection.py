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
from panther.core.utils import utils

LOG = logging.getLogger(__name__)


def _report(value, confidence):
    issue_text = "Possible NoSQL script injection vector: '%s'"

    return panther.Issue(
        severity=panther.HIGH,
        confidence=confidence,
        text=(issue_text % value)
    )


@test.checks('CallExpression')
@test.test_id('P603')
def dollar_where_used(context):
    '''Checks whether a query contains a $where filtering.
    To catch the call it looks for db.{any_collection}.find
    pattern in the call and checks whether first argument is
    an object and it contains the key "$where".

    See example below:

    db.collection.find({
        active: true,
        $where: function() {
            return obj.credits - obj.debits < $userInput;
        }
    });
    '''

    try:
        node = context.node

        is_name_space_matched = utils.match_name_space(
            node, ['*db', '*', '*find'])

        if is_name_space_matched:
            is_argument_key_matched = utils.match_argument_with_object_key(
                node,  '*$where')

            if is_argument_key_matched:
                return _report('$where condition detected while querying. Please use $expr instead.', panther.MEDIUM)

    except Exception as e:
        LOG.error(e)


@test.checks('CallExpression')
@test.test_id('P603')
def group_used(context):
    '''Checks whether a query contains an unsafe grouping.
    To catch the call it looks for db.{any_collection}.group
    pattern in the call or db.runCommand({}) pattern with a
    key named 'group'.

    See examples below:

    1)

    db.collection.group({
        key: {
            ord_dt: 1,
            'item.sku': 1
        },
        cond: {
            ord_dt: {
                $gt: new Date('01/01/2012')
            }
        },
        reduce: function(curr, result) {
            result.total += curr.item.qty;
        },
        initial: {
            total: 0
        }
    });

    2)

    db.runCommand({
        group: {
            ns: 'orders',
            key: {
                ord_dt: 1,
                'item.sku': 1
            },
            cond: {
                ord_dt: {
                    $gt: new Date('01/01/2012')
                }
            },
            $reduce: reduceFn,
            initial: {}
        }
    });
    '''

    try:
        deprecation_text = 'Mongodb 3.4 deprecates the group command. Please use db.collection.aggregate() with the $group stage or db.collection.mapReduce() instead.'

        node = context.node

        is_name_space_matched = utils.match_name_space(
            node, ['*db', '*', '*group'])

        if is_name_space_matched:
            return _report('Group command detected while querying a collection. ' + deprecation_text, panther.MEDIUM)

        is_name_space_matched = utils.match_name_space(
            node, ['*db', '*runCommand'])

        if is_name_space_matched:
            is_argument_key_matched = utils.match_argument_with_object_key(
                node, '*group')

            if is_argument_key_matched:
                return _report('Grouping detected using run command. ' + deprecation_text, panther.MEDIUM)

    except Exception as e:
        LOG.error(e)


@test.checks('CallExpression')
@test.test_id('P603')
def map_reduce_used(context):
    '''Checks whether a query contains a possible unsafe map reduce.
    To catch the call it looks for db.{any_collection}.mapReduce
    pattern in the call or db.runCommand({}) pattern with a
    key named 'mapReduce'.

    See examples below:

    1)

    db.collection.mapReduce(mapFn,
        reduceFn, {
            out: {
                merge: "map_reduce_example"
            },
            query: {
                ord_date: {
                    $gt: new Date('01/01/2012')
                }
            },
            finalize: finalizeFn
        }
    );

    2)

        db.runCommand({
            mapReduce: collection,
            map: mapFn,
            reduce: reduceFn,
            finalize: finalizeFn,
            out: output,
            query: document,
            sort: document,
            limit: 5,
            scope: document,
            jsMode: true,
            verbose: false,
            bypassDocumentValidation: false,
            collation: document
        });

    '''

    try:
        warning_text = 'Please be aware of the security risks of using "mapReduce".'

        node = context.node

        is_name_space_matched = utils.match_name_space(
            node, ['*db', '*', '*mapReduce'])

        if is_name_space_matched:
            return _report('Map reduce command detected while querying a collection. ' + warning_text, panther.LOW)

        is_name_space_matched = utils.match_name_space(
            node, ['*db', '*runCommand'])

        if is_name_space_matched:
            is_argument_key_matched = utils.match_argument_with_object_key(
                node, '*mapReduce')

            if is_argument_key_matched:
                return _report('Map reduce detected using run command. ' + warning_text, panther.LOW)

    except Exception as e:
        LOG.error(e)
