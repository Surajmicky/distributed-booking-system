.PHONY: help install dev test migrate migrate-up migrate-down lint clean

help:           ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-15s\033[0m %s\n", $$1, $$2}'

install:        ## Install dependencies
	pip install -r requirements.txt

dev:            ## Start development server
	uvicorn app.main:app --reload

test:           ## Run tests
	pytest

migrate:        ## Create migration (usage: make migrate MSG="message")
	alembic revision --autogenerate -m "$(MSG)"

migrate-up:     ## Apply migrations
	alembic upgrade head

migrate-down:   ## Rollback last migration
	alembic downgrade -1

migrate-down-to: ## Rollback to specific revision (usage: make migrate-down-to REV="revision_id")
	alembic downgrade "$(REV)"

lint:           ## Run linting
	flake8 app

clean:          ## Clean cache files
	find . -type d -name "__pycache__" -delete
	find . -type f -name "*.pyc" -delete