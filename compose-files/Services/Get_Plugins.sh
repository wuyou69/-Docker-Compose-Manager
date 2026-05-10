#!/bin/bash

read -e -s -p "请输入你的 APT 认证令牌: " APT_TOKEN

read -e -p "请输入要下载到的本地路径: " LOCAL_DIR

if [ -d "$LOCAL_DIR" ]; then
    echo "本地文件夹 $LOCAL_DIR 已存在。"
else
    echo "本地文件夹 $LOCAL_DIR 不存在，正在创建..."
    mkdir -p "$LOCAL_DIR"
    if [ $? -eq 0 ]; then
        echo "本地文件夹 $LOCAL_DIR 创建成功。"
    else
        echo "创建本地文件夹 $LOCAL_DIR 失败，请检查权限。"
        exit 1
    fi
fi

ACCELERATOR_OPTIONS=(
    "不加速（建议墙外用户使用）"
    "使用脚本自带加速链接: https://gitproxy.click/"
    "使用脚本自带加速链接: https://github.moeyy.xyz/"
    "使用脚本自带加速链接: https://github.tbedu.top/"
    "使用脚本自带加速链接: https://github.proxy.class3.fun/"
    "使用脚本自带加速链接: https://ghfile.geekertao.top/"
    "使用脚本自带加速链接: https://github.proxy.class3.fun/"
    "使用脚本自带加速链接: https://github-proxy.lixxing.top/"
    "使用脚本自带加速链接: https://ghf.无名氏.top/"
    "使用脚本自带加速链接: https://ghm.078465.xyz/"
    "使用脚本自带加速链接: https://gh-proxy.net/"
    "手动输入加速链接（自行寻找加速链接）"
)

ACCELERATOR_LINKS=(
    ""
    "https://gitproxy.click/"
    "https://github.moeyy.xyz/"
    "https://github.tbedu.top/"
    "https://github.proxy.class3.fun/"
    "https://ghfile.geekertao.top/"
    "https://github.proxy.class3.fun/"
    "https://github-proxy.lixxing.top/"
    "https://ghf.无名氏.top/"
    "https://ghm.078465.xyz/"
    "https://gh-proxy.net/"
)

echo "请选择加速选项:"
for i in "${!ACCELERATOR_OPTIONS[@]}"; do
    echo "$((i + 1)). ${ACCELERATOR_OPTIONS[$i]}"
done
read -p "输入选项编号: " choice

if [ "$choice" -eq 12 ]; then
    read -p "请输入自定义加速链接: " CUSTOM_ACCELERATOR
    ACCELERATOR="$CUSTOM_ACCELERATOR"
elif [ "$choice" -ge 1 ] && [ "$choice" -le 11 ]; then
    index=$((choice - 1))
    ACCELERATOR="${ACCELERATOR_LINKS[$index]}"
else
    echo "无效的选项，使用不加速模式。"
    ACCELERATOR=""
fi

REPO_OWNER="ATaKi-Myt"
REPO_NAME="Last_Three_Service_Package_Pro"
TARGET_DIR="Plugins"
API_URL="https://api.github.com/repos/${REPO_OWNER}/${REPO_NAME}/contents/${TARGET_DIR}"

FILE_LIST=$(curl -s -H "Authorization: token $APT_TOKEN" "$API_URL" | grep '"download_url":' | sed 's/.*"download_url": "\([^"]*\)".*/\1/')

if [ -z "$FILE_LIST" ]; then
    echo "未能获取到文件列表，请检查 APT 令牌和仓库权限。"
    exit 1
fi

OLD_IFS=$IFS
IFS=$'\n'

for file_url in $FILE_LIST; do
    clean_url=$(echo "$file_url" | sed 's/\?token=.*//')
    file_name=$(basename "$clean_url")
    if [ -n "$ACCELERATOR" ]; then
        download_url="${ACCELERATOR}${clean_url}"
    else
        download_url="$file_url"
    fi
    echo "正在下载 $file_name..."
    curl -s -H "Authorization: token $APT_TOKEN" -o "$LOCAL_DIR/$file_name" "$download_url"
    if [ $? -eq 0 ]; then
        echo "$file_name 下载成功"
    else
        echo "下载 $file_name 失败"
    fi
done

IFS=$OLD_IFS

echo "所有文件下载完成"
