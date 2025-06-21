all: build up

build:
	docker-compose build

up:
	docker-compose up -d load_balancer

down:
	docker-compose down

logs:
	docker-compose logs -f
