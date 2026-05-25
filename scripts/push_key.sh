#!/bin/bash
# BastionPlayHub 密钥分发脚本
# 将堡垒机用户的公钥推送到服务器，实现免密连接
#
# 用法:
#   bash push_key.sh <目标IP> [用户名]            分发到单台服务器 (默认 root)
#   bash push_key.sh --all [用户名]               分发到 servers.yml 中所有服务器
#   bash push_key.sh --file <IP列表文件> [用户名] 分发到文件中的所有服务器
#
# 首次分发需要输入目标服务器密码

BASTION_USER="${BASTION_USER:-bastion_user}"
USER_HOME=$(eval echo "~$BASTION_USER")
PUB_KEY_FILE="$USER_HOME/.ssh/id_rsa.pub"
CONFIG_FILE="/usr/local/bin/BastionPlayHub/config/servers.yml"

if [ ! -f "$PUB_KEY_FILE" ]; then
    echo "[错误] 堡垒机用户公钥不存在: $PUB_KEY_FILE"
    echo "请先运行部署脚本生成密钥对。"
    exit 1
fi

# 默认目标用户为 root
TARGET_USER="root"

push_key_to_host() {
    local host=$1
    echo -n "  分发到 ${TARGET_USER}@${host} ... "
    ssh-copy-id -i "$PUB_KEY_FILE" -o StrictHostKeyChecking=no "${TARGET_USER}@${host}" 2>/dev/null
    if [ $? -eq 0 ]; then
        echo "✓ 成功"
    else
        echo "✗ 失败"
    fi
}

get_all_ips() {
    grep 'ip:' "$CONFIG_FILE" | awk '{print $2}' | tr -d '"' | tr -d "'"
}

show_help() {
    echo "BastionPlayHub 密钥分发工具"
    echo ""
    echo "用法:"
    echo "  $0 <目标IP> [用户名]            分发到单台服务器 (默认 root)"
    echo "  $0 --all [用户名]               分发到 servers.yml 中所有服务器"
    echo "  $0 --file <IP列表> [用户名]     分发到文件中的所有服务器"
    echo ""
    echo "堡垒机用户: $BASTION_USER"
    echo "公钥路径:   $PUB_KEY_FILE"
}

case "${1:-}" in
    --all)
        if [ -n "$2" ]; then
            TARGET_USER="$2"
        fi
        if [ ! -f "$CONFIG_FILE" ]; then
            echo "[错误] 服务器配置文件不存在: $CONFIG_FILE"
            exit 1
        fi
        echo "分发公钥到所有服务器 (用户: $TARGET_USER)..."
        echo ""
        for ip in $(get_all_ips); do
            push_key_to_host "$ip"
        done
        echo ""
        echo "完成。"
        ;;
    --file)
        if [ -z "$2" ] || [ ! -f "$2" ]; then
            echo "用法: $0 --file <IP列表文件> [用户名]"
            exit 1
        fi
        if [ -n "$3" ]; then
            TARGET_USER="$3"
        fi
        echo "分发公钥到文件中的服务器 (用户: $TARGET_USER)..."
        echo ""
        while IFS= read -r ip; do
            ip=$(echo "$ip" | tr -d '[:space:]')
            if [ -n "$ip" ] && [ "${ip:0:1}" != "#" ]; then
                push_key_to_host "$ip"
            fi
        done < "$2"
        echo ""
        echo "完成。"
        ;;
    ""|--help|-h)
        show_help
        ;;
    *)
        # 当作 IP 处理，第二个参数为用户名
        if [ -n "$2" ]; then
            TARGET_USER="$2"
        fi
        echo "分发公钥到 ${TARGET_USER}@${1} ..."
        push_key_to_host "$1"
        echo ""
        echo "完成。"
        ;;
esac
