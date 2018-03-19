# -*- coding:utf-8 -*-

r"""
==========================================================================
P603: Test for NoSQL injection
==========================================================================

All of the following MongoDB operations permit you to run arbitrary JavaScript
expressions directly on the server:

1) $where
--------------
Reference: https://docs.mongodb.com/manual/reference/operator/query/where/#op._S_where
Category: Operators > Query and Projection Operators > Evaluation Query Operators > $where

2) mapReduce
--------------
Reference: https://docs.mongodb.com/manual/reference/method/db.collection.mapReduce/
Category: mongo Shell Methods > Collection Methods > db.collection.mapReduce()

Reference 2: https://docs.mongodb.com/manual/reference/command/mapReduce/#dbcmd.mapReduce
Category 2: Database Commands > Aggregation Commands > mapReduce

3) group
--------------
Reference: https://docs.mongodb.com/manual/reference/method/db.collection.group/
Category: mongo Shell Methods > Collection Methods > db.collection.group()

Reference 2: https://docs.mongodb.com/manual/reference/command/group/
Category 2: Database Commands > Aggregation Commands > group

These methods can be really convenient, but they pose a huge security risk to
your database integrity if your application does not sanitize and escape user-provided
values properly, as proven by many reports of NoSQL injection attacks.

For more info see: https://docs.mongodb.com/manual/faq/fundamentals/#javascript

:Example:

    >> Issue: [P603:dollar_where_used] Possible NoSQL script injection vector:
    '$where condition detected while querying. Please use $expr instead.'
    Severity: High   Confidence: Medium
    Location: examples/nosql_injection.js:20
    19
    20	db.collection.find({
    21	    active: true,
    22	    $where: function() {

    --------------------------------------------------
    >> Issue: [P603:map_reduce_used] Possible NoSQL script injection vector:
    'Map reduce detected using run command. Please be aware of the security risks of using "mapReduce".'
    Severity: Medium   Confidence: Low
    Location: examples/nosql_injection.js:29
    28
    29	db.runCommand({
    30	    mapReduce: collection,
    31	    map: mapFn,

    --------------------------------------------------
    >> Issue: [P603:map_reduce_used] Possible NoSQL script injection vector:
    'Map reduce command detected while querying a collection.
    Please be aware of the security risks of using "mapReduce".'
    Severity: Medium   Confidence: Low
    Location: examples/nosql_injection.js:47
    46
    47	db.collection.mapReduce(mapFn,
    48	    reduceFn, {
    49	        out: {

    --------------------------------------------------
    >> Issue: [P603:group_used] Possible NoSQL script injection vector:
    'Grouping detected using run command. Mongodb 3.4 deprecates the group command.
    Please use db.collection.aggregate() with the $group stage or db.collection.mapReduce() instead.'
    Severity: High   Confidence: Medium
    Location: examples/nosql_injection.js:63
    62
    63	db.runCommand({
    64	    group: {
    65	        ns: 'orders',

    --------------------------------------------------
    >> Issue: [P603:group_used] Possible NoSQL script injection vector:
    'Group command detected while querying a collection. Mongodb 3.4 deprecates the group command.
    Please use db.collection.aggregate() with the $group stage or db.collection.mapReduce() instead.'
    Severity: High   Confidence: Medium
    Location: examples/nosql_injection.js:82
    81
    82	db.collection.group({
    83	    key: {
    84	        ord_dt: 1,

"""

import logging
import panther
from panther.core import test_properties as test
from panther.core import utils

LOG = logging.getLogger(__name__)


def _report(value, severity, confidence):
    issue_text = "Possible NoSQL script injection vector: '%s'"

    return panther.Issue(
        severity=severity,
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
                node, '*$where')

            if is_argument_key_matched:
                return _report('$where condition detected while querying. Please use $expr instead.',
                               severity=panther.HIGH, confidence=panther.MEDIUM)

    except Exception as e:
        LOG.debug(e)


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
        deprecation_text = 'Mongodb 3.4 deprecates the group command. Please use db.collection.aggregate()\
        with the $group stage or db.collection.mapReduce() instead.'

        node = context.node

        is_name_space_matched = utils.match_name_space(
            node, ['*db', '*', '*group'])

        if is_name_space_matched:
            return _report('Group command detected while querying a collection. ' + deprecation_text,
                           severity=panther.HIGH, confidence=panther.MEDIUM)

        is_name_space_matched = utils.match_name_space(
            node, ['*db', '*runCommand'])

        if is_name_space_matched:
            is_argument_key_matched = utils.match_argument_with_object_key(
                node, '*group')

            if is_argument_key_matched:
                return _report('Grouping detected using run command. ' + deprecation_text,
                               severity=panther.HIGH, confidence=panther.MEDIUM)

    except Exception as e:
        LOG.debug(e)


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
            return _report('Map reduce command detected while querying a collection. ' + warning_text,
                           severity=panther.MEDIUM, confidence=panther.LOW)

        is_name_space_matched = utils.match_name_space(
            node, ['*db', '*runCommand'])

        if is_name_space_matched:
            is_argument_key_matched = utils.match_argument_with_object_key(
                node, '*mapReduce')

            if is_argument_key_matched:
                return _report('Map reduce detected using run command. ' + warning_text,
                               severity=panther.MEDIUM, confidence=panther.LOW)

    except Exception as e:
        LOG.debug(e)
