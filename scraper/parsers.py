"""Parsing logic for OGP Biblioteca Virtual (SharePoint-based)."""

import re
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from scraper.config import BASE_URL


def parse_main_page(html: str) -> dict:
    """Parse the main landing page of the Biblioteca Virtual."""
    soup = BeautifulSoup(html, "html.parser")
    result = {
        "title": "",
        "description": "",
        "sections": [],
        "links": [],
    }

    # Title
    title_el = soup.find("h1")
    if title_el:
        result["title"] = title_el.get_text(strip=True)

    # Description paragraphs
    desc_parts = []
    for p in soup.find_all("p"):
        text = p.get_text(strip=True)
        if text and len(text) > 30:
            desc_parts.append(text)
    result["description"] = " ".join(desc_parts)

    # Extract section links from the page
    for a in soup.find_all("a", href=True):
        href = a["href"]
        text = a.get_text(strip=True)
        if text and not href.startswith("#") and not href.startswith("javascript"):
            full_url = urljoin(BASE_URL, href)
            # Check if it's an internal SharePoint page
            if "/ogp/Bvirtual/" in full_url or "bvirtualogp" in full_url:
                result["links"].append({
                    "text": text,
                    "url": full_url,
                })
                # Identify sections by keywords
                keywords = {
                    "leyes orgánicas": "leyes_organicas",
                    "leyes de referencia": "leyes_referencia",
                    "reorganización": "reorganizacion",
                    "resoluciones conjuntas": "resoluciones_presupuesto",
                    "memoriales explicativos": "memoriales",
                }
                for kw, section_key in keywords.items():
                    if kw in text.lower():
                        result["sections"].append({
                            "key": section_key,
                            "text": text,
                            "url": full_url,
                        })

    return result


def parse_sharepoint_list_page(html: str, section_name: str) -> dict:
    """Parse a SharePoint list page to extract document links."""
    soup = BeautifulSoup(html, "html.parser")
    result = {
        "section": section_name,
        "title": "",
        "documents": [],
        "subcategories": [],
    }

    # Title
    title_el = soup.find("h1")
    if title_el:
        result["title"] = title_el.get_text(strip=True)

    # Try to find SharePoint list items
    # SharePoint often uses <table> with class ms-listviewtable
    table = soup.find("table", class_=re.compile(r"ms-listviewtable"))
    if table:
        for row in table.find_all("tr")[1:]:  # skip header
            cols = row.find_all("td")
            if cols:
                link = cols[0].find("a") if cols[0] else None
                if link and link.get("href"):
                    doc = {
                        "title": link.get_text(strip=True),
                        "url": urljoin(BASE_URL, link["href"]),
                    }
                    # Check for file type
                    if link["href"].lower().endswith((".pdf", ".doc", ".docx", ".xls", ".xlsx")):
                        doc["type"] = link["href"].split(".")[-1]
                    result["documents"].append(doc)

    # Fallback: look for any anchor tags with document extensions
    if not result["documents"]:
        for a in soup.find_all("a", href=True):
            href = a["href"].lower()
            text = a.get_text(strip=True)
            if text and any(href.endswith(ext) for ext in [".pdf", ".doc", ".docx", ".xls", ".xlsx"]):
                result["documents"].append({
                    "title": text,
                    "url": urljoin(BASE_URL, a["href"]),
                    "type": href.split(".")[-1],
                })

    # Extract subcategory links
    for a in soup.find_all("a", href=True):
        href = a["href"]
        text = a.get_text(strip=True)
        if text and ("/ogp/Bvirtual/" in href or "bvirtualogp" in href):
            if text.lower() not in [section_name.lower(), result["title"].lower()]:
                result["subcategories"].append({
                    "text": text,
                    "url": urljoin(BASE_URL, href),
                })

    return result
