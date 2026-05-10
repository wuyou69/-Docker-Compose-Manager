import os

import requests
import yaml
from flask import Blueprint, jsonify, request, session

from app import db
from app.models.user import DockerComposeFile
from app.services.gitee_service import GiteeService

gitee_bp = Blueprint("gitee", __name__)

system_types = {
    "fnOS": "飞牛系统",
    "QNAP": "威联通系统",
    "Synology": "群晖系统",
    "TrueNAS": "TrueNAS",
    "UgreenNew": "绿联系统",
    "Ugreen": "绿联旧系统",
    "ZSpace": "极空间系统",
    "ZimaOS": "ZimaOS",
}


def _require_login():
    return "user_id" in session


def _remote_service():
    return GiteeService(token=session.get("gitee_token", ""))


@gitee_bp.route("/api/gitee/files/<system_type>", methods=["GET"])
def get_gitee_files(system_type):
    """Get compose files from the configured GitHub repository."""
    if not _require_login():
        return jsonify({"error": "Not authenticated"}), 401
    if system_type not in system_types:
        return jsonify({"error": f"Invalid system type. Available: {list(system_types.keys())}"}), 400

    success, data = _remote_service().get_files_list(system_type)
    if not success:
        return jsonify({"error": data.get("error", "Unknown error")}), 500

    result = []
    for file in data.get("files", []):
        existing_file = DockerComposeFile.query.filter_by(
            filename=file["name"],
            system_type=system_type,
            source="github",
        ).first()
        result.append(
            {
                "name": file.get("name", "Unknown"),
                "download_url": file.get("download_url", ""),
                "size": file.get("size", 0),
                "updated_at": file.get("updated_at", ""),
                "exists_locally": file.get("exists_locally", False) or existing_file is not None,
            }
        )

    return jsonify(
        {
            "success": True,
            "system_type": system_type,
            "system_name": system_types[system_type],
            "files": result,
            "total": len(result),
        }
    )


@gitee_bp.route("/api/gitee/download", methods=["POST"])
def download_gitee_file():
    """Download a compose file from GitHub into local data storage."""
    if not _require_login():
        return jsonify({"error": "Not authenticated"}), 401

    data = request.json or {}
    download_url = data.get("download_url")
    system_type = data.get("system_type")
    filename = data.get("filename")
    if not download_url or not system_type or not filename:
        return jsonify({"error": "Missing required parameters"}), 400
    if system_type not in system_types:
        return jsonify({"error": "Invalid system type"}), 400

    success, result = _remote_service().download_file(download_url, system_type, filename)
    if not success:
        return jsonify(result), 500

    file_path = result["file_path"]
    existing_file = DockerComposeFile.query.filter_by(
        filename=filename,
        system_type=system_type,
        source="github",
    ).first()

    if existing_file:
        existing_file.file_path = file_path
    else:
        db.session.add(
            DockerComposeFile(
                filename=filename,
                system_type=system_type,
                source="github",
                file_path=file_path,
            )
        )
    db.session.commit()

    return jsonify(
        {
            "success": True,
            "message": "File downloaded successfully",
            "file_path": file_path,
            "size": os.path.getsize(file_path),
        }
    )


@gitee_bp.route("/api/gitee/system-types", methods=["GET"])
def get_system_types():
    """Get all available system types from GitHub, with a local fallback."""
    if not _require_login():
        return jsonify({"error": "Not authenticated"}), 401

    token = session.get("gitee_token", "")
    api_url = os.environ.get("GITHUB_API_URL", "https://api.github.com")
    repo = os.environ.get("GITHUB_REPO", "wuyou69/Docker-Compose-Manager")
    content_root = os.environ.get("GITHUB_CONTENT_ROOT", "compose-files").strip("/")
    branch = os.environ.get("GITHUB_BRANCH", "main")
    headers = {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"

    try:
        response = requests.get(
            f"{api_url}/repos/{repo}/contents/{content_root}",
            params={"ref": branch} if branch else {},
            headers=headers,
            timeout=10,
        )
        if response.status_code == 200:
            contents = response.json()
            available_systems = [
                {"key": item["name"], "name": system_types[item["name"]]}
                for item in contents
                if isinstance(item, dict) and item.get("type") == "dir" and item.get("name") in system_types
            ]
            if available_systems:
                return jsonify({"success": True, "system_types": available_systems})
    except Exception:
        pass

    return jsonify({"success": True, "system_types": [{"key": k, "name": v} for k, v in system_types.items()]})


@gitee_bp.route("/api/gitee/file-content", methods=["POST"])
def get_file_content():
    if not _require_login():
        return jsonify({"error": "Not authenticated"}), 401

    file_path = (request.json or {}).get("file_path")
    if not file_path:
        return jsonify({"error": "File path required"}), 400
    if not os.path.exists(file_path):
        return jsonify({"error": "File not found"}), 404

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
        try:
            yaml_data = yaml.safe_load(content)
            return jsonify({"success": True, "content": content, "parsed": True, "yaml_data": yaml_data})
        except Exception as exc:
            return jsonify({"success": True, "content": content, "parsed": False, "error": str(exc)})
    except Exception as exc:
        return jsonify({"error": f"Error reading file: {exc}"}), 500


@gitee_bp.route("/api/gitee/update-file", methods=["POST"])
def update_file_content():
    if not _require_login():
        return jsonify({"error": "Not authenticated"}), 401

    data = request.json or {}
    file_path = data.get("file_path")
    content = data.get("content")
    if not file_path or content is None:
        return jsonify({"error": "Missing required parameters"}), 400

    try:
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)
        return jsonify({"success": True, "message": "File updated successfully"})
    except Exception as exc:
        return jsonify({"error": f"Error updating file: {exc}"}), 500


@gitee_bp.route("/api/local/files", methods=["GET"])
def get_local_files():
    if not _require_login():
        return jsonify({"error": "Not authenticated"}), 401

    try:
        all_files = []
        for system_type in system_types.keys():
            system_dir = os.path.join("/app/data", system_type)
            if not os.path.exists(system_dir):
                continue
            for filename in os.listdir(system_dir):
                if not filename.endswith((".yml", ".yaml")):
                    continue
                file_path = os.path.join(system_dir, filename)
                stat = os.stat(file_path)
                all_files.append(
                    {
                        "filename": filename,
                        "system_type": system_type,
                        "system_name": system_types[system_type],
                        "file_path": file_path,
                        "size": stat.st_size,
                        "mtime": stat.st_mtime,
                        "source": "github",
                    }
                )

        local_dir = os.path.join("/app/data", "local")
        if os.path.exists(local_dir):
            for filename in os.listdir(local_dir):
                if filename.endswith((".yml", ".yaml")):
                    file_path = os.path.join(local_dir, filename)
                    stat = os.stat(file_path)
                    all_files.append(
                        {
                            "filename": filename,
                            "system_type": "local",
                            "system_name": "本地文件",
                            "file_path": file_path,
                            "size": stat.st_size,
                            "mtime": stat.st_mtime,
                            "source": "local",
                        }
                    )

        all_files.sort(key=lambda x: x["mtime"], reverse=True)
        return jsonify({"success": True, "files": all_files, "total": len(all_files)})
    except Exception as exc:
        return jsonify({"error": f"Error fetching local files: {exc}"}), 500


@gitee_bp.route("/api/local/upload", methods=["POST"])
def upload_local_file():
    if not _require_login():
        return jsonify({"error": "Not authenticated"}), 401
    if "file" not in request.files:
        return jsonify({"error": "No file provided"}), 400

    file = request.files["file"]
    if file.filename == "" or not file.filename.endswith((".yml", ".yaml")):
        return jsonify({"error": "Invalid file format. Please upload a .yml or .yaml file"}), 400

    try:
        local_dir = os.path.join("/app/data", "local")
        os.makedirs(local_dir, exist_ok=True)
        file_path = os.path.join(local_dir, file.filename)
        file.save(file_path)

        existing_file = DockerComposeFile.query.filter_by(
            filename=file.filename,
            system_type="local",
            source="local",
        ).first()
        if existing_file:
            existing_file.file_path = file_path
        else:
            db.session.add(
                DockerComposeFile(
                    filename=file.filename,
                    system_type="local",
                    source="local",
                    file_path=file_path,
                )
            )
        db.session.commit()
        return jsonify({"success": True, "message": "File uploaded successfully", "file_path": file_path})
    except Exception as exc:
        return jsonify({"error": f"Error uploading file: {exc}"}), 500
