"""Main entry point for OGP Biblioteca Virtual scraper via SharePoint REST API."""

import json
import os
from pathlib import Path

from scraper.config import LISTS_OF_INTEREST, OUTPUT_DIR, SITE_URL
from scraper.sharepoint_client import SharePointClient


def save_json(data: dict, filename: str):
    """Save data as JSON to the output directory."""
    Path(OUTPUT_DIR).mkdir(parents=True, exist_ok=True)
    path = os.path.join(OUTPUT_DIR, filename)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"[OK] Saved {path}")


def explore_site():
    """Explore the SharePoint site structure via REST API."""
    client = SharePointClient()

    # 1. Get site info
    print("=== Site Info ===")
    title = client.get_web_title()
    print(f"Site title: {title}")

    # 2. Get all lists
    print("\n=== Lists ===")
    all_lists = client.get_lists()
    print(f"Found {len(all_lists)} lists total")

    list_summary = []
    for lst in all_lists:
        info = {
            "title": lst.get("Title", ""),
            "id": lst.get("Id", ""),
            "item_count": lst.get("ItemCount", 0),
            "base_type": lst.get("BaseType", ""),
            "created": lst.get("Created", ""),
        }
        list_summary.append(info)
        print(f"  - {info['title']} ({info['item_count']} items)")

    save_json({"site_title": title, "lists": list_summary}, "site_structure.json")

    # 3. Get items from lists of interest
    print("\n=== List Items ===")
    all_items = {}
    for list_name in LISTS_OF_INTEREST:
        print(f"\n--- {list_name} ---")
        items = client.get_list_items(list_name)
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
            save_json({"list": list_name, "items": cleaned}, f"list_{list_name.replace(' ', '_').lower()}.json")
        else:
            print(f"  No items or list not accessible")
            all_items[list_name] = []

    save_json(all_items, "all_list_items.json")

    # 4. Try to discover document libraries
    print("\n=== Document Libraries ===")
    doc_libs = [lst for lst in all_lists if lst.get("BaseType", 0) == 1]  # BaseType 1 = Document Library
    for lib in doc_libs:
        lib_title = lib.get("Title", "")
        print(f"  Library: {lib_title} ({lib.get('ItemCount', 0)} items)")
        items = client.get_list_items(lib_title)
        if items:
            files = []
            for item in items:
                if "File" in item and item["File"]:
                    files.append({
                        "name": item.get("Title", ""),
                        "url": item["File"].get("ServerRelativeUrl", ""),
                        "size": item["File"].get("Length", 0),
                    })
            if files:
                save_json({"library": lib_title, "files": files}, f"library_{lib_title.replace(' ', '_').lower()}.json")
                print(f"    Extracted {len(files)} files")

    print("\nDone! All data saved to output/")
    return all_items


def download_documents(output_subdir: str = "documents"):
    """Download all discoverable documents from the site."""
    client = SharePointClient()
    download_dir = os.path.join(OUTPUT_DIR, output_subdir)
    Path(download_dir).mkdir(parents=True, exist_ok=True)

    # Get all lists and find files
    all_lists = client.get_lists()
    doc_libs = [lst for lst in all_lists if lst.get("BaseType", 0) == 1]

    downloaded = 0
    for lib in doc_libs:
        lib_title = lib.get("Title", "")
        items = client.get_list_items(lib_title)
        if not items:
            continue

        for item in items:
            if "File" in item and item["File"]:
                file_url = item["File"].get("ServerRelativeUrl", "")
                if not file_url:
                    continue

                # Get filename from URL
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


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "download":
        download_documents()
    else:
        explore_site()
