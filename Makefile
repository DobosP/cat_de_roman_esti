# Thin wrappers over the owner-bound managed launcher. See ./run.sh help.
# run/build/dev require the actual trusted fleet worktree; docker is the
# canonical-image alternative for an ordinary clean checkout. No host toolchains.

.PHONY: run dev docker build help
.DEFAULT_GOAL := help

run: ## Fresh managed build, verify the owning receipt, serve locally
	./run.sh run

dev: ## Managed API + pinned-container Vite HMR; development only
	./run.sh dev

docker: ## Canonical Docker build/run with explicit owner-qualified SHA/tree
	./run.sh docker

build: ## Fresh owning-wrapper build and verified native binary; no start
	./run.sh build

help: ## Show launcher requirements and commands
	./run.sh help
