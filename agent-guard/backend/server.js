const express = require('express');
const app = express();

app.get('/api/projects', (req, res) => {
  res.json([
    { id: 1, title: 'Portfolio Project', tech: 'React' }
  ]);
});

app.post('/api/contact', (req, res) => {
  res.json({ status: 'message received' });
});

app.listen(5000, () => {
  console.log('Server running on port 5000');
});
