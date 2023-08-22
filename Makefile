
main: build init

build:
	docker build -f Dockerfile . -t openai-relay:0.0.1
	docker build -f DockerfileSync . -t openai-log-sync:0.0.1

init:
	docker compose -f ./deploy/docker-compose-middleware.yml up -d
	docker exec -i mysql8 mysql -u root -p123456 openai < ./deploy/init.sql

