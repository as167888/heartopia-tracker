import json
import os
import sys
from datetime import datetime
from zoneinfo import ZoneInfo

import requests

import config


def fetch_invite_data():
    proxies = None
    if config.PROXY:
        proxies = {"http": config.PROXY, "https": config.PROXY}

    headers = {"User-Agent": config.USER_AGENT}

    resp = requests.get(
        config.API_URL,
        proxies=proxies,
        headers=headers,
        timeout=config.REQUEST_TIMEOUT,
    )
    resp.raise_for_status()
    data = resp.json()

    return {
        "member_count": data["approximate_member_count"],
        "presence_count": data["approximate_presence_count"],
        "guild_name": data.get("guild", {}).get("name", ""),
        "guild_id": data.get("guild", {}).get("id", ""),
    }


def save_to_json(info):
    os.makedirs(config.DATA_DIR, exist_ok=True)

    beijing_tz = ZoneInfo("Asia/Shanghai")
    now = datetime.now(beijing_tz)
    json_path = os.path.join(config.DATA_DIR, "heartopia_data.json")

    existing = []
    if os.path.isfile(json_path):
        with open(json_path, "r", encoding="utf-8") as f:
            try:
                existing = json.load(f)
            except json.JSONDecodeError:
                existing = []

    existing.append({
        "timestamp": now.strftime("%Y-%m-%d %H:%M:%S"),
        "member_count": info["member_count"],
        "presence_count": info["presence_count"],
    })

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(existing, f, ensure_ascii=False, indent=2)

    return json_path


def main():
    try:
        info = fetch_invite_data()
    except requests.RequestException as e:
        print(f"[ERROR] API request failed: {e}", file=sys.stderr)
        sys.exit(1)
    except KeyError as e:
        print(f"[ERROR] Unexpected API response, missing key: {e}", file=sys.stderr)
        sys.exit(1)

    path = save_to_json(info)

    print(
        f"[{info['guild_name']}] "
        f"members={info['member_count']:,} "
        f"online={info['presence_count']:,} "
        f"-> {path}"
    )


if __name__ == "__main__":
    main()
