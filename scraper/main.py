"""Main entry point for OGP Biblioteca Virtual scraper.

Usage:
    python -m scraper.main              # Explore site structure via REST API
    python -m scraper.main download     # Download all documents via REST API
    python -m scraper.main selenium     # Use Selenium to extract documents
    python -m scraper.main all          # Try API first, fall back to Selenium

Environment variables:
    OGP_USE_SELENIUM=1      Enable Selenium-based extraction
    OGP_SELENIUM_HEADLESS=1 Run Selenium in headless mode (default: 1)
    OGP_OUTPUT_DIR=output   Output directory (default: scraper/output)
    OGP_USERNAME=...        SharePoint username (for authenticated access)
    OGP_PASSWORD=...        SharePoint password
"""

import json
import os
import sys
from pathlib import Path

from scraper.config import OUTPUT_DIR, SECTIONS, ALTERNATIVE_LIST_NAMES
from scraper.sharepoint_client import SharePointClient


def save_json(data, filename):
    """Save data as JSON to the output directory."""
    Path(OUTPUT_DIR).mkdir(parents=True, exist_ok=True)
    path = os.path.join(OUTPUT_DIR, filename)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"  [OK] Saved {path}")


def explore_site():
    """Explore the SharePoint site structure via REST API."""
    client = SharePointClient()
    results = {}

    try:
        # 1. Get site info
        print("=== Site Info ===")
        title = client.get_web_title()
        print(f"  Site title: {title}")
        results["site_title"] = title

        # 2. Get all lists
        print("\n=== Lists ===")
        all_lists = client.get_lists()
        print(f"  Found {len(all_lists)} lists total")

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
            print(f"  - {info['title']} ({info['item_count']} items)")
        results["lists"] = list_summary
        save_json(list_summary, "site_structure.json")

        # 3. Get items from known sections + alternative list names
        print("\n=== List Items ===")
        all_list_names = list(SECTIONS.keys()) + ALTERNATIVE_LIST_NAMES
        seen_names = set()
        all_items = {}

        for list_name in all_list_names:
            if list_name in seen_names:
                continue
            seen_names.add(list_name)

            print(f"\n  --- {list_name} ---")
            items = client.get_list_items_paged(list_name)
            if items:
                print(f"  Found {len(items)} items")
                # Clean items for serialization
                cleaned = []
                for item in items:
                    clean = {}
                    for k, v in item.items():
                        if not k.startswith("_"):
                            clean[k] = v
                    cleaned.append(clean)

                all_items[list_name] = cleaned
                filename = f"list_{list_name.replace(' ', '_').replace('/', '_').lower()}.json"
                save_json({"list": list_name, "items": cleaned}, filename)
            else:
                print(f"  No items or list not accessible")
                all_items[list_name] = []

        save_json(all_items, "all_list_items.json")

        # 4. Try to discover document libraries
        print("\n=== Document Libraries ===")
        doc_libs = [lst for lst in all_lists if str(lst.get("BaseType", "")) == "1"]
        if not doc_libs:
            doc_libs = [lst for lst in all_lists if lst.get("BaseType") == 1]

        for lib in doc_libs:
            lib_title = lib.get("Title", "")
            print(f"  Library: {lib_title} ({lib.get('ItemCount', 0)} items)")
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
                    filename = f"library_{lib_title.replace(' ', '_').lower()}.json"
                    save_json({"library": lib_title, "files": files}, filename)
                    print(f"    Extracted {len(files)} files")

    finally:
        client.close()

    print("\nDone! All data saved to output/")
    return results


def download_documents(output_subdir: str = "documents"):
    """Download all discoverable documents from the site via REST API."""
    client = SharePointClient()
    download_dir = os.path.join(OUTPUT_DIR, output_subdir)
    Path(download_dir).mkdir(parents=True, exist_ok=True)

    try:
        # Get all lists and find files
        all_lists = client.get_lists()
        doc_libs = [lst for lst in all_lists if str(lst.get("BaseType", "")) == "1"]
        if not doc_libs:
            doc_libs = [lst for lst in all_lists if lst.get("BaseType") == 1]

        downloaded = 0
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

                print(f"  Downloading: {filename}")
                content = client.download_file(file_url)
                if content:
                    filepath = os.path.join(download_dir, filename)
                    with open(filepath, "wb") as f:
                        f.write(content)
                    downloaded += 1

        print(f"\nDownloaded {downloaded} files to {download_dir}/")
        return downloaded

    finally:
        client.close()


def extract_with_selenium():
    """Use Selenium to extract documents from all sections."""
    client = SharePointClient()
    all_documents = []

    try:
        print("=== Selenium Extraction ===")
        for section_name in SECTIONS:
            print(f"\n--- {section_name} ---")
            docs = client.extract_with_selenium(section_name)
            all_documents.extend(docs)
            print(f"  Found {len(docs)} documents")

        save_json({"sections": list(SECTIONS.keys()), "documents": all_documents}, "selenium_documents.json")
        print(f"\nTotal documents found: {len(all_documents)}")
        return all_documents

    finally:
        client.close()


def run_all():
    """Try API first, then Selenium fallback."""
    print("=== Phase 1: REST API Exploration ===\n")
    try:
        explore_site()
    except Exception as e:
        print(f"[ERROR] API exploration failed: {e}")

    print("\n=== Phase 2: Download Documents via API ===\n")
    try:
        download_documents()
    except Exception as e:
        print(f"[ERROR] API download failed: {e}")

    if USE_SELENIUM or os.getenv("OGP_USE_SELENIUM") == "1":
        print("\n=== Phase 3: Selenium Extraction ===\n")
        try:
            extract_with_selenium()
        except Exception as e:
            print(f"[ERROR] Selenium extraction failed: {e}")


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "explore"

    if mode == "download":
        download_documents()
    elif mode == "selenium":
        extract_with_selenium()
    elif mode == "all":
        run_all()
    else:
        explore_site()
