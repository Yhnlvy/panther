var router = require('express').Router()
var vulnDict = require('../config/vulns')
var authHandler = require('../core/authHandler')

router.get('/crazy', authHandler.isAuthenticated, function (req, res) {
    res.render('app/admin', {
        admin: (req.user.role == 'admin')
    })
})

router.post('/crazy', authHandler.isAuthenticated, function (req, res) {
    res.render('app/admin', {
        admin: (req.user.role == 'admin')
    })
})