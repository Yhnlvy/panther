var router = require('express').Router()
var vulnDict = require('./basic.ref1')
var authHandler = require('../tracer/folder_reference/basic.ref2')

router.get('/crazy', authHandler.isAuthenticated, function (req, res) {
    res.render('app/admin', {
        admin: (req.user.role == 'admin')
    })
})