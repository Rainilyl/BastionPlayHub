#!/bin/bash

set -e

if [ "$(id -u)" -ne 0 ]; then
    echo "请以 root 权限运行此脚本。"
    exit 1
fi

DEFAULT_USERNAME="bastion_user"
USERNAME=${1:-$DEFAULT_USERNAME}
INSTALL_DIR="/usr/local/bin/BastionPlayHub"
PLAYBOOK_DIR="/data/playbooks"

echo "=========================================="
echo "  BastionPlayHub 堡垒机部署"
echo "=========================================="
echo ""

echo "[1/6] 安装系统依赖..."

install_pkg() {
    if command -v apt-get >/dev/null 2>&1; then
        apt-get install -y "$@"
    elif command -v yum >/dev/null 2>&1; then
        yum install -y "$@"
    else
        echo "不支持的包管理器，请手动安装: $@"
        exit 1
    fi
}

if command -v apt-get >/dev/null 2>&1; then
    apt-get update -qq
fi

if ! command -v python3 >/dev/null 2>&1; then
    install_pkg python3 python3-pip python3-dev
fi

if ! command -v pip3 >/dev/null 2>&1; then
    install_pkg python3-pip
fi

if ! command -v git >/dev/null 2>&1; then
    install_pkg git
fi

if ! command -v ansible-playbook >/dev/null 2>&1; then
    install_pkg ansible || pip3 install ansible
fi

install_pkg sshpass 2>/dev/null || true
install_pkg lrzsz 2>/dev/null || true

echo "[2/6] 安装 Python 依赖..."
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

pip3 install -i https://pypi.tuna.tsinghua.edu.cn/simple \
    --trusted-host pypi.tuna.tsinghua.edu.cn \
    -r "$PROJECT_DIR/requirements.txt" -q

echo "[3/6] 部署程序文件..."
mkdir -p "$INSTALL_DIR"
cp -rf "$PROJECT_DIR"/* "$INSTALL_DIR/"

chmod +x "$INSTALL_DIR/restricted_shell.py"
ln -sf "$INSTALL_DIR/restricted_shell.py" /usr/local/bin/restricted_shell.py

if ! grep -q "/usr/local/bin/restricted_shell.py" /etc/shells; then
    echo "/usr/local/bin/restricted_shell.py" >> /etc/shells
fi

echo "[4/6] 初始化 Playbook 目录..."
mkdir -p "$PLAYBOOK_DIR"
chmod +x "$INSTALL_DIR/scripts/gitlab_sync.sh"

mkdir -p "$PLAYBOOK_DIR/test"
cat > "$PLAYBOOK_DIR/test/ping.yml" << 'PLAYBOOKEOF'
---
- hosts: targets
  gather_facts: no
  tasks:
    - name: 测试连通性
      ping:

    - name: 获取主机名
      command: hostname
      register: result

    - name: 显示主机名
      debug:
        msg: "{{ result.stdout }}"
PLAYBOOKEOF
echo "  已创建测试 playbook: test/ping.yml"

echo "[5/6] 配置堡垒机用户: $USERNAME"
if id "$USERNAME" >/dev/null 2>&1; then
    echo "  用户 $USERNAME 已存在，更新 shell..."
    usermod -s /usr/local/bin/restricted_shell.py "$USERNAME"
else
    useradd -m -s /usr/local/bin/restricted_shell.py "$USERNAME"
    echo "  用户 $USERNAME 已创建"
fi

USER_HOME=$(eval echo "~$USERNAME")
SSH_DIR="$USER_HOME/.ssh"
mkdir -p "$SSH_DIR"

if [ ! -f "$SSH_DIR/id_rsa" ]; then
    ssh-keygen -t rsa -b 4096 -f "$SSH_DIR/id_rsa" -N "" -q
    echo "  已生成堡垒机用户密钥对"
else
    echo "  密钥对已存在，跳过生成"
fi

touch "$SSH_DIR/authorized_keys"
chmod 700 "$SSH_DIR"
chmod 600 "$SSH_DIR/id_rsa"
chmod 644 "$SSH_DIR/id_rsa.pub"
chmod 600 "$SSH_DIR/authorized_keys"
chown -R "$USERNAME:$USERNAME" "$SSH_DIR"

echo "[6/6] 配置日志..."
touch /var/log/bastion_gitlab_sync.log
chmod 644 /var/log/bastion_gitlab_sync.log

echo ""
echo "=========================================="
echo "  部署完成!"
echo "=========================================="
echo ""
echo "═══════════════════════════════════════════════════════════════"
echo ""
echo " 【必选】完成以下配置后堡垒机才能正常使用"
echo ""
echo "  1. 编辑服务器列表"
echo "     vi $INSTALL_DIR/config/servers.yml"
echo ""
echo "  2. 配置服务器免密连接"
echo "     公钥路径: $SSH_DIR/id_rsa.pub"
echo "     分发脚本: bash $INSTALL_DIR/scripts/push_key.sh <IP> [用户名]"
echo "              bash $INSTALL_DIR/scripts/push_key.sh --all [用户名]"
echo "     默认分发到 root，可指定其他用户。也可自行配置免密。"
echo ""
echo "  3. 配置用户登录堡垒机"
echo "     推荐密钥: echo '公钥内容' >> $SSH_DIR/authorized_keys"
echo "     或密码:   passwd $USERNAME"
echo ""
echo " 【可选】按需配置"
echo ""
echo "  · 远程仓库同步 Playbook"
echo "    vi $INSTALL_DIR/config/gitlab.yml  填写 repo_url"
echo "    bash $INSTALL_DIR/scripts/gitlab_sync.sh  首次同步"
echo "    crontab -e 添加: */<分钟> * * * * $INSTALL_DIR/scripts/gitlab_sync.sh"
echo ""
echo "  · 修改 Playbook 存储路径 (默认 $PLAYBOOK_DIR)"
echo "    编辑 $INSTALL_DIR/restricted_shell.py 中的 PLAYBOOK_DIR"
echo ""
echo "  · 密钥分发到文件列表"
echo "    bash $INSTALL_DIR/scripts/push_key.sh --file <IP列表> [用户名]"
echo ""
echo " 【测试】"
echo ""
echo "  ssh $USERNAME@<堡垒机IP>"
echo "  进入后执行: vi host → 填入 127.0.0.1 → as host test/ping.yml"
echo ""
echo "═══════════════════════════════════════════════════════════════"
