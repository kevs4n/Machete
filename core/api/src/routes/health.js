const express = require('express');
const router = express.Router();

router.get('/', (req, res) => {
  res.json({ 
    status: 'healthy', 
    service: 'MACHETE API',
    timestamp: new Date().toISOString()
  });
});

module.exports = router;
