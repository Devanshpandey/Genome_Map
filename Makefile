.PHONY: install download-ref prepare-ref api web dev

install:
	pip install -r requirements.txt
	cd apps/web && npm install

download-ref:
	python3 scripts/download_1kg.py --chrom 22 --out-dir data/raw/1kg

prepare-ref:
	python3 scripts/prepare_reference_panel.py --in-dir data/raw/1kg --out-dir data/processed

api:
	uvicorn apps.api.main:app --reload --host 0.0.0.0 --port 8000

web:
	cd apps/web && npm run dev

dev:
	docker-compose up -d || (echo "Running locally instead of docker" && make api & make web)
