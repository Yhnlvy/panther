// #region hardcoded_sql_expressions_with_plus 

// var dangerous_with_plus_mixed_identifier_literal = 'SELECT Id FROM ' + query + 'WHERE Id = 6';

// var dangerous_with_plus_mixed_expression_literal = 'SELECT Id FROM ' + query['key'];

// var dangerous_with_plus_mixed_complex_literal = '' + ('SELECT Id FROM ' + query)

// var dangerous_with_plus_a_string_and_a_number = "SELECT Id FROM MyTable WHERE Id = " + 2

// var safe_with_plus_mixed_expression_literal_escape = "SELECT * FROM MyTable WHERE Id = " + connection.escape(id);

// var safe_with_plus_two_literal = 'SELECT Id FROM MyTable' + ' WHERE Id = 5'

// #endregion


// db.collection.find({ $where : function | string })

db.collection.find({
    active: true,
    $where: function() {
        return obj.credits - obj.debits < $userInput;
    }
});

// db.runCommand({mapReduce: {}})

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

// db.runCommand({group: {}})

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

// db.collection.group()

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
})

// db.collection.mapReduce()

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
)






