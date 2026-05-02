# 🏛️ OGP Biblioteca Virtual Scraper

Scraper para la **Biblioteca Virtual de OGP "Miguel J. Rodríguez Fernández"**.
Extrae leyes, resoluciones y documentos presupuestarios del portal de la
Oficina de Gerencia y Presupuesto de Puerto Rico.

## Estrategia

Dos enfoques complementarios:

| Enfoque | Pros | Contras |
|---|---|---|
| **REST API** (`_api/web/lists`) | Rápido, sin navegador | Algunas listas requieren auth |
| **Selenium** (opcional) | Ve lo mismo que un humano | Más lento, requiere Chrome |

## Uso rápido

```bash
# Instalar
pip install -r requirements.txt

# Explorar estructura
python -m scraper.main

# Descargar documentos
python -m scraper.main download

# Con Selenium (si hay contenido JS)
OGP_USE_SELENIUM=1 python -m scraper.main selenium

# Exportar todo a CSV
python -m scraper.main csv

# Todo en uno
OGP_USE_SELENIUM=1 python -m scraper.main all
```

O con `make`:
```bash
make explore
make download
make selenium
make csv
make all
```

## Docker

```bash
make docker-build
make docker-run          # API mode
make docker-run-selenium # Selenium mode
```

## Output

| Archivo | Contenido |
|---|---|
| `site_structure.json` | Listas y bibliotecas del sitio |
| `list_*.json` / `list_*.csv` | Items de cada sección |
| `all_list_items.json` | Todos los items combinados |
| `library_*.json` | Archivos en bibliotecas de documentos |
| `selenium_documents.json` / `.csv` | Documentos extraídos con Selenium |
| `documents/` | Archivos descargados |

## Configuración

| Variable | Default | Descripción |
|---|---|---|
| `OGP_DEBUG` | `0` | Logs detallados |
| `OGP_USE_SELENIUM` | `0` | Activar Selenium |
| `OGP_SELENIUM_HEADLESS` | `1` | Modo headless |
| `OGP_SELENIUM_DRIVER` | `chromium` | chromium, firefox, edge |
| `OGP_OUTPUT_DIR` | `scraper/output` | Directorio de salida |
| `OGP_USERNAME` | — | Usuario SharePoint |
| `OGP_PASSWORD` | — | Contraseña SharePoint |

## Secciones

1. **Leyes Orgánicas** — Leyes que crean agencias y entidades gubernamentales
2. **Leyes de Referencia** — Leyes por temas (Contabilidad, Empleos, Ética, etc.)
3. **Reorganización Gubernamental** — Documentos de reorganización
4. **Resoluciones Conjuntas del Presupuesto** — Presupuestos por año fiscal
5. **Memoriales Explicativos del Presupuesto** — Documentos presupuestarios
