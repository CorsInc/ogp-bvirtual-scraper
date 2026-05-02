"""Configuration for OGP Biblioteca Virtual scraper."""

BASE_URL = "https://bvirtualogp.pr.gov"
SITE_PATH = "/ogp/Bvirtual/Pages"

SECTIONS = {
    "inicio": f"{SITE_PATH}/default.aspx",
    "leyes_organicas": f"{SITE_PATH}/LeyesOrganicas.aspx",
    "leyes_referencia": f"{SITE_PATH}/LeyesReferencia.aspx",
    "reorganizacion": f"{SITE_PATH}/ReorganizacionGubernamental.aspx",
    "resoluciones_presupuesto": f"{SITE_PATH}/ResolucionesConjuntas.aspx",
    "memoriales": f"{SITE_PATH}/MemorialesExplicativos.aspx",
}

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "es-PR,es;q=0.9,en;q=0.8",
}

REQUEST_DELAY = 1.5  # seconds between requests
OUTPUT_DIR = "scraper/output"
