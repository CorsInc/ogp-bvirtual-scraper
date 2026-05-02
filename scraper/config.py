"""Configuration for OGP Biblioteca Virtual scraper using SharePoint REST API."""

BASE_URL = "https://bvirtualogp.pr.gov"
SITE_URL = f"{BASE_URL}/ogp/Bvirtual"
API_URL = f"{SITE_URL}/_api/web"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json;odata=verbose",
    "Accept-Language": "es-PR,es;q=0.9,en;q=0.8",
}

REQUEST_DELAY = 1.0
OUTPUT_DIR = "scraper/output"

# Known list names from the Biblioteca Virtual
LISTS_OF_INTEREST = [
    "Pages",
    "Documentos",
    "Leyes Orgánicas",
    "Leyes de Referencia",
    "Reorganización Gubernamental",
    "Resoluciones Conjuntas",
    "Memoriales Explicativos",
]
