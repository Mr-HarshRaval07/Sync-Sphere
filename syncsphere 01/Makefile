.PHONY: help build up down restart logs test clean lint

help:
	@echo "SyncSphere AI Dev Commands:"
	@echo "  make build    - Build all docker containers"
	@echo "  make up       - Run docker-compose in background"
	@echo "  make down     - Stop docker-compose services"
	@echo "  make restart  - Restart docker-compose services"
	@echo "  make logs     - View docker-compose logs"
	@echo "  make test     - Run test suite inside test container"
	@echo "  make clean    - Clean virtual environments and cache directories"

build:
	docker-compose build

up:
	docker-compose up -d

down:
	docker-compose down

restart:
	docker-compose restart

logs:
	docker-compose logs -f

test:
	docker-compose run --rm api pytest

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.py[co]" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".mypy_cache" -exec rm -rf {} +
	find . -type d -name ".ruff_cache" -exec rm -rf {} +
