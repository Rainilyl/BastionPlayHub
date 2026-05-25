#!/bin/bash
# GitLab 仓库同步脚本
# 每5分钟通过 cron 执行，将远端 GitLab 仓库同步到 /data/playbooks
# 用法: gitlab_sync.sh <git_repo_url>

REPO_DIR="/data/playbooks"
LOG_FILE="/var/log/bastion_gitlab_sync.log"
LOCK_FILE="/tmp/bastion_gitlab_sync.lock"

# 从配置文件读取仓库地址，或使用参数传入
SYNC_CONFIG="/usr/local/bin/BastionPlayHub/config/gitlab.yml"

# 获取仓库 URL
get_repo_url() {
    if [ -n "$1" ]; then
        echo "$1"
        return
    fi
    if [ -f "$SYNC_CONFIG" ]; then
        # 从 yaml 配置读取 repo_url
        grep 'repo_url:' "$SYNC_CONFIG" | awk '{print $2}' | tr -d '"' | tr -d "'"
        return
    fi
    echo ""
}

REPO_URL=$(get_repo_url "$1")

if [ -z "$REPO_URL" ]; then
    echo "[$(date)] 错误: 未配置 GitLab 仓库地址" >> "$LOG_FILE"
    echo "用法: $0 <git_repo_url>"
    echo "或在 $SYNC_CONFIG 中配置 repo_url"
    exit 1
fi

# 防止并发执行
if [ -f "$LOCK_FILE" ]; then
    LOCK_PID=$(cat "$LOCK_FILE")
    if kill -0 "$LOCK_PID" 2>/dev/null; then
        echo "[$(date)] 同步正在进行中 (PID: $LOCK_PID)，跳过" >> "$LOG_FILE"
        exit 0
    else
        rm -f "$LOCK_FILE"
    fi
fi

echo $$ > "$LOCK_FILE"
trap "rm -f $LOCK_FILE" EXIT

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" >> "$LOG_FILE"
}

# 如果目录不存在，首次克隆
if [ ! -d "$REPO_DIR" ]; then
    log "首次克隆仓库: $REPO_URL"
    mkdir -p "$(dirname $REPO_DIR)"
    git clone "$REPO_URL" "$REPO_DIR" >> "$LOG_FILE" 2>&1
    if [ $? -eq 0 ]; then
        log "克隆成功"
    else
        log "克隆失败"
        exit 1
    fi
else
    # 目录存在，执行 pull 更新
    cd "$REPO_DIR" || exit 1

    # 重置本地修改，确保 pull 不会冲突
    git fetch --all >> "$LOG_FILE" 2>&1
    git reset --hard origin/$(git symbolic-ref --short HEAD) >> "$LOG_FILE" 2>&1

    if [ $? -eq 0 ]; then
        log "同步成功"
    else
        log "同步失败，尝试重新克隆"
        rm -rf "$REPO_DIR"
        git clone "$REPO_URL" "$REPO_DIR" >> "$LOG_FILE" 2>&1
        if [ $? -eq 0 ]; then
            log "重新克隆成功"
        else
            log "重新克隆失败"
            exit 1
        fi
    fi
fi
