#!/bin/bash

# 检查是否有sudo权限
if ! sudo -v &>/dev/null; then
    echo "错误: 需要sudo权限来运行此脚本。"
    exit 1
fi

# 获取用户输入配置（添加 -e 选项启用行编辑）
echo "==== OpenList WebDAV 挂载配置 ===="
read -e -p "请输入OpenList访问地址 (例如: http://192.168.1.100:24005): " OPENLIST_URL
read -e -p "请输入OpenList用户名: " OPENLIST_USERNAME
read -s -e -p "请输入OpenList密码: " OPENLIST_PASSWORD
echo
read -e -p "请输入本地挂载点路径 [默认: $HOME/openlist_mount]: " CUSTOM_MOUNT_POINT
MOUNT_POINT="${CUSTOM_MOUNT_POINT:-$HOME/openlist_mount}"

# 检查并安装rclone
install_rclone() {
    echo "检测到rclone未安装，正在安装最新版本..."
    curl https://rclone.org/install.sh | sudo bash
    if [ $? -ne 0 ]; then
        echo "错误: rclone安装失败，请手动安装。"
        exit 1
    fi
    echo "rclone安装成功！"
}

# 检查rclone是否安装
if ! command -v rclone &> /dev/null; then
    install_rclone
fi

# 检查并配置fuse.conf
configure_fuse() {
    if ! grep -q "user_allow_other" /etc/fuse.conf; then
        echo "配置FUSE允许其他用户访问..."
        echo "user_allow_other" | sudo tee -a /etc/fuse.conf > /dev/null
    fi
}
configure_fuse

# 检查挂载点是否存在，不存在则创建
if [ ! -d "$MOUNT_POINT" ]; then
    mkdir -p "$MOUNT_POINT"
    echo "已创建挂载点: $MOUNT_POINT"
fi

# 配置rclone远程
echo "配置rclone远程..."
rclone config create openlist_webdav webdav \
    url "$OPENLIST_URL/dav" \
    vendor other \
    user "$OPENLIST_USERNAME" \
    pass "$OPENLIST_PASSWORD"

# 挂载OpenList，添加15秒刷新间隔和权限设置
echo "正在挂载OpenList到 $MOUNT_POINT..."
rclone mount \
    --allow-other \
    --allow-non-empty \
    --vfs-cache-mode writes \
    --vfs-cache-max-age 15s \
    --umask 000 \
    openlist_webdav: "$MOUNT_POINT" &

# 等待挂载完成并验证
sleep 2
if ! mount | grep -q "$MOUNT_POINT"; then
    echo "错误: 挂载失败！"
    exit 1
fi

echo "挂载成功！OpenList已挂载到 $MOUNT_POINT"
echo "进程ID: $!"
echo "使用 'fusermount -u $MOUNT_POINT' 命令卸载"
