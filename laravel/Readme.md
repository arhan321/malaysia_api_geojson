# SETUP
- tambahkan di .env
```bash
PREDICT_KEY = berapaya
PREDICT_URL = http://berapaya:8000
API_KEY = test
```
- shared network
```bash
docker network create shared_net
```

- running api predict
```bash
cd predict
docker compose up -d --build
```
- running api laravel
```bash
docker compose up -d --build
```

