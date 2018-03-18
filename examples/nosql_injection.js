// #region dollar_where_used 

// Pattern: db.collection.find({ $where : function | string })

db.collection.find({
    active: true,
    $where: function() {
        return obj.credits - obj.debits < $userInput;
    }
});

// #endregion

// #region map_reduce_used 

// Pattern: db.runCommand({mapReduce: {}})

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

// Pattern: db.collection.mapReduce(...)

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

// #endregion

// #region group_used
// Pattern: db.runCommand({group: {}})

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

// Pattern: db.collection.group(...)

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
// #endregion







