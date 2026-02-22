.PHONY: up down build logs test health

up: ## Build and start all services
	docker compose up --build -d
	@echo ""
	@echo "========================================"
	@echo "  Legal Form Fill is running!"
	@echo "  Open: http://localhost:3000"
	@echo "========================================"
	@echo ""

down: ## Stop all services
	docker compose down

build: ## Rebuild without starting
	docker compose build

logs: ## Tail backend logs
	docker logs -f legal-form-fill-backend

test: ## Run backend tests locally
	cd backend && python -m pytest -v

health: ## Check service health
	@curl -s http://localhost:3000/api/health | python -m json.tool

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## ' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-10s\033[0m %s\n", $$1, $$2}'
