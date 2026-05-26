#!/bin/bash

REPO_DIR="/data/playbooks"
LOG_FILE="/var/log/bastion_gitlab_sync.log"
LOCK_FILE="/tmp/bastion_gitlab_sync.lock"

SYNC_CONFIG="/usr/local/bin/BastionPlayHub/config/gitlab.yml"

get_repo_url() {
    if [ -n "$1" ]; then
        echo "$1"
        return
    fi
    if [ -f "$SYNC_CONFIG" ]; then
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
    cd "$REPO_DIR" || exit 1

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
