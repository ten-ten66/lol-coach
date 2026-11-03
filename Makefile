.PHONY: help up down logs ps reset dev test lint typecheck format check sync

help: ## Show available commands
	@awk 'BEGIN {FS = ":.*## "} /^[a-zA-Z_-]+:.*## / {printf "  \033[36m%-12s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)

# ---- Infrastructure (Postgres + Redis via Docker) -----------------------

up: ## Start Postgres + Redis
	docker compose up -d

down: ## Stop containers (keep volumes)
	docker compose down

logs: ## Tail container logs
	docker compose logs -f

ps: ## Show container status
	docker compose ps

reset: ## Destroy containers AND data volumes
	docker compose down -v

# ---- Backend (Python) ---------------------------------------------------

sync: ## Install/sync Python deps
	cd backend && uv sync

dev: ## Run API server with hot reload
	cd backend && uv run lol-coach serve

test: ## Run pytest
	cd backend && uv run pytest

lint: ## Ruff lint
	cd backend && uv run ruff check src tests

format: ## Ruff format
	cd backend && uv run ruff format src tests

typecheck: ## Mypy
	cd backend && uv run mypy src

check: lint typecheck test ## Lint + typecheck + test
