"""SharePoint REST API client for OGP Biblioteca Virtual.

Supports both JSON (odata=verbose) and Atom XML responses,
with optional Selenium fallback for JS-heavy pages.
"""

import json
import time
import xml.etree.ElementTree as ET
from urllib.parse import quote, urljoin

import requests

from scraper.config import (
    API_URL,
    BASE_URL,
    HEADERS,
    REQUEST_DELAY,
    SECTIONS,
    SELENIUM_DRIVER,
    SELENIUM_HEADLESS,
    SHAREPOINT_PASSWORD,
    SHAREPOINT_USERNAME,
    USE_SELENIUM,
)
from scraper.log import log

# Namespace map for Atom XML responses
ATOM_NS = {
    "atom": "http://www.w3.org/2005/Atom",
    "d": "http://schemas.microsoft.com/ado/2007/08/dataservices",
    "m": "http://schemas.microsoft.com/ado/2007/08/dataservices/metadata",
}


class SharePointClient:
    """SharePoint REST API client with JSON and Atom XML support."""

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(HEADERS)
        self.base_url = API_URL
        self._selenium_driver = None
        self._list_cache = None  # Cache for get_lists()

    # ── Selenium setup (lazy) ──────────────────────────────────────────

    def _init_selenium(self):
        """Initialize Selenium WebDriver if configured."""
        if self._selenium_driver is not None:
            return self._selenium_driver
        if not USE_SELENIUM:
            return None

        try:
            if SELENIUM_DRIVER == "firefox":
                from selenium.webdriver import Firefox, FirefoxOptions

                options = FirefoxOptions()
                if SELENIUM_HEADLESS:
                    options.add_argument("--headless")
                self._selenium_driver = Firefox(options=options)
            else:
                from selenium.webdriver import Chrome, ChromeOptions

                options = ChromeOptions()
                if SELENIUM_HEADLESS:
                    options.add_argument("--headless")
                options.add_argument("--no-sandbox")
                options.add_argument("--disable-dev-shm-usage")
                self._selenium_driver = Chrome(options=options)

            if SHAREPOINT_USERNAME and SHAREPOINT_PASSWORD:
                self._selenium_login()

            return self._selenium_driver
        except ImportError:
            log.warning("Selenium no instalado. pip install selenium")
            return None
        except Exception as e:
            log.warning("Error iniciando Selenium: %s", e)
            return None

    def _selenium_login(self):
        """Authenticate via SharePoint forms-based auth using Selenium."""
        driver = self._selenium_driver
        if not driver:
            return

        login_url = f"{BASE_URL}/ogp/Bvirtual/_layouts/15/Authenticate.aspx"
        log.info("Iniciando sesión en SharePoint...")
        try:
            driver.get(login_url)
            time.sleep(2)

            username_field = driver.find_element("id", "userName")
            password_field = driver.find_element("id", "password")
            submit_btn = driver.find_element("id", "SubmitButton")

            username_field.send_keys(SHAREPOINT_USERNAME)
            password_field.send_keys(SHAREPOINT_PASSWORD)
            submit_btn.click()
            time.sleep(3)

            for cookie in driver.get_cookies():
                self.session.cookies.set(cookie["name"], cookie["value"])

            log.info("Login exitoso, cookies transferidas.")
        except Exception as e:
            log.warning("Login falló o no era necesario: %s", e)

    def close(self):
        """Clean up Selenium driver if active."""
        if self._selenium_driver:
            try:
                self._selenium_driver.quit()
            except Exception:
                pass
            self._selenium_driver = None

    # ── Core HTTP methods ──────────────────────────────────────────────

    def _request_json(self, endpoint: str) -> dict | None:
        """Make a GET request expecting JSON response."""
        url = urljoin(self.base_url + "/", endpoint.lstrip("/"))
        headers = {"Accept": "application/json;odata=verbose"}
        try:
            resp = self.session.get(url, headers=headers, timeout=30)
            resp.raise_for_status()
            time.sleep(REQUEST_DELAY)

            ct = resp.headers.get("Content-Type", "")
            if "json" in ct:
                return resp.json()
            elif "atom" in ct or "xml" in ct:
                return self._parse_atom_to_dict(resp.text)
            log.debug("Content-Type inesperado: %s", ct)
            return None
        except requests.RequestException as e:
            log.debug("JSON request falló: %s — %s", url, e)
            return None
        except json.JSONDecodeError:
            try:
                return self._parse_atom_to_dict(resp.text)
            except Exception:
                log.debug("No se pudo parsear respuesta de %s", url)
                return None

    def _request_atom(self, endpoint: str) -> ET.Element | None:
        """Make a GET request expecting Atom XML response."""
        url = urljoin(self.base_url + "/", endpoint.lstrip("/"))
        headers = {"Accept": "application/atom+xml"}
        try:
            resp = self.session.get(url, headers=headers, timeout=30)
            resp.raise_for_status()
            time.sleep(REQUEST_DELAY)
            return ET.fromstring(resp.content)
        except requests.RequestException as e:
            log.debug("Atom request falló: %s — %s", url, e)
            return None
        except ET.ParseError as e:
            log.debug("XML parse error: %s", e)
            return None

    def _request(self, endpoint: str) -> dict | None:
        """Try JSON first, fall back to Atom XML."""
        result = self._request_json(endpoint)
        if result is not None:
            return result

        root = self._request_atom(endpoint)
        if root is not None:
            return self._parse_atom_to_dict(ET.tostring(root, encoding="unicode"))

        return None

    # ── Atom XML parsing ───────────────────────────────────────────────

    def _parse_atom_to_dict(self, xml_text: str) -> dict:
        """Parse Atom XML response into a dict similar to JSON odata format."""
        root = ET.fromstring(xml_text)
        result = {"d": {"results": []}}

        entries = root.findall("atom:entry", ATOM_NS) or root.findall("entry", ATOM_NS)
        for entry in entries:
            item = {}
            props = entry.find(".//m:properties", ATOM_NS)
            if props is not None:
                for child in props:
                    tag = child.tag.split("}")[-1] if "}" in child.tag else child.tag
                    text = child.text or ""
                    if text.startswith("{") or text.startswith("["):
                        try:
                            item[tag] = json.loads(text)
                        except json.JSONDecodeError:
                            item[tag] = text
                    else:
                        item[tag] = text

            links = entry.findall("atom:link", ATOM_NS)
            for link in links:
                rel = link.get("rel", "")
                href = link.get("href", "")
                if rel == "edit-media":
                    item["__media_url"] = href
                elif "File" in rel:
                    item["__file_url"] = href

            result["d"]["results"].append(item)

        if not entries:
            props = root.find(".//m:properties", ATOM_NS)
            if props is not None:
                for child in props:
                    tag = child.tag.split("}")[-1] if "}" in child.tag else child.tag
                    result["d"][tag] = child.text or ""

        return result

    # ── API methods ────────────────────────────────────────────────────

    def get_lists(self) -> list[dict]:
        """Get all lists from the site. Results are cached."""
        if self._list_cache is not None:
            return self._list_cache

        data = self._request("lists")
        if data and "d" in data:
            results = data["d"].get("results", [])
            if not results and isinstance(data["d"], dict):
                results = [data["d"]]
            self._list_cache = results
            return results

        self._list_cache = []
        return []

    def discover_lists(self) -> list[dict]:
        """Discover lists by trying known names and patterns.

        Returns lists that actually have items.
        """
        all_lists = self.get_lists()
        if all_lists:
            log.info("API devolvió %d listas directamente", len(all_lists))
            return all_lists

        # Fallback: try each known section name as a list
        log.info("API directa no devolvió listas. Probando nombres conocidos...")
        discovered = []
        for name in list(SECTIONS.keys()):
            items = self.get_list_items(name, top=1)
            if items:
                discovered.append({
                    "Title": name,
                    "ItemCount": len(self.get_list_items(name, top=500)),
                    "BaseType": 0,
                    "discovered_by": "probe",
                })
                log.info("  ✅ %s — tiene items", name)
            else:
                log.debug("  ❌ %s — sin acceso", name)

        return discovered

    def get_list_items(self, list_title: str, top: int = 500) -> list[dict]:
        """Get items from a specific list by title."""
        encoded_title = quote(list_title, safe="")
        endpoint = f"lists/getbytitle('{encoded_title}')/items?$top={top}"
        data = self._request(endpoint)
        if data and "d" in data:
            return data["d"].get("results", [])
        return []

    def get_list_items_paged(self, list_title: str, batch_size: int = 100) -> list[dict]:
        """Get all items from a list with pagination support."""
        all_items = []
        encoded_title = quote(list_title, safe="")
        skip = 0

        while True:
            endpoint = (
                f"lists/getbytitle('{encoded_title}')/items"
                f"?$top={batch_size}&$skip={skip}"
            )
            data = self._request(endpoint)
            if not data or "d" not in data:
                break

            items = data["d"].get("results", [])
            if not items:
                break

            all_items.extend(items)
            if len(items) < batch_size:
                break
            skip += batch_size

        return all_items

    def get_list_by_id(self, list_id: str, top: int = 500) -> list[dict]:
        """Get items from a list by GUID."""
        endpoint = f"lists(guid'{list_id}')/items?$top={top}"
        data = self._request(endpoint)
        if data and "d" in data:
            return data["d"].get("results", [])
        return []

    def get_web_title(self) -> str | None:
        """Get the title of the web/site."""
        data = self._request("")
        if data and "d" in data:
            return data["d"].get("Title")
        return None

    def download_file(self, server_relative_url: str) -> bytes | None:
        """Download a file from SharePoint by its server-relative URL."""
        base = self.base_url.rsplit("/_api", 1)[0]
        url = f"{base}{server_relative_url}"
        try:
            resp = self.session.get(url, timeout=60)
            resp.raise_for_status()
            return resp.content
        except requests.RequestException as e:
            log.error("Fallo descarga %s: %s", url, e)
            return None

    # ── Selenium-based extraction ──────────────────────────────────────

    def extract_with_selenium(self, section_name: str) -> list[dict]:
        """Use Selenium to extract document links from a section page."""
        driver = self._init_selenium()
        if not driver:
            log.warning("Selenium no disponible, saltando extracción.")
            return []

        section = SECTIONS.get(section_name)
        if not section:
            log.error("Sección desconocida: %s", section_name)
            return []

        url = section["url"]
        log.info("Navegando a %s ...", url)
        try:
            driver.get(url)
            time.sleep(5)

            documents = []
            seen_urls = set()

            # Strategy 1: File links
            links = driver.find_elements(
                "css selector",
                "a[href*='.pdf'], a[href*='.doc'], a[href*='.xls'], a[href*='.pptx'], "
                "a[href*='.docx'], a[href*='.xlsx']",
            )
            for link in links:
                href = link.get_attribute("href")
                title = link.text.strip() or href.split("/")[-1]
                if href and href not in seen_urls:
                    seen_urls.add(href)
                    documents.append({
                        "title": title,
                        "url": href,
                        "section": section_name,
                    })

            # Strategy 2: SharePoint list view table
            rows = driver.find_elements("css selector", "table.ms-listviewtable tr")
            for row in rows:
                cells = row.find_elements("css selector", "td")
                if len(cells) >= 2:
                    try:
                        link = cells[0].find_element("css selector", "a")
                        href = link.get_attribute("href")
                        title = link.text.strip()
                        if href and title and href not in seen_urls:
                            seen_urls.add(href)
                            documents.append({
                                "title": title,
                                "url": href,
                                "section": section_name,
                            })
                    except Exception:
                        pass

            # Strategy 3: Any link with "Document" or file-like patterns
            all_links = driver.find_elements("css selector", "a[href*='Download'], a[href*='download'], a[href*='document']")
            for link in all_links:
                href = link.get_attribute("href")
                title = link.text.strip() or href.split("/")[-1]
                if href and href not in seen_urls:
                    seen_urls.add(href)
                    documents.append({
                        "title": title,
                        "url": href,
                        "section": section_name,
                    })

            log.info("Encontrados %d documentos en '%s'", len(documents), section_name)
            return documents

        except Exception as e:
            log.error("Error extrayendo '%s': %s", section_name, e)
            return []
