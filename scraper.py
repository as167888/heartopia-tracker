#!/usr/bin/env python3
"""Heartopia Discord 数据抓取 — 每小时第7分钟抓取成员数和在线人数并推送到 GitHub。"""

import json
import os
import subprocess
import sys
import time
import urllib.request
from datetime import datetime, timezone, timedelta

DISCORD_API = "https://discord.com/api/v9/invites/heartopia?with_counts=true"
DATA_PATH = "data/heartopia_data.json"
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
)
TZ = timezone(timedelta(hours=8))


def beijing_timestamp():
    return datetime.now(TZ).strftime("%Y-%m-%d %H:%M:%S")


def fetch_discord():
    req = urllib.request.Request(DISCORD_API, headers={"User-Agent": USER_AGENT})
    proxy = os.environ.get("HTTP_PROXY") or os.environ.get("http_proxy")

    max_retries = 3
    for attempt in range(max_retries):
        try:
            if proxy:
                proxy_handler = urllib.request.ProxyHandler({"https": proxy})
                opener = urllib.request.build_opener(proxy_handler)
                resp = opener.open(req, timeout=30)
            else:
                resp = urllib.request.urlopen(req, timeout=30)
            data = json.loads(resp.read())
            return {
                "member_count": data["approximate_member_count"],
                "presence_count": data["approximate_presence_count"],
            }
        except (urllib.error.URLError, OSError) as e:
            if attempt < max_retries - 1:
                delay = 5 * (2 ** attempt)
                print(f"  请求失败 ({e})，{delay}s 后重试 (第 {attempt + 1}/{max_retries} 次)...")
                time.sleep(delay)
            else:
                raise


def read_data():
    with open(DATA_PATH, "r") as f:
        return json.load(f)


def write_data(entries):
    with open(DATA_PATH, "w") as f:
        json.dump(entries, f, indent=2, ensure_ascii=False)
        f.write("\n")


def git_push(token: str):
    remote_url = f"https://oauth2:{token}@github.com/as167888/heartopia-tracker.git"

    max_retries = 3
    for attempt in range(max_retries):
        try:
            subprocess.run(["git", "add", DATA_PATH], check=True)
            subprocess.run(["git", "-c", f"user.name=heartopia-bot",
                                 "-c", f"user.email=bot@heartopia.local",
                                 "commit", "-m", "Update data [skip ci]"], check=True)
            subprocess.run(["git", "push", remote_url, "HEAD"], check=True)
            return
        except subprocess.CalledProcessError as e:
            if attempt < max_retries - 1:
                delay = 5 * (2 ** attempt)
                print(f"  git push 失败 ({e})，{delay}s 后重试 (第 {attempt + 1}/{max_retries} 次)...")
                # 重置本地改动，下次重试重新 add/commit/push
                subprocess.run(["git", "reset", "--soft", "HEAD~1"], capture_output=True)
                subprocess.run(["git", "restore", "--staged", DATA_PATH], capture_output=True)
                time.sleep(delay)
            else:
                raise


def main():
    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        print("错误: 未设置 GITHUB_TOKEN 环境变量", file=sys.stderr)
        sys.exit(1)

    print(f"[{beijing_timestamp()}] 正在抓取 Discord 数据...")
    info = fetch_discord()
    print(f"  注册成员={info['member_count']}  在线人数={info['presence_count']}")

    entries = read_data()
    entries.append({
        "timestamp": beijing_timestamp(),
        "member_count": info["member_count"],
        "presence_count": info["presence_count"],
    })
    write_data(entries)
    print(f"  已追加到 {DATA_PATH}（共 {len(entries)} 条记录）")

    print("  正在推送到 GitHub...")
    git_push(token)
    print("  完成。")


if __name__ == "__main__":
    main()
