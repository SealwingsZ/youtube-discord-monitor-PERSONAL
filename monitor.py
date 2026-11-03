
import os
import json
import requests

from datetime import datetime, timezone, timedelta
from pathlib import Path

# -------------------------
# CONFIG
# -------------------------

API_KEY = os.environ["YOUTUBE_API_KEY"]

CONFIG_FILE = "config.json"
STATE_FILE = "state.json"

BASE_URL = "https://www.googleapis.com/youtube/v3"

session = requests.Session()


def api_get(endpoint, params):
    params["key"] = API_KEY

    response = session.get(
        f"{BASE_URL}/{endpoint}",
        params=params,
        timeout=30
    )
    response.raise_for_status()
    return response.json()


def load_json(path, default):
    if not Path(path).exists():
        return default

    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_state(state):
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)


# -------------------------
# YOUTUBE
# -------------------------

def get_upload_playlist(channel_id):
    data = api_get("channels", {
        "part": "contentDetails",
        "id": channel_id
    })

    items = data.get("items", [])

    if not items:
        raise ValueError(f"Channel not found: {channel_id}")

    return items[0]["contentDetails"]["relatedPlaylists"]["uploads"]


def get_channel_videos(channel):
    playlist_id = get_upload_playlist(channel["id"])

    data = api_get("playlistItems", {
        "part": "snippet",
        "playlistId": playlist_id,
        "maxResults": 10
    })

    videos = []

    for item in data.get("items", []):
        video_id = (
            item["snippet"]["resourceId"]["videoId"]
        )

        videos.append(video_id)

    return videos


def get_video_details(video_ids):
    result = {}

    # YouTube API supports up to 50 IDs per request
    for start in range(0, len(video_ids), 50):
        batch = video_ids[start:start + 50]

        if not batch:
            continue

        data = api_get("videos", {
            "part": "snippet,liveStreamingDetails",
            "id": ",".join(batch)
        })

        for video in data.get("items", []):
            result[video["id"]] = video

    return result


# -------------------------
# DISCORD
# -------------------------

def send_discord(webhook, channel, video, live=False):

    snippet = video["snippet"]

    title = snippet.get("title", "Untitled")
    video_id = video["id"]

    url = f"https://www.youtube.com/watch?v={video_id}"

    if live:
        heading = "🔴 LIVE NOW!"
        color = 0xFF0000
    else:
        heading = "🎬 NEW VIDEO!"
        color = 0x5865F2

    embed = {
        "title": heading,
        "description": (
            f"**{title}**\n\n"
            f"ช่อง: {channel['name']}\n\n"
            f"[▶ รับชมบน YouTube]({url})"
        ),
        "url": url,
        "color": color,
        "footer": {
            "text": channel["name"]
        }
    }

    thumbnails = snippet.get("thumbnails", {})
    thumbnail = (
        thumbnails.get("high")
        or thumbnails.get("medium")
        or thumbnails.get("default")
    )

    if thumbnail:
        embed["thumbnail"] = {
            "url": thumbnail["url"]
        }

    response = session.post(
        webhook,
        params={"wait": "true"},
        json={
            "embeds": [embed],
            "allowed_mentions": {"parse": []}
        },
        timeout=30
    )

    response.raise_for_status()

    print(f"Sent: {title}")


# -------------------------
# MAIN MONITOR
# -------------------------

def main():

    config = load_json(CONFIG_FILE, {})
    state = load_json(STATE_FILE, {
        "last_run": None,
        "channels": {}
    })

    interval = config.get("check_interval_minutes", 5)

    now = datetime.now(timezone.utc)

    last_run = state.get("last_run")

    if last_run:
        previous = datetime.fromisoformat(last_run)

        if now - previous < timedelta(minutes=interval):
            print("Not time to check yet")
            return

    groups = config["groups"]
    channels = config["channels"]

    all_video_ids = []
    channel_videos = {}
    failed_channels = set()

    # 1. Collect latest videos from all channels

    for channel in channels:
        try:
            ids = get_channel_videos(channel)

            channel_videos[channel["id"]] = ids
            all_video_ids.extend(ids)

            print(
                f"Checked: {channel['name']} "
                f"({len(ids)} videos)"
            )

        except Exception as error:
            failed_channels.add(channel["id"])
            print(
                f"Channel error: {channel['name']}: {error}"
            )

    # 2. Get video and live information

    unique_ids = list(dict.fromkeys(all_video_ids))
    details = get_video_details(unique_ids)

    # 3. Process each channel

    for channel in channels:

        channel_id = channel["id"]

        if channel_id in failed_channels:
            continue

        ids = channel_videos.get(channel_id, [])

        channel_state = state["channels"].get(channel_id)

        # First run for a channel:
        # Save existing videos without old notifications.

        if channel_state is None:
            live_ids = [
                vid for vid in ids
                if (
                    vid in details
                    and details[vid]["snippet"].get(
                        "liveBroadcastContent"
                    ) == "live"
                )
            ]

            state["channels"][channel_id] = {
                "seen": ids,
                "live_notified": live_ids
            }

            print(f"Initialized: {channel['name']}")
            continue

        seen = set(channel_state.get("seen", []))
        live_notified = set(
            channel_state.get("live_notified", [])
        )

        group = groups[channel["group"]]
        webhook = os.environ[group["webhook_env"]]

        for video_id in ids:

            video = details.get(video_id)

            if video is None:
                continue

            snippet = video["snippet"]

            broadcast = snippet.get(
                "liveBroadcastContent", "none"
            )

            live_details = video.get(
                "liveStreamingDetails"
            )

            # A. Active livestream

            if broadcast == "live":

                if video_id not in live_notified:

                    send_discord(
                        webhook,
                        channel,
                        video,
                        live=True
                    )

                    live_notified.add(video_id)

            # B. New normal video
            # Upcoming/completed live broadcasts
            # must not be treated as normal videos.

            elif (
                video_id not in seen
                and broadcast == "none"
                and live_details is None
            ):

                send_discord(
                    webhook,
                    channel,
                    video,
                    live=False
                )

            seen.add(video_id)

        # Keep recent history

        channel_state["seen"] = list(seen)[-100:]
        channel_state["live_notified"] = list(
            live_notified
        )[-100:]

    # 4. Save state only when every channel was checked.
    # This prevents missed notifications after API errors.

    
    # Save successful channel history even if
    # another channel failed.

    if not failed_channels:
        state["last_run"] = now.isoformat()

    save_state(state)

    if failed_channels:
        print("Some channels failed. Retrying next run.")

    print("Monitor completed.")



if __name__ == "__main__":
    main()
