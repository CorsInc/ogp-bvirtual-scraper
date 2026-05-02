"""SharePoint REST API client for OGP Biblioteca Virtual."""

import json
import time
from urllib.parse import quote, urljoin

import requests

from scraper.config import API_URL, HEADERS, REQUEST_DELAY


class SharePointClient:
    """Minimal SharePoint REST API client."""

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(HEADERS)
        self.base_url = API_URL

    def _request(self, endpoint: str, accept: str = "application/json;odata=verbose") -> dict | None:
        """Make a GET request to the SharePoint REST API."""
        url = urljoin(self.base_url + "/", endpoint.lstrip("/"))
        headers = {"Accept": accept}
        try:
            resp = self.session.get(url, headers=headers, timeout=30)
            resp.raise_for_status()
            time.sleep(REQUEST_DELAY)
            return resp.json()
        except requests.RequestException as e:
            print(f"[ERROR] API request failed: {url} — {e}")
            return None
        except json.JSONDecodeError:
            print(f"[ERROR] Non-JSON response from {url}")
            return None

    def get_lists(self) -> list[dict]:
        """Get all lists from the site."""
        data = self._request("lists")
        if data and "d" in data and "results" in data["d"]:
            return data["d"]["results"]
        return []

    def get_list_items(self, list_title: str, top: int = 100) -> list[dict]:
        """Get items from a specific list by title."""
        encoded_title = quote(list_title, safe="")
        data = self._request(
            f"lists/getbytitle('{encoded_title}')/items?$top={top}"
        )
        if data and "d" and "results" in data.get("d", {}):
            return data["d"]["results"]
        return []

    def get_list_by_id(self, list_id: str, top: int = 100) -> list[dict]:
        """Get items from a list by GUID."""
        data = self._request(
            f"lists(guid'{list_id}')/items?$top={top}"
        )
        if data and "d" and "results" in data.get("d", {}):
            return data["d"]["results"]
        return []

    def get_web_title(self) -> str | None:
        """Get the title of the web/site."""
        data = self._request("")
        if data and "d" and "Title" in data["d"]:
            return data["d"]["Title"]
        return None

    def get_folders(self, list_title: str) -> list[dict]:
        """Get folders from a document library."""
        encoded_title = quote(list_title, safe="")
        data = self._request(
            f"lists/getbytitle('{encoded_title}')/items?$select=Title,FileSystemObjectType,File&$filter=FileSystemObjectType eq 1"
        )
        if data and "d" and "results" in data.get("d", {}):
            return data["d"]["results"]
        return []

    def get_files_in_folder(self, list_title: str, folder_path: str) -> list[dict]:
        """Get files from a specific folder in a document library."""
        encoded_list = quote(list_title, safe="")
        encoded_folder = quote(folder_path, safe="/")
        data = self._request(
            f"lists/getbytitle('{encoded_list}')/items?$select=Title,File/ServerRelativeUrl,File/Length&$expand=File&$filter=startswith(File/ServerRelativeUrl,'{encoded_folder}')"
        )
        if data and "d" and "results" in data.get("d", {}):
            return data["d"]["results"]
        return []

    def download_file(self, server_relative_url: str) -> bytes | None:
        """Download a file from SharePoint by its server-relative URL."""
        url = f"{self.base_url.rsplit('/_api', 1)[0]}{server_relative_url}"
        try:
            resp = self.session.get(url, timeout=60)
            resp.raise_for_status()
            return resp.content
        except requests.RequestException as e:
            print(f"[ERROR] Failed to download {url}: {e}")
            return None
