#!/bin/bash

# 获取 Docker Compose 最新版本号
echo "正在获取 Docker Compose 最新版本号..."
LATEST_VERSION=$(curl -s https://api.github.com/repos/docker/compose/releases/latest | grep 'tag_name' | cut -d\" -f4 | sed 's/v//')

# 检查版本号获取是否成功
if [ -z "$LATEST_VERSION" ]; then
    echo "获取 Docker Compose 最新版本号失败，请检查网络连接。"
    exit 1
fi

# 提示用户选择加速链接
echo "请选择加速链接:"
echo "1. 不加速（建议墙外用户使用）"
echo "2. 使用脚本自带加速链接: https://gitproxy.click/"
echo "3. 使用脚本自带加速链接: https://github.moeyy.xyz/"
echo "4. 使用脚本自带加速链接: https://github.tbedu.top/"
echo "5. 使用脚本自带加速链接: https://github.proxy.class3.fun/"
echo "6. 使用脚本自带加速链接: https://ghfile.geekertao.top/"
echo "7. 使用脚本自带加速链接: https://github.proxy.class3.fun/"
echo "8. 使用脚本自带加速链接: https://github-proxy.lixxing.top/"
echo "9. 使用脚本自带加速链接: https://ghf.无名氏.top/"
echo "10. 使用脚本自带加速链接: https://ghm.078465.xyz/"
echo "11. 使用脚本自带加速链接: https://gh-proxy.net/"
echo "12. 手动输入加速链接（自行寻找加速链接）"

read -p "请输入你的选择 (1-12): " choice

case $choice in
    1)
        BASE_URL=""
        ;;
    2)
        BASE_URL="https://gitproxy.click/"
        ;;
    3)
        BASE_URL="https://github.moeyy.xyz/"
        ;;
    4)
        BASE_URL="https://github.tbedu.top/"
        ;;
    5|7)
        BASE_URL="https://github.proxy.class3.fun/"
        ;;
    6)
        BASE_URL="https://ghfile.geekertao.top/"
        ;;
    8)
        BASE_URL="https://github-proxy.lixxing.top/"
        ;;
    9)
        BASE_URL="https://ghf.无名氏.top/"
        ;;
    10)
        BASE_URL="https://ghm.078465.xyz/"
        ;;
    11)
        BASE_URL="https://gh-proxy.net/"
        ;;
    12)
        read -p "请输入加速链接: " CUSTOM_URL
        BASE_URL="${CUSTOM_URL}"
        ;;
    *)
        echo "无效的选择，请输入 1-12 之间的数字。"
        exit 1
        ;;
esac

# 拼接完整下载链接
DOWNLOAD_URL="${BASE_URL}https://github.com/docker/compose/releases/download/v${LATEST_VERSION}/docker-compose-$(uname -s)-$(uname -m)"

# 下载最新版本的 Docker Compose
echo "正在下载 Docker Compose 版本 $LATEST_VERSION..."
sudo curl -SL "$DOWNLOAD_URL" -o /usr/local/bin/docker-compose

# 检查下载是否成功
if [ $? -ne 0 ]; then
    echo "Docker Compose 下载失败，请检查网络连接或加速链接是否有效。"
    exit 1
fi

# 添加执行权限
echo "正在为 Docker Compose 添加执行权限..."
sudo chmod +x /usr/local/bin/docker-compose

# 验证安装
echo "正在验证 Docker Compose 安装..."
docker-compose --version

if [ $? -eq 0 ]; then
    echo "Docker Compose 安装成功！"
else
    echo "Docker Compose 安装验证失败，请检查安装过程。"
fi
