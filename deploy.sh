docker compose down
docker compose build --no-cache backend frontend
docker compose up -d backend frontend