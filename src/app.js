const express = require('express');
const app = express();
const plantRoutes = require('./routes/plantRoutes');

// 미들웨어 설정
app.use(express.json());
app.use(express.urlencoded({ extended: true }));

// 라우터 연결
app.use('/api/plants', plantRoutes);

// 기본 헬스체크 엔드포인트
app.get('/', (req, res) => {
  res.send('Plant Platform Backend API is running!');
});

module.exports = app;
