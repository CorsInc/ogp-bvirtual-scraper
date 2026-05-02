# OGP Biblioteca Virtual Scraper

Scraper para la **Biblioteca Virtual de OGP "Miguel J. Rodríguez Fernández"**.
Extrae leyes, resoluciones y documentos presupuestarios del portal de la
Oficina de Gerencia y Presupuesto de Puerto Rico.

## Estrategia

El scraper usa **dos enfoques** complementarios:

1. **REST API de SharePoint** (`_api/web/lists`) — intenta obtener listas e
   items directamente. Soporta respuestas JSON y Atom XML.
2. **Selenium** (opcional) — para cuando el contenido requiere JavaScript o
   autenticación. Navega las secciones y extrae enlaces a documentos.

## Instalación

```bash
pip install -r requirements.txt
```

Para Selenium (opcional):
```bash
pip install selenium
# Además necesitas ChromeDriver o GeckoDriver en el PATH
```

## Uso

### Explorar estructura del sitio vía API:
```bash
python -m scraper.main
```

### Descargar documentos vía API:
```bash
python -m scraper.main download
```

### Extraer documentos con Selenium:
```bash
OGP_USE_SELENIUM=1 python -m scraper.main selenium
```

### Todo en uno (API + Selenium):
```bash
OGP_USE_SELENIUM=1 python -m scraper.main all
```

## Configuración (variables de entorno)

| Variable | Default | Descripción |
|---|---|---|
| `OGP_USE_SELENIUM` | `0` | Activar Selenium |
| `OGP_SELENIUM_HEADLESS` | `1` | Modo headless |
| `OGP_SELENIUM_DRIVER` | `chromium` | chromium, firefox, edge |
| `OGP_OUTPUT_DIR` | `scraper/output` | Directorio de salida |
| `OGP_USERNAME` | — | Usuario SharePoint (auth) |
| `OGP_PASSWORD` | — | Contraseña SharePoint |

## Output

- `site_structure.json` — Listas y bibliotecas del sitio
- `list_*.json` — Items de cada lista/sección
- `all_list_items.json` — Todos los items combinados
- `library_*.json` — Archivos en bibliotecas de documentos
- `selenium_documents.json` — Documentos extraídos con Selenium
- `documents/` — Archivos descargados (modo `download`)

## Secciones

1. **Leyes Orgánicas** — Leyes que crean agencias y entidades gubernamentales
2. **Leyes de Referencia** — Leyes por temas (Contabilidad, Empleos, etc.)
3. **Reorganización Gubernamental** — Documentos de reorganización
4. **Resoluciones Conjuntas del Presupuesto** — Presupuestos por año fiscal
5. **Memoriales Explicativos del Presupuesto** — Documentos presupuestarios
