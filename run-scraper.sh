#!/bin/bash
# Heartopia Tracker 定时任务包装脚本
# 从安全文件读取 GITHUB_TOKEN，拉取最新数据后执行抓取并推送。

REPO_DIR="/home/ubuntu/project/heartopia-tracker"
TOKEN_FILE="$REPO_DIR/.github-token"
LOG_FILE="$REPO_DIR/cron.log"
PROXY_URL="http://127.0.0.1:7890"
DISCORD_API="https://discord.com/api/v9/invites/heartopia?with_counts=true"

if [ ! -f "$TOKEN_FILE" ]; then
    echo "[$(date)] 错误: 未找到 token 文件 $TOKEN_FILE" >> "$LOG_FILE"
    exit 1
fi

export GITHUB_TOKEN="$(cat "$TOKEN_FILE")"
cd "$REPO_DIR" || exit 1

# ── git pull（失败不阻止抓取）─────────────────────────────────────────

max_retries=3
pull_ok=false
for ((i=1; i<=max_retries; i++)); do
    if git pull origin HEAD --rebase >> "$LOG_FILE" 2>&1; then
        pull_ok=true
        break
    fi
    if [ "$i" -lt "$max_retries" ]; then
        delay=$((5 * 2 ** (i - 1)))
        echo "[$(date)] git pull 失败，${delay}s 后重试 (第 ${i}/${max_retries} 次)..." >> "$LOG_FILE"
        sleep "$delay"
    fi
done
if [ "$pull_ok" = false ]; then
    echo "[$(date)] git pull 最终失败，跳过同步，继续抓取" >> "$LOG_FILE"
fi

# ── 代理连通性检测 + 自动重启 mihomo ─────────────────────────────────

check_proxy() {
    curl -s --max-time 10 --proxy "$PROXY_URL" "$DISCORD_API" > /dev/null 2>&1
}

if check_proxy; then
    echo "[$(date)] 代理连通性检测通过" >> "$LOG_FILE"
else
    echo "[$(date)] 代理不可达，尝试重启 mihomo..." >> "$LOG_FILE"
    sudo systemctl restart mihomo >> "$LOG_FILE" 2>&1
    sleep 5
    if check_proxy; then
        echo "[$(date)] mihomo 重启后代理恢复" >> "$LOG_FILE"
    else
        echo "[$(date)] 代理仍然不可达，继续尝试抓取" >> "$LOG_FILE"
    fi
fi

# ── 抓取 ──────────────────────────────────────────────────────────────

python3 "$REPO_DIR/scraper.py" >> "$LOG_FILE" 2>&1
