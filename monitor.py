import os
import json
import requests
from datetime import datetime, timezone, timedelta
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
# YOUTUBE
# -------------------------
def get_upload_playlist(channel_id):
    items = api_get("channels", {"part": "contentDetails", "id": channel_id}).get("items", [])
    if not items:
        raise ValueError(f"Channel not found: {channel_id}")
    return items[0]["contentDetails"]["relatedPlaylists"]["uploads"]


def get_channel_videos(channel):
    playlist_id = get_upload_playlist(channel["id"])
    data = api_get("playlistItems", {"part": "snippet", "playlistId": playlist_id, "maxResults": 10})
    return [item["snippet"]["resourceId"]["videoId"] for item in data.get("items", [])]


def get_video_details(video_ids):
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
def send_discord(webhook, video_id, event_type):
    heading = (
        "NO WAY?? Unstable SMP MEMBER IS LIVE!!"
        if event_type == "live"
        else "FEDDING TIME🍗🍗 Unstable SMP NEW VIDEO!!"
    )

    video_url = f"https://www.youtube.com/watch?v={video_id}"

    message = f"{heading}\n\n{video_url}"

    payload = {
        "content": message,
        "allowed_mentions": {"parse": []}
    }

    requests.post(webhook, json=payload, timeout=15).raise_for_status()

    print(f"Sent notification: {video_id}")


# -------------------------
# MAIN MONITOR
# -------------------------
def main():
    config = load_json(CONFIG_FILE, {})
    state = load_json(STATE_FILE, {"last_run": None, "channels": {}})

    interval = config.get("check_interval_minutes", 5)
    now = datetime.now(timezone.utc)

    if state.get("last_run") and now - datetime.fromisoformat(state["last_run"]) < timedelta(minutes=interval):
        print("Not time to check yet")
        return

    groups, channels = config["groups"], config["channels"]
    all_video_ids, channel_videos, failed_channels = [], {}, set()

    # 1. Collect latest videos from all channels
    for channel in channels:
        try:
            ids = get_channel_videos(channel)
            channel_videos[channel["id"]] = ids
            all_video_ids.extend(ids)
            print(f"Checked: {channel['name']} ({len(ids)} videos)")
        except Exception as error:
            failed_channels.add(channel["id"])
            print(f"Channel error: {channel['name']}: {error}")

    # 2. Get video and live information
    details = get_video_details(list(dict.fromkeys(all_video_ids)))

    # 3. Process each channel
    for channel in channels:
        channel_id = channel["id"]
        if channel_id in failed_channels:
            continue

        ids = channel_videos.get(channel_id, [])
        channel_state = state["channels"].get(channel_id)

        # First run for a channel
        if channel_state is None:
            live_ids = [
                vid for vid in ids
                if details.get(vid, {}).get("snippet", {}).get("liveBroadcastContent") == "live"
            ]
            state["channels"][channel_id] = {"seen": ids, "live_notified": live_ids}
            print(f"Initialized: {channel['name']}")
            continue

        seen = set(channel_state.get("seen", []))
        live_notified = set(channel_state.get("live_notified", []))
        webhook = os.environ[groups[channel["group"]]["webhook_env"]]

        for video_id in ids:
            video = details.get(video_id)
            if video is None:
                continue

            snippet = video["snippet"]
            broadcast = snippet.get("liveBroadcastContent", "none")
            live_details = video.get("liveStreamingDetails")

            if broadcast == "live":
                if video_id not in live_notified:
                    send_discord(webhook, snippet["title"], channel["name"], video_id, "live")
                    live_notified.add(video_id)
            elif video_id not in seen and broadcast == "none" and live_details is None:
                send_discord(webhook, snippet["title"], channel["name"], video_id, "video")

            seen.add(video_id)

        channel_state["seen"] = list(seen)[-100:]
        channel_state["live_notified"] = list(live_notified)[-100:]

    # 4. Save state
    if not failed_channels:
        state["last_run"] = now.isoformat()

    save_state(state)

    if failed_channels:
        print("Some channels failed. Retrying next run.")

    print("Monitor completed.")


if __name__ == "__main__":
    main()