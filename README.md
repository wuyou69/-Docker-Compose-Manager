# Docker Compose Manager

Docker Compose Manager 是一个面向 NAS 和 Linux 服务器的 Docker Compose 可视化管理工具。
它可以集中管理常用服务的 `docker-compose.yml` 模板，支持在线查看、编辑、保存、下载和部署 Compose 文件，也可以查看容器、镜像、部署记录和运行日志。

本仓库版本已经改为 GitHub 文件源，并内置了一份常用 NAS Compose 模板库，适合 fnOS、QNAP、Synology、TrueNAS、Ugreen、ZSpace、ZimaOS 等环境使用。

## 功能特点

- 在线查看和下载 Compose 模板
- 上传、编辑、保存本地 Compose 文件
- 一键部署 Compose 文件到当前 Docker 环境
- 查看部署进度、部署历史和执行日志
- 查看容器列表、镜像列表和容器日志
- 支持 GitHub 公开仓库和私有仓库 Token
- 支持 Docker Hub 镜像一键安装

## 一键安装

SSH 登录 NAS 后执行：

```bash
wget -O install.sh https://raw.githubusercontent.com/wuyou69/Docker-Compose-Manager/main/install.sh && chmod +x install.sh && sudo ./install.sh
```

默认访问地址：

```text
http://服务器IP:5000
```

默认登录信息：

```text
账号：admin
密码：已在应用启动日志中生成
```

查看生成的管理员密码：

```bash
docker logs docker-compose-file | grep "Generated admin password"
```

登录后请及时在后台修改密码。

## 手动 Compose 安装

新建一个 `docker-compose.yml`：

```yaml
version: '3.8'

services:
  docker-compose-file:
    image: wuyou69/docker-compose-manager:latest
    container_name: docker-compose-file
    restart: unless-stopped
    ports:
      - "5000:5000"
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock
      - ./data:/app/data
      - ./docker_compose_file.db:/app/docker_compose_file.db
    environment:
      - SECRET_KEY=请改成一串随机字符
      - FLASK_APP=run.py
      - FLASK_ENV=production
      - DATABASE_URL=sqlite:///./docker_compose_file.db
      - ADMIN_USERNAME=admin
      - GITHUB_API_URL=https://api.github.com
      - GITHUB_REPO=wuyou69/Docker-Compose-Manager
      - GITHUB_CONTENT_ROOT=compose-files
      - GITHUB_BRANCH=main
      - DOCKER_COMPOSE_VERSION=auto
      - APP_VERSION=1.0.0
      - LANGUAGE=zh_CN
```

启动：

```bash
docker compose up -d
docker logs docker-compose-file | grep "Generated admin password"
```

## Docker Run

```bash
docker run -d \
  --name docker-compose-file \
  -p 5000:5000 \
  -v /var/run/docker.sock:/var/run/docker.sock \
  -v ./data:/app/data \
  -v ./docker_compose_file.db:/app/docker_compose_file.db \
  -e ADMIN_USERNAME=admin \
  --restart unless-stopped \
  wuyou69/docker-compose-manager:latest

docker logs docker-compose-file | grep "Generated admin password"
```

## GitHub 文件源

默认配置：

```env
GITHUB_API_URL=https://api.github.com
GITHUB_REPO=wuyou69/Docker-Compose-Manager
GITHUB_CONTENT_ROOT=compose-files
GITHUB_BRANCH=main
```

如果仓库改成私有，请在 `.env` 里加入只读 Token：

```env
GITHUB_TOKEN=你的GitHubToken
```

Token 只需要给当前仓库 `Contents: Read-only` 权限。

## 目录说明

- `app/`：Flask Web 应用
- `compose-files/`：内置 Docker Compose 模板库
- `Dockerfile`：镜像构建文件
- `docker-compose.yml`：部署文件
- `install.sh`：一键安装脚本

## 注意事项

- 容器需要挂载 `/var/run/docker.sock` 才能管理宿主机 Docker。
- 不要把真实 `.env`、数据库文件、GitHub Token 或个人密码提交到仓库。
- 部署 Compose 文件前，请先检查端口、路径和挂载是否适合你的 NAS 环境。
