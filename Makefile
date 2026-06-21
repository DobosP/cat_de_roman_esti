# Makefile — thin wrappers over ./run.sh for the cat_de_roman_esti web app.
#
#   make run      build SPA if missing, then serve the BFF (offline by default)
#   make dev      vite dev + uvicorn --reload (hot-reload)
#   make docker   docker build + run the production image
#   make build    build the SPA into cat_de_roman_esti/web/static
#   make help     list targets
#
# Pass env through as usual, e.g.:  make run PORT=9000 ROEDU_API_URL=http://localhost:8077

.PHONY: run dev docker build help
.DEFAULT_GOAL := help

run: ## Build SPA if missing, then serve the BFF (offline fixture by default)
	./run.sh run

dev: ## Vite dev server + uvicorn --reload for hot-reload development
	./run.sh dev

docker: ## docker build + run the production image
	./run.sh docker

build: ## Build the SPA into cat_de_roman_esti/web/static
	./run.sh build

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) \
	  | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-8s\033[0m %s\n", $$1, $$2}'
