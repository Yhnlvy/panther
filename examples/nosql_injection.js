// #region dollar_where_used 

// Pattern: db.collection.find({ $where : function | string })

timelineRouter.route("/api/timeline")
    .get(function (req, res) {
        try {
            const { startDate, endDate } = req.query;

            const TimelineItem = getTimelineItemModel();

            const timelineItems = TimelineItem.find({
                $where: "this.start >= new Date('" + startDate + "') && " +
                    "this.end <= new Date('" + endDate + "') &&" +
                    "this.hidden == false;"
            });

            console.log(colors.yellow(`# of Timeline Items retrieved: ${timelineItems.length}`));

            return res.json({
                timelineItems: timelineItems
            });

        } catch (error) {
            res.status(500).send("There was an error retrieving timeline items.  Please try again later");
        }
    });

// Exploit: "');return true;}+// for startDate or endDate

db.collection.find({
    active: true,
    $where: function () {
        return obj.credits - obj.debits < $userInput;
    }
});

// Exploit: "(function(){var date = new Date(); do{curDate = new Date();}while(curDate-date<10000); return Math.max();})()" for $userInput.

// #endregion

// #region map_reduce_used 

// Pattern: db.runCommand({mapReduce: {}})

db.runCommand({
    mapReduce: collection,
    map: function () { emit(this.cust_id, this.amount); },
    reduce:  function (key, values) { return Array.sum(values); },
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

db.orders.mapReduce(
    function () { emit(this.cust_id, this.amount); },
    function (key, values) { return Array.sum(values); },
    {
        query: {
            status: 'A'
        },
        out: 'order_totals'
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
        $reduce: function ( curr, result ) { },
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
    reduce: function (curr, result) {
        result.total += curr.item.qty;
    },
    initial: {
        total: 0
    }
});
// #endregion







