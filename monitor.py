import os
import json
import requests
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path

# -------------------------
# CONFIG
# -------------------------
API_KEY = os.environ["YOUTUBE_API_KEY"]
CONFIG_FILE, STATE_FILE = "config.json", "state.json"
BASE_URL = "https://www.googleapis.com/youtube/v3"

session = requests.Session()


def api_get(endpoint, params):
    params["key"] = API_KEY
    response = session.get(f"{BASE_URL}/{endpoint}", params=params, timeout=30)
    response.raise_for_status()
    return response.json()


def load_json(path, default):
    p = Path(path)
    return json.loads(p.read_text("utf-8")) if p.exists() else default


def save_state(state):
    Path(STATE_FILE).write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")


# -------------------------
# YOUTUBE (RSS + API)
# -------------------------
def get_channel_videos_rss(channel_id):
    """ดึง 5 คลิปล่าสุดผ่าน RSS Feed (0 Quota)"""
    url = f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"
    response = session.get(url, timeout=15)
    response.raise_for_status()

    root = ET.fromstring(response.content)
    ns = {
        'atom': 'http://www.w3.org/2005/Atom',
        'yt': 'http://www.youtube.com/xml/schemas/2015'
    }

    video_ids = []
    for entry in root.findall('atom:entry', ns):
        video_id_elem = entry.find('yt:videoId', ns)
        if video_id_elem is not None and video_id_elem.text:
            video_ids.append(video_id_elem.text)
            
    return video_ids[:5]


def get_video_details(video_ids):
    """เช็กสถานะ Live / Video ผ่าน API Batching"""
    result = {}
    for start in range(0, len(video_ids), 50):
        batch = video_ids[start:start + 50]
        if batch:
            data = api_get("videos", {"part": "snippet,liveStreamingDetails", "id": ",".join(batch)})
            for video in data.get("items", []):
                result[video["id"]] = video
    return result


# -------------------------
# DISCORD
# -------------------------
def send_discord(webhook, video_id, event_type, group):
    video_url = f"https://www.youtube.com/watch?v={video_id}"

    if group == "A":
        if event_type == "live":
            message = f"NO WAY?? Unstable SMP MEMBER IS LIVE!!\n\n{video_url}"
        else:
            message = f"FEDDING TIME🍗🍗 Unstable SMP NEW VIDEO!!\n\n{video_url}"
    elif group == "B":
        if event_type == "live":
            message = f"🔴 LIVE NOW!\n\n{video_url}"
        else:
            message = f"🚨 NEW VIDEO ALERT 🚨\n\n{video_url}"

    payload = {
        "content": message,
        "allowed_mentions": {"parse": []}
    }

    requests.post(webhook, json=payload, timeout=15).raise_for_status()
    print(f"Sent {event_type} notification to Group {group}: {video_id}")


# -------------------------
# MAIN MONITOR
# -------------------------
def main():
    config = load_json(CONFIG_FILE, {})
    state = load_json(STATE_FILE, {"channels": {}})

    groups, channels = config["groups"], config["channels"]
    all_video_ids, channel_videos, failed_channels = [], {}, set()
    state_changed = False  # ตัวแปรเช็กว่ามีการอัปเดตข้อมูลใหม่หรือไม่

    # 1. Collect latest videos via RSS Feed
    for channel in channels:
        try:
            ids = get_channel_videos_rss(channel["id"])
            channel_videos[channel["id"]] = ids
            all_video_ids.extend(ids)
            print(f"Checked (RSS): {channel['name']} ({len(ids)} videos)")
        except Exception as error:
            failed_channels.add(channel["id"])
            print(f"Channel error: {channel['name']}: {error}")

    # 2. Get video and live details
    unique_ids = list(dict.fromkeys(all_video_ids))
    details = get_video_details(unique_ids) if unique_ids else {}

    # 3. Process each channel
    for channel in channels:
        channel_id = channel["id"]
        if channel_id in failed_channels:
            continue

        ids = channel_videos.get(channel_id, [])
        channel_state = state["channels"].get(channel_id)

        # รันครั้งแรกของช่อง ให้บันทึกข้อมูลตั้งต้น
        if channel_state is None:
            live_ids = [
                vid for vid in ids
                if details.get(vid, {}).get("snippet", {}).get("liveBroadcastContent") == "live"
            ]
            state["channels"][channel_id] = {"seen": ids, "live_notified": live_ids}
            state_changed = True
            print(f"Initialized: {channel['name']}")
            continue

        # ดึงลิสต์เดิม (รักษาลำดับเดิมเพื่อ Append ต่อท้ายอย่างเดียว)
        seen = channel_state.get("seen", [])
        live_notified = channel_state.get("live_notified", [])
        webhook = os.environ[groups[channel["group"]]["webhook_env"]]

        for video_id in ids:
            video = details.get(video_id)
            if video is None:
                continue

            snippet = video["snippet"]
            broadcast = snippet.get("liveBroadcastContent", "none")
            live_details = video.get("liveStreamingDetails")

            # เช็กและแจ้งเตือน LIVE
            if broadcast == "live":
                if video_id not in live_notified:
                    send_discord(webhook, video_id, "live", channel["group"])
                    live_notified.append(video_id)
                    state_changed = True

            # เช็กและแจ้งเตือนคลิปใหม่
            elif video_id not in seen and broadcast == "none" and live_details is None:
                send_discord(webhook, video_id, "video", channel["group"])

            # เพิ่ม ID ใหม่ต่อท้าย list
            if video_id not in seen:
                seen.append(video_id)
                state_changed = True

        channel_state["seen"] = seen[-100:]
        channel_state["live_notified"] = live_notified[-100:]

    # 4. บันทึกไฟล์ state.json เฉพาะเมื่อมีข้อมูลใหม่เกิดขึ้นจริง
    if state_changed:
        save_state(state)
        print("State updated and saved.")
    else:
        print("No new videos or state changes. Skipping state save.")

    if failed_channels:
        print("Some channels failed. Retrying next run.")

    print("Monitor completed.")


if __name__ == "__main__":
    main()