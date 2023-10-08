
main: build init

build:
	docker build -f Dockerfile . -t openai-relay:0.0.1
	docker build -f DockerfileSync . -t openai-log-sync:0.0.1

init:
	docker compose -f ./deploy/docker-compose.yml up -d
	docker exec -i mysql-openai mysql -u root -pZ8nVfAqXERe82VwJ openai < ./init.sql

