import base64
import logging
import os
from pathlib import Path
from urllib.parse import quote

import requests

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class GiteeService:
    """Compatibility wrapper used by the existing routes.

    The original project read compose files from Gitee. This fork keeps the
    route names stable, but reads from GitHub by default.
    """

    def __init__(self, token=None):
        self.repo = os.environ.get("GITHUB_REPO", "wuyou69/Docker-Compose-Manager")
        self.api_base_url = os.environ.get("GITHUB_API_URL", "https://api.github.com")
        self.content_root = os.environ.get("GITHUB_CONTENT_ROOT", "compose-files").strip("/")
        self.branch = os.environ.get("GITHUB_BRANCH", "main")
        self.token = token or os.environ.get("GITHUB_TOKEN", "")
        self.base_data_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
            "data",
        )

    def _get_headers(self):
        headers = {
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers

    def _contents_url(self, path=""):
        parts = [self.content_root, path.strip("/")]
        repo_path = "/".join(part for part in parts if part)
        encoded_path = "/".join(quote(part) for part in repo_path.split("/") if part)
        return f"{self.api_base_url}/repos/{self.repo}/contents/{encoded_path}"

    def _request_params(self):
        return {"ref": self.branch} if self.branch else {}

    def get_files_list(self, system_type):
        try:
            if not system_type or not isinstance(system_type, str):
                return False, {"error": "Invalid system type"}

            response = requests.get(
                self._contents_url(system_type),
                headers=self._get_headers(),
                params=self._request_params(),
                timeout=20,
            )

            if response.status_code == 404:
                return True, {"files": []}
            if response.status_code != 200:
                return False, {"error": f"GitHub API request failed: {response.status_code}"}

            items = response.json()
            if not isinstance(items, list):
                return False, {"error": "GitHub API returned an unexpected response"}

            yaml_files = []
            for item in items:
                name = item.get("name", "")
                if item.get("type") != "file" or not name.endswith((".yml", ".yaml")):
                    continue
                local_path = os.path.join(self.base_data_path, system_type, name)
                yaml_files.append(
                    {
                        "name": name,
                        "size": item.get("size", 0),
                        "updated_at": "",
                        "download_url": item.get("download_url", ""),
                        "exists_locally": os.path.exists(local_path),
                    }
                )

            return True, {"files": yaml_files}
        except requests.exceptions.RequestException as exc:
            logger.error("Failed to list GitHub files: %s", exc)
            return False, {"error": f"Failed to list GitHub files: {exc}"}
        except Exception as exc:
            logger.exception("Unexpected error while listing GitHub files")
            return False, {"error": str(exc)}

    def download_file(self, download_url, system_type, filename):
        try:
            if not download_url:
                download_url = self._contents_url(f"{system_type}/{filename}")
                response = requests.get(
                    download_url,
                    headers=self._get_headers(),
                    params=self._request_params(),
                    timeout=20,
                )
                response.raise_for_status()
                file_data = response.json()
                content = base64.b64decode(file_data["content"])
            else:
                response = requests.get(download_url, headers=self._get_headers(), timeout=30)
                response.raise_for_status()
                content = response.content

            system_dir = os.path.join(self.base_data_path, system_type)
            os.makedirs(system_dir, exist_ok=True)
            file_path = os.path.join(system_dir, filename)
            with open(file_path, "wb") as f:
                f.write(content)

            return True, {"file_path": file_path}
        except Exception as exc:
            logger.error("Failed to download GitHub file: %s", exc)
            return False, {"error": f"File download failed: {exc}"}

    def get_file_content(self, file_path):
        try:
            if os.path.exists(file_path):
                with open(file_path, "r", encoding="utf-8") as f:
                    return True, f.read(), {"source": "local"}

            relative_path = Path(file_path).relative_to(self.base_data_path).as_posix()
            response = requests.get(
                self._contents_url(relative_path),
                headers=self._get_headers(),
                params=self._request_params(),
                timeout=20,
            )
            if response.status_code == 404:
                return False, None, {"error": "File not found"}
            response.raise_for_status()

            file_data = response.json()
            content = base64.b64decode(file_data["content"]).decode("utf-8")
            return True, content, {"source": "github"}
        except Exception as exc:
            logger.error("Failed to get file content: %s", exc)
            return False, None, {"error": str(exc)}

    def update_file(self, file_path, content):
        try:
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)
            return True, {"file_path": file_path}
        except Exception as exc:
            return False, {"error": str(exc)}

    def get_system_types(self):
        return [
            {"key": "fnOS", "name": "飞牛系统 (fnOS)"},
            {"key": "QNAP", "name": "威联通系统 (QNAP)"},
            {"key": "Synology", "name": "群晖系统 (Synology)"},
            {"key": "TrueNAS", "name": "TrueNAS"},
            {"key": "UgreenNew", "name": "绿联系统 (UgreenNew)"},
            {"key": "Ugreen", "name": "绿联旧系统 (Ugreen)"},
            {"key": "ZSpace", "name": "极空间系统 (ZSpace)"},
            {"key": "ZimaOS", "name": "ZimaOS"},
        ]

    def check_file_exists_remote(self, system_type, filename):
        response = requests.get(
            self._contents_url(f"{system_type}/{filename}"),
            headers=self._get_headers(),
            params=self._request_params(),
            timeout=20,
        )
        if response.status_code == 200:
            return True, {"exists": True, "file_info": response.json()}
        if response.status_code == 404:
            return True, {"exists": False}
        return False, {"error": f"GitHub API request failed: {response.status_code}"}

    def get_repo_info(self):
        try:
            response = requests.get(
                f"{self.api_base_url}/repos/{self.repo}",
                headers=self._get_headers(),
                timeout=20,
            )
            response.raise_for_status()
            return True, response.json()
        except Exception as exc:
            return False, {"error": str(exc)}

    def search_files(self, keyword, system_type=None):
        results = []
        systems = [{"key": system_type}] if system_type else self.get_system_types()
        for system in systems:
            success, data = self.get_files_list(system["key"])
            if not success:
                continue
            for file in data.get("files", []):
                if keyword.lower() in file["name"].lower():
                    file["system_type"] = system["key"]
                    results.append(file)
        return True, {"files": results}

    def validate_download_url(self, url):
        if not url.startswith(("https://raw.githubusercontent.com/", "https://github.com/")):
            return False, "URL is not a GitHub file URL"
        try:
            response = requests.head(url, allow_redirects=True, timeout=10)
            return response.status_code == 200, {"valid": response.status_code == 200}
        except Exception as exc:
            return False, {"error": str(exc)}

    def get_file_history(self, system_type, filename):
        return True, {"history": []}

    def get_latest_updates(self, limit=5):
        all_files = []
        for system in self.get_system_types():
            success, data = self.get_files_list(system["key"])
            if success:
                for file in data.get("files", []):
                    file["system_type"] = system["key"]
                    file["system_name"] = system["name"]
                    all_files.append(file)
        return True, {"files": all_files[:limit]}
