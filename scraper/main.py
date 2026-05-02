"""Main entry point for OGP Biblioteca Virtual scraper.

Usage:
    python -m scraper.main              # Explore site structure via REST API
    python -m scraper.main download     # Download all documents via REST API
    python -m scraper.main selenium     # Use Selenium to extract documents
    python -m scraper.main all          # Try API first, fall back to Selenium
    python -m scraper.main csv          # Export items as CSV

Environment variables:
    OGP_DEBUG=1             Enable debug logging
    OGP_USE_SELENIUM=1      Enable Selenium-based extraction
    OGP_SELENIUM_HEADLESS=1 Run Selenium in headless mode (default: 1)
    OGP_OUTPUT_DIR=output   Output directory (default: scraper/output)
    OGP_USERNAME=...        SharePoint username (for authenticated access)
    OGP_PASSWORD=...        SharePoint password
"""

import csv
import json
import os
import sys
from pathlib import Path

from scraper.config import OUTPUT_DIR, SECTIONS, ALTERNATIVE_LIST_NAMES
from scraper.log import log
from scraper.sharepoint_client import SharePointClient


def save_json(data, filename):
    """Save data as JSON to the output directory."""
    Path(OUTPUT_DIR).mkdir(parents=True, exist_ok=True)
    path = os.path.join(OUTPUT_DIR, filename)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    log.info("Guardado %s", path)
    return path


def save_csv(items, filename, fieldnames=None):
    """Save a list of dicts as CSV."""
    if not items:
        log.warning("No hay datos para CSV: %s", filename)
        return

    Path(OUTPUT_DIR).mkdir(parents=True, exist_ok=True)
    path = os.path.join(OUTPUT_DIR, filename)

    if not fieldnames:
        fieldnames = list(items[0].keys())

    with open(path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(items)

    log.info("Guardado CSV %s (%d filas)", path, len(items))
    return path


def export_all_as_csv():
    """Export all scraped data as CSVs."""
    client = SharePointClient()
    try:
        log.info("Exportando datos a CSV...")

        # Discover lists
        lists = client.discover_lists()
        if not lists:
            log.warning("No se encontraron listas para exportar")
            return

        for lst in lists:
            title = lst.get("Title", "")
            if not title:
                continue

            log.info("Exportando '%s'...", title)
            items = client.get_list_items_paged(title)
            if not items:
                continue

            # Flatten nested dicts for CSV
            flat_items = []
            for item in items:
                flat = {}
                for k, v in item.items():
                    if k.startswith("_"):
                        continue
                    if isinstance(v, dict):
                        # Flatten one level
                        for sk, sv in v.items():
                            flat[f"{k}_{sk}"] = str(sv) if not isinstance(sv, (str, int, float)) else sv
                    elif isinstance(v, list):
                        flat[k] = json.dumps(v, ensure_ascii=False)
                    else:
                        flat[k] = v
                flat_items.append(flat)

            safe_name = title.replace(" ", "_").replace("/", "_").lower()
            save_csv(flat_items, f"list_{safe_name}.csv")

        log.info("Exportación CSV completada.")
    finally:
        client.close()


def explore_site():
    """Explore the SharePoint site structure via REST API."""
    client = SharePointClient()
    results = {}

    try:
        # 1. Site info
        log.info("=== Información del Sitio ===")
        title = client.get_web_title()
        log.info("Título: %s", title)
        results["site_title"] = title

        # 2. Discover lists
        log.info("\n=== Listas ===")
        all_lists = client.discover_lists()
        log.info("Total listas encontradas: %d", len(all_lists))

        list_summary = []
        for lst in all_lists:
            info = {
                "title": lst.get("Title", ""),
                "id": lst.get("Id", ""),
                "item_count": lst.get("ItemCount", 0),
                "base_type": lst.get("BaseType", 0),
                "created": lst.get("Created", ""),
            }
            list_summary.append(info)
            log.info("  • %s (%s items)", info["title"], info["item_count"])
        results["lists"] = list_summary
        save_json(list_summary, "site_structure.json")

        # 3. Get items from all discovered lists
        log.info("\n=== Items por Lista ===")
        seen_names = set()
        all_items = {}

        for lst in all_lists:
            title = lst.get("Title", "")
            if not title or title in seen_names:
                continue
            seen_names.add(title)

            log.info("  ─ %s ─", title)
            items = client.get_list_items_paged(title)
            if items:
                log.info("  → %d items", len(items))
                cleaned = []
                for item in items:
                    clean = {k: v for k, v in item.items() if not k.startswith("_")}
                    cleaned.append(clean)

                all_items[title] = cleaned
                safe_name = title.replace(" ", "_").replace("/", "_").lower()
                save_json({"list": title, "items": cleaned}, f"list_{safe_name}.json")

                # Also save CSV
                flat_items = []
                for item in cleaned:
                    flat = {}
                    for k, v in item.items():
                        if isinstance(v, dict):
                            for sk, sv in v.items():
                                flat[f"{k}_{sk}"] = str(sv) if not isinstance(sv, (str, int, float)) else sv
                        elif isinstance(v, list):
                            flat[k] = json.dumps(v, ensure_ascii=False)
                        else:
                            flat[k] = v
                    flat_items.append(flat)
                if flat_items:
                    save_csv(flat_items, f"list_{safe_name}.csv")
            else:
                log.info("  → sin items o sin acceso")
                all_items[title] = []

        save_json(all_items, "all_list_items.json")

        # 4. Document libraries
        log.info("\n=== Bibliotecas de Documentos ===")
        doc_libs = [
            lst for lst in all_lists
            if str(lst.get("BaseType", "")) == "1" or lst.get("BaseType") == 1
        ]

        for lib in doc_libs:
            lib_title = lib.get("Title", "")
            log.info("  %s (%s items)", lib_title, lib.get("ItemCount", 0))
            items = client.get_list_items_paged(lib_title)
            if items:
                files = []
                for item in items:
                    file_info = item.get("File") or item.get("__file_url", "")
                    if file_info:
                        if isinstance(file_info, dict):
                            files.append({
                                "name": item.get("Title", ""),
                                "url": file_info.get("ServerRelativeUrl", ""),
                                "size": file_info.get("Length", 0),
                            })
                        elif isinstance(file_info, str):
                            files.append({
                                "name": item.get("Title", ""),
                                "url": file_info,
                            })
                if files:
                    safe_name = lib_title.replace(" ", "_").lower()
                    save_json({"library": lib_title, "files": files}, f"library_{safe_name}.json")
                    log.info("    → %d archivos", len(files))

    finally:
        client.close()

    log.info("\n✅ Exploración completada. Datos en %s/", OUTPUT_DIR)
    return results


def download_documents(output_subdir: str = "documents"):
    """Download all discoverable documents from the site via REST API."""
    client = SharePointClient()
    download_dir = os.path.join(OUTPUT_DIR, output_subdir)
    Path(download_dir).mkdir(parents=True, exist_ok=True)

    try:
        all_lists = client.get_lists()
        doc_libs = [
            lst for lst in all_lists
            if str(lst.get("BaseType", "")) == "1" or lst.get("BaseType") == 1
        ]

        if not doc_libs:
            log.warning("No se encontraron bibliotecas de documentos vía API.")
            log.info("Prueba 'python -m scraper.main selenium' como alternativa.")

        total = 0
        for lib in doc_libs:
            lib_title = lib.get("Title", "")
            items = client.get_list_items_paged(lib_title)
            if not items:
                continue

            for item in items:
                file_info = item.get("File")
                if not file_info:
                    continue

                file_url = ""
                if isinstance(file_info, dict):
                    file_url = file_info.get("ServerRelativeUrl", "")
                elif isinstance(file_info, str):
                    file_url = file_info

                if not file_url:
                    continue

                filename = file_url.split("/")[-1]
                if not filename:
                    continue

                log.info("Descargando: %s", filename)
                content = client.download_file(file_url)
                if content:
                    filepath = os.path.join(download_dir, filename)
                    with open(filepath, "wb") as f:
                        f.write(content)
                    total += 1

        log.info("\n✅ Descargados %d archivos a %s/", total, download_dir)
        return total

    finally:
        client.close()


def extract_with_selenium():
    """Use Selenium to extract documents from all sections."""
    client = SharePointClient()
    all_documents = []

    try:
        log.info("=== Extracción con Selenium ===")
        for section_name in SECTIONS:
            log.info("  ─ %s ─", section_name)
            docs = client.extract_with_selenium(section_name)
            all_documents.extend(docs)
            log.info("  → %d documentos", len(docs))

        if all_documents:
            save_json(
                {"sections": list(SECTIONS.keys()), "documents": all_documents},
                "selenium_documents.json",
            )
            save_csv(all_documents, "selenium_documents.csv",
                     fieldnames=["title", "url", "section"])

        log.info("\n✅ Total documentos encontrados: %d", len(all_documents))
        return all_documents

    finally:
        client.close()


def run_all():
    """Try API first, then Selenium fallback."""
    log.info("=== Fase 1: API REST ===\n")
    try:
        explore_site()
    except Exception as e:
        log.error("API exploration falló: %s", e)

    log.info("\n=== Fase 2: Descarga de Documentos ===\n")
    try:
        download_documents()
    except Exception as e:
        log.error("Descarga falló: %s", e)

    if os.getenv("OGP_USE_SELENIUM") == "1":
        log.info("\n=== Fase 3: Selenium ===\n")
        try:
            extract_with_selenium()
        except Exception as e:
            log.error("Selenium falló: %s", e)


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "explore"

    if mode == "download":
        download_documents()
    elif mode == "selenium":
        extract_with_selenium()
    elif mode == "csv":
        export_all_as_csv()
    elif mode == "all":
        run_all()
    else:
        explore_site()
