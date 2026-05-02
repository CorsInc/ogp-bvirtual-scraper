# OGP Biblioteca Virtual Scraper (SharePoint REST API)

Scraper para la **Biblioteca Virtual de OGP "Miguel J. Rodríguez Fernández"** usando la API REST de SharePoint.

## ¿Cómo funciona?

En lugar de hacer web scraping tradicional, este scraper usa la **API REST de SharePoint** (`_api/web/lists`) para:

1. Descubrir todas las listas y bibliotecas de documentos del sitio
2. Extraer metadatos de cada lista (título, número de items, IDs)
3. Obtener items y archivos de las listas de interés
4. Descargar documentos (PDFs, Word, Excel) a tu máquina local

## Instalación

```bash
pip install -r requirements.txt
```

## Uso

### Explorar la estructura del sitio:
```bash
python -m scraper.main
```
Esto guarda JSONs con toda la estructura de listas, items y archivos en `scraper/output/`.

### Descargar todos los documentos:
```bash
python -m scraper.main download
```
Esto descarga los archivos a `scraper/output/documents/`.

## Output

- `site_structure.json` — Listas y bibliotecas del sitio
- `list_*.json` — Items de cada lista de interés
- `all_list_items.json` — Todos los items combinados
- `library_*.json` — Archivos encontrados en bibliotecas de documentos
- `documents/` — Archivos descargados (modo download)

## Notas

- El sitio usa SharePoint y requiere autenticación para algunas operaciones
- Las listas públicas deberían ser accesibles sin autenticación
- Si una lista devuelve 0 items, puede requerir autenticación o no existir
