SHELL := /bin/bash

# Configurable variables
PY ?= python3
PORT ?= 8000
IMAGE ?= openwebui-remote-tools:latest
CONTAINER ?= openwebui-remote-tools

.PHONY: help venv install playwright-install run run-dev openapi check docker-build docker-up docker-down docker-logs docker-restart docker-shell docker-clean

.DEFAULT_GOAL := help

help: ## Show this help
	@echo "Available targets:" && \
	awk 'BEGIN {FS = ":.*##"} /^[a-zA-Z0-9_\-]+:.*##/ {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)

venv: ## Create virtualenv in .venv
	$(PY) -m venv .venv

install: ## Install Python dependencies into .venv
	@if [ ! -d .venv ]; then $(PY) -m venv .venv; fi; \
	source .venv/bin/activate && pip install -r requirements.txt

playwright-install: ## Install Playwright Chromium (one-time)
	@if [ ! -d .venv ]; then $(PY) -m venv .venv; fi; \
	source .venv/bin/activate && $(PY) -m playwright install --with-deps chromium

run: ## Run server locally (uses .env automatically)
	@if [ ! -d .venv ]; then $(PY) -m venv .venv; fi; \
	source .venv/bin/activate && uvicorn app.main:app --host 0.0.0.0 --port $(PORT)

run-dev: ## Run server locally with autoreload
	@if [ ! -d .venv ]; then $(PY) -m venv .venv; fi; \
	source .venv/bin/activate && uvicorn app.main:app --host 0.0.0.0 --port $(PORT) --reload

openapi: ## Print OpenAPI URL
	@echo "OpenAPI schema: http://localhost:$(PORT)/openapi.json"

check: ## Quick syntax check of app modules
	@if [ ! -d .venv ]; then $(PY) -m venv .venv; fi; \
	source .venv/bin/activate && $(PY) -m py_compile app/*.py && echo "OK"

docker-build: ## Build docker image
	docker build -t $(IMAGE) .

docker-up: ## Start with docker compose (detached)
	docker compose up --build

docker-down: ## Stop and remove containers
	docker compose down

docker-logs: ## Follow logs
	docker compose logs -f

docker-restart: ## Restart compose service
	docker compose restart

docker-shell: ## Shell into running container
	docker exec -it $(CONTAINER) bash || docker exec -it $(CONTAINER) sh

docker-clean: ## Remove dangling images/volumes (careful!)
	docker system prune -f


