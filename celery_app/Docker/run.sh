docker build -t redis -f Dockerfile.redis ../
docker build -t web -f Dockerfile.web ../
docker build -t worker -f Dockerfile.worker ../
docker compose up