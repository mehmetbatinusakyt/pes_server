const express = require('express');
const app = express();

app.get('/admin', (req, res) => {
  res.send('Административен панел');
});

app.listen(3000, () => {
  console.log('Административен панел стартиран на порт 3000');
});
