#!/bin/bash
# Heartopia Tracker 定时任务包装脚本
# 从安全文件读取 GITHUB_TOKEN，拉取最新数据后执行抓取并推送。

REPO_DIR="/home/ubuntu/project/heartopia-tracker"
TOKEN_FILE="$REPO_DIR/.github-token"
LOG_FILE="$REPO_DIR/cron.log"

if [ ! -f "$TOKEN_FILE" ]; then
    echo "[$(date)] 错误: 未找到 token 文件 $TOKEN_FILE" >> "$LOG_FILE"
    exit 1
fi

export GITHUB_TOKEN="$(cat "$TOKEN_FILE")"
cd "$REPO_DIR" || exit 1

# 先拉取最新数据，避免推送冲突
git pull origin HEAD --rebase >> "$LOG_FILE" 2>&1

python3 "$REPO_DIR/scraper.py" >> "$LOG_FILE" 2>&1
