"""Configuration for OGP Biblioteca Virtual scraper."""

import os

BASE_URL = "https://bvirtualogp.pr.gov"
SITE_URL = f"{BASE_URL}/ogp/Bvirtual"
API_URL = f"{SITE_URL}/_api/web"

# SharePoint REST API endpoints
API_ENDPOINTS = {
    "web": "",
    "lists": "lists",
    "list_items": "lists/getbytitle('{title}')/items",
    "list_items_by_id": "lists(guid'{id}')/items",
    "folders": "lists/getbytitle('{title}')/items?$select=Title,FileSystemObjectType,File&$filter=FileSystemObjectType eq 1",
    "files_in_folder": "lists/getbytitle('{title}')/items?$select=Title,File/ServerRelativeUrl,File/Length&$expand=File&$filter=startswith(File/ServerRelativeUrl,'{folder}')",
}

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json;odata=verbose",
    "Accept-Language": "es-PR,es;q=0.9,en;q=0.8",
}

REQUEST_DELAY = 1.0  # seconds between requests
OUTPUT_DIR = os.getenv("OGP_OUTPUT_DIR", "scraper/output")

# Known list/section names from the Biblioteca Virtual
SECTIONS = {
    "Leyes Orgánicas": {
        "description": "Leyes que crean agencias, corporaciones y entidades gubernamentales",
        "url": f"{SITE_URL}/Lists/LeyesOrganicas",
    },
    "Leyes de Referencia": {
        "description": "Leyes agrupadas por temas (Contabilidad, Empleos, Estadísticas, etc.)",
        "url": f"{SITE_URL}/Lists/LeyesDeReferencia",
    },
    "Reorganización Gubernamental": {
        "description": "Documentos de reorganización gubernamental",
        "url": f"{SITE_URL}/Lists/ReorganizacionGubernamental",
    },
    "Resoluciones Conjuntas del Presupuesto": {
        "description": "Resoluciones que acompañan el presupuesto de cada año fiscal",
        "url": f"{SITE_URL}/Lists/ResolucionesConjuntas",
    },
    "Memoriales Explicativos del Presupuesto": {
        "description": "Memorandos explicativos del presupuesto recomendado",
        "url": f"{SITE_URL}/Lists/MemorialesExplicativos",
    },
}

# Also try these as fallback list names
ALTERNATIVE_LIST_NAMES = [
    "Pages",
    "Documentos",
    "Leyes Orgánicas",
    "Leyes de Referencia",
    "Reorganización Gubernamental",
    "Resoluciones Conjuntas",
    "Memoriales Explicativos",
    "LeyesOrganicas",
    "LeyesDeReferencia",
    "ReorganizacionGubernamental",
    "ResolucionesConjuntas",
    "MemorialesExplicativos",
]

# Selenium config
USE_SELENIUM = os.getenv("OGP_USE_SELENIUM", "0") == "1"
SELENIUM_HEADLESS = os.getenv("OGP_SELENIUM_HEADLESS", "1") == "1"
SELENIUM_DRIVER = os.getenv("OGP_SELENIUM_DRIVER", "chromium")  # chromium, firefox, or edge

# Auth (optional - for authenticated access)
SHAREPOINT_USERNAME = os.getenv("OGP_USERNAME", "")
SHAREPOINT_PASSWORD = os.getenv("OGP_PASSWORD", "")
