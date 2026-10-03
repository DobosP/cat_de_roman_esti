# Makefile — thin wrappers over ./run.sh for the cat_de_roman_esti web app.
#
#   make run      build Go + SPA if missing, then serve the anonymous arcade
#   make dev      Vite frontend reload + Go API (restart after Go edits)
#   make docker   docker build + run the production image
#   make build    rebuild the compiled SPA + Go executable
#   make help     list targets
#
# Pass listener settings through as usual, e.g.: make run PORT=9000

.PHONY: run dev docker build help
.DEFAULT_GOAL := help

run: ## Build Go + SPA if missing, then serve the anonymous arcade
	./run.sh run

dev: ## Vite frontend reload + Go API (restart after Go edits)
	./run.sh dev

docker: ## docker build + run the production image
	./run.sh docker

build: ## Rebuild the compiled SPA and Go executable
	./run.sh build

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) \
	  | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-8s\033[0m %s\n", $$1, $$2}'
