.PHONY: install lint test up down load kind-up kind-deploy kind-down

install:   ## install dev deps
	pip install -r requirements-dev.txt
lint:
	ruff check .
test:
	pytest -q
up:        ## full local stack: app+postgres+redis+prometheus+grafana
	docker compose up -d --build
down:
	docker compose down -v
load:      ## generate traffic so dashboards have data
	./scripts/loadgen.sh
kind-up:
	kind create cluster --name urlshort
kind-deploy:
	docker build -t urlshort:local .
	kind load docker-image urlshort:local --name urlshort
	cd k8s/base && kustomize edit set image urlshort=urlshort:local && kubectl apply -k .
kind-down:
	kind delete cluster --name urlshort
