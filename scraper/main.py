"""Main entry point for OGP Biblioteca Virtual scraper."""

import json
import os
import time
from pathlib import Path

import requests
from bs4 import BeautifulSoup

from scraper.config import BASE_URL, HEADERS, REQUEST_DELAY, OUTPUT_DIR, SECTIONS
from scraper.parsers import parse_main_page, parse_sharepoint_list_page


def fetch(url: str) -> str | None:
    """Fetch a URL with error handling."""
    try:
        resp = requests.get(url, headers=HEADERS, timeout=30)
        resp.raise_for_status()
        return resp.text
    except requests.RequestException as e:
        print(f"[ERROR] Failed to fetch {url}: {e}")
        return None


def save_json(data: dict, filename: str):
    """Save data as JSON to the output directory."""
    Path(OUTPUT_DIR).mkdir(parents=True, exist_ok=True)
    path = os.path.join(OUTPUT_DIR, filename)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"[OK] Saved {path}")


def discover_sections(html: str) -> list[dict]:
    """Discover section URLs from the main page by parsing links."""
    soup = BeautifulSoup(html, "html.parser")
    sections = []
    seen_urls = set()

    for a in soup.find_all("a", href=True):
        href = a["href"]
        text = a.get_text(strip=True)
        if not text or href.startswith("#") or href.startswith("javascript"):
            continue

        full_url = href if href.startswith("http") else f"{BASE_URL}{href}"
        if full_url in seen_urls:
            continue

        if "/ogp/Bvirtual/" in full_url or "bvirtualogp" in full_url:
            seen_urls.add(full_url)
            sections.append({
                "text": text,
                "url": full_url,
            })

    return sections


def scrape_all():
    """Scrape all known sections of the Biblioteca Virtual."""
    print(f"Starting scrape of OGP Biblioteca Virtual: {BASE_URL}")
    results = {}

    # 1. Main page
    print("\n--- Scraping main page ---")
    html = fetch(f"{BASE_URL}{SECTIONS['inicio']}")
    if html:
        data = parse_main_page(html)
        results["inicio"] = data
        save_json(data, "inicio.json")
        time.sleep(REQUEST_DELAY)

        # Discover more sections from main page
        discovered = discover_sections(html)
        print(f"  Discovered {len(discovered)} links on main page")
        results["_discovered_links"] = discovered
        save_json({"links": discovered}, "discovered_links.json")

    # 2. Try each known section
    for name, path in SECTIONS.items():
        if name == "inicio":
            continue

        url = f"{BASE_URL}{path}"
        print(f"\n--- Scraping {name}: {url} ---")
        html = fetch(url)
        if not html:
            print(f"  [SKIP] Could not fetch {name}")
            continue

        data = parse_sharepoint_list_page(html, name)
        results[name] = data
        save_json(data, f"{name}.json")
        print(f"  Found {len(data.get('documents', []))} documents")
        time.sleep(REQUEST_DELAY)

    # Save full report
    save_json(results, "full_report.json")
    print(f"\nDone! Scraped {len(results)} sections.")
    return results


def scrape_section(section_key: str):
    """Scrape a single section by key."""
    if section_key not in SECTIONS:
        print(f"[ERROR] Unknown section '{section_key}'. Options: {list(SECTIONS.keys())}")
        return None

    url = f"{BASE_URL}{SECTIONS[section_key]}"
    html = fetch(url)
    if not html:
        return None

    if section_key == "inicio":
        data = parse_main_page(html)
    else:
        data = parse_sharepoint_list_page(html, section_key)

    save_json(data, f"{section_key}.json")
    print(f"Found {len(data.get('documents', []))} documents in {section_key}")
    return data


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        scrape_section(sys.argv[1])
    else:
        scrape_all()
