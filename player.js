const express = require('express');
const app = express();

app.get('/', (req, res) => {
  res.send('Потребителски интерфейс');
});
app.get('/players', (req, res) => {
  res.send('Списък на активните играчи');
});

app.get('/player/:id', (req, res) => {
  res.send('Профил на играч');
});

app.listen(3001, () => {
  console.log('Потребителски интерфейс стартиран на порт 3001');
});
