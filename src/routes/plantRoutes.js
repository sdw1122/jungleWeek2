const express = require('express');
const router = express.Router();
const plantController = require('../controllers/plantController');

router.post('/:id/care', plantController.carePlant);
router.post('/:id/chat', plantController.chatPlant);

module.exports = router;
