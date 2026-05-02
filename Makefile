# OGP Biblioteca Virtual Scraper - Comandos rápidos
#
# Uso:
#   make explore       # Explorar estructura del sitio
#   make download      # Descargar documentos
#   make selenium      # Extraer con Selenium
#   make csv           # Exportar todo a CSV
#   make all           # Todo en uno
#   make docker-build  # Construir imagen Docker
#   make docker-run    # Correr en Docker (explore)
#   make clean         # Limpiar outputs

.PHONY: explore download selenium csv all docker-build docker-run clean

explore:
	python -m scraper.main

download:
	python -m scraper.main download

selenium:
	OGP_USE_SELENIUM=1 python -m scraper.main selenium

csv:
	python -m scraper.main csv

all:
	OGP_USE_SELENIUM=1 python -m scraper.main all

docker-build:
	docker build -t ogp-scraper .

docker-run:
	docker run --rm -v $(PWD)/output:/app/scraper/output ogp-scraper

docker-run-selenium:
	docker run --rm \
		-e OGP_USE_SELENIUM=1 \
		-v $(PWD)/output:/app/scraper/output \
		ogp-scraper python -m scraper.main selenium

clean:
	rm -rf scraper/output/
