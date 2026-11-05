import os
import json
import re
import requests
from datetime import datetime, timezone
from pathlib import Path
import time

# -------------------------
# CONFIG
# -------------------------
API_KEY = os.environ.get("YOUTUBE_API_KEY")
CONFIG_FILE, STATE_FILE = "config.json", "state.json"
BASE_URL = "https://www.googleapis.com/youtube/v3"
MAX_RECOMMENDED_CHANNELS = 30

session = requests.Session()


def parse_iso_duration(duration_str):
    """แปลง ISO 8601 Duration (เช่น PT10M15S -> 10:15, PT1H2M30S -> 1:02:30)"""
    if not duration_str or duration_str == "P0D":
        return ""
    pattern = r'PT(?:(?P<hours>\d+)H)?(?:(?P<minutes>\d+)M)?(?:(?P<seconds>\d+)S)?'
    match = re.match(pattern, duration_str)
    if not match:
        return ""
    parts = match.groupdict(0)
    hours = int(parts['hours'])
    minutes = int(parts['minutes'])
    seconds = int(parts['seconds'])
    
    if hours > 0:
        return f"{hours}:{minutes:02d}:{seconds:02d}"
    return f"{minutes}:{seconds:02d}"


def generate_channel_summary(channels, groups, state):
    """สร้างตารางสรุปสถานะช่องและการ Route Webhook"""
    total = len(channels)
    summary_lines = []
    summary_lines.append(f"### 📊 YouTube Monitor Status Summary ({total}/{MAX_RECOMMENDED_CHANNELS} Channels)\n")
    
    if total > MAX_RECOMMENDED_CHANNELS:
        summary_lines.append(f"> ⚠️ **Warning:** Exceeded recommended limit of {MAX_RECOMMENDED_CHANNELS} channels!\n")

    summary_lines.append("| No. | Channel Name | Channel ID | Group | Route / Webhook Status | Memory State |")
    summary_lines.append("|---|---|---|---|---|---|")

    for idx, channel in enumerate(channels, 1):
        c_id = channel.get("id", "Unknown")
        c_name = channel.get("name", "Unknown")
        c_group = channel.get("group", "-")
        
        # ตรวจสอบการ Route Webhook
        group_info = groups.get(c_group, {})
        webhook_env = group_info.get("webhook_env", "")
        has_webhook = bool(os.environ.get(webhook_env)) if webhook_env else False
        
        route_status = f"✅ `{webhook_env}`" if has_webhook else f"❌ Missing `{webhook_env}`"
        
        # ตรวจสอบสถานะ State
        ch_state = state.get("channels", {}).get(c_id)
        if ch_state:
            seen_count = len(ch_state.get("seen", []))
            state_status = f"Tracking ({seen_count} videos)"
        else:
            state_status = "🆕 Pending First Run"

        summary_lines.append(f"| {idx} | **{c_name}** | `{c_id}` | Group {c_group} | {route_status} | {state_status} |")

    summary_text = "\n".join(summary_lines)

    # 1. แสดงผลลง Console Log
    print("\n" + "="*60)
    print(f" CHANNEL SUMMARY ({total}/{MAX_RECOMMENDED_CHANNELS})")
    print("="*60)
    for channel in channels:
        c_group = channel.get("group", "-")
        w_env = groups.get(c_group, {}).get("webhook_env", "")
        w_ok = "OK" if os.environ.get(w_env) else "MISSING"
        print(f" - [{channel.get('name')}] Group: {c_group} | Env: {w_env} ({w_ok})")
    print("="*60 + "\n")

    # 2. ส่งออกไปยัง GitHub Job Summary (ถ้าอยู่บน GitHub Actions)
    github_summary_path = os.environ.get("GITHUB_STEP_SUMMARY")
    if github_summary_path:
        try:
            with open(github_summary_path, "a", encoding="utf-8") as f:
                f.write(summary_text + "\n")
        except Exception as e:
            print(f"Failed to write to GITHUB_STEP_SUMMARY: {e}")


def should_send_error_alert(state, error_msg, cooldown_hours=6):
    """ตรวจสอบว่าควรส่งแจ้งเตือน Error หรือไม่ (ป้องกันการส่งซ้ำทุก 5 นาที)"""
    last_error = state.get("last_error")
    last_error_time_str = state.get("last_error_time")

    if last_error != error_msg:
        return True

    if last_error_time_str:
        try:
            last_error_time = datetime.fromisoformat(last_error_time_str)
            elapsed_hours = (datetime.now(timezone.utc) - last_error_time).total_seconds() / 3600
            if elapsed_hours < cooldown_hours:
                return False
        except Exception:
            return True

    return True


def handle_error(state, error_msg, webhook):
    """จัดการส่งแจ้งเตือน Error เข้า Discord พร้อมบันทึก Cooldown ลง state"""
    if not webhook:
        print(f"Cannot send error alert: Webhook missing. Error: {error_msg}")
        return

    if should_send_error_alert(state, error_msg):
        payload = {
            "content": f"🚨 **[System Alert] YouTube Monitor Error**\n```{error_msg}```",
            "allowed_mentions": {"parse": []}
        }
        try:
            requests.post(webhook, json=payload, timeout=10)
            print("Sent error alert to Discord.")
        except Exception as e:
            print(f"Failed to send error alert to Discord: {e}")

        state["last_error"] = error_msg
        state["last_error_time"] = datetime.now(timezone.utc).isoformat()
        save_state(state)
    else:
        print(f"Skipped error alert (Cooldown active): {error_msg}")


def api_get(endpoint, params):
    params["key"] = API_KEY
    response = session.get(f"{BASE_URL}/{endpoint}", params=params, timeout=30)
    
    if response.status_code == 403:
        error_detail = response.json().get("error", {}).get("message", "Quota exceeded or API error")
        raise RuntimeError(f"YouTube API Quota/Permission Error (403): {error_detail}")
        
    response.raise_for_status()
    return response.json()


def load_json(path, default):
    p = Path(path)
    return json.loads(p.read_text("utf-8")) if p.exists() else default


def save_state(state):
    Path(STATE_FILE).write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")


# -------------------------
# YOUTUBE (Official API)
# -------------------------
def get_channel_videos_api(channel_id):
    cid = channel_id.strip()
    playlist_id = "UU" + cid[2:] if cid.startswith("UC") else cid

    data = api_get("playlistItems", {
        "part": "snippet",
        "playlistId": playlist_id,
        "maxResults": 3
    })
    
    return [item["snippet"]["resourceId"]["videoId"] for item in data.get("items", [])]


def get_video_details(video_ids):
    result = {}
    for start in range(0, len(video_ids), 50):
        batch = video_ids[start:start + 50]
        if batch:
            data = api_get("videos", {
                "part": "snippet,contentDetails,liveStreamingDetails",
                "id": ",".join(batch)
            })
            for video in data.get("items", []):
                result[video["id"]] = video
    return result


# -------------------------
# DISCORD
# -------------------------
def send_discord(webhook, video_id, event_type, group, channel_name, duration="", event_time_iso=None):
    video_url = f"https://www.youtube.com/watch?v={video_id}"

    time_tag = ""
    if event_time_iso:
        dt = datetime.fromisoformat(event_time_iso.replace("Z", "+00:00"))
        unix_ts = int(dt.timestamp())
        time_tag = f" (<t:{unix_ts}:R>)"

    # หัวข้อตามแต่ละ Group
    if group == "A":
        if event_type == "live":
            header = "🔴 NO WAY?? Unstable SMP MEMBER IS LIVE!!"
        else:
            header = "🎬 FEEDING TIME🍗🍗 Unstable SMP NEW VIDEO!!"
    elif group == "B":
        if event_type == "live":
            header = "🔴 LIVE NOW!"
        else:
            header = "🚨 NEW VIDEO ALERT 🚨"
    else:
        header = "🔴 NEW LIVE STREAM!!" if event_type == "live" else "🎬 NEW VIDEO!!"

    # รายละเอียดช่องและความยาวคลิป
    info_line = f"from **{channel_name}**"
    if duration and event_type == "video":
        info_line += f" | video duration [{duration}]"

    # จัดโครงสร้างข้อความใหม่ตามรูปแบบที่ต้องการ
    message = f"{header}{time_tag}\n{info_line}\n{video_url}"

    payload = {
        "content": message,
        "allowed_mentions": {"parse": []}
    }

    requests.post(webhook, json=payload, timeout=15).raise_for_status()
    time.sleep(1)
    print(f"Sent {event_type} notification for '{channel_name}' to Group {group}: {video_id}")

# -------------------------
# MAIN MONITOR
# -------------------------
def main():
    config = load_json(CONFIG_FILE, {})
    state = load_json(STATE_FILE, {"last_run": None, "channels": {}})

    now = datetime.now(timezone.utc)
    groups = config.get("groups", {})
    channels = config.get("channels", [])

    # Webhook สำหรับส่งแจ้งเตือน Error
    default_webhook = None
    if groups:
        first_group = list(groups.values())[0]
        default_webhook = os.environ.get(first_group.get("webhook_env", ""))

    # สรุปสถานะช่องและ Route
    generate_channel_summary(channels, groups, state)

    if not API_KEY:
        error_msg = "YOUTUBE_API_KEY is missing from environment variables."
        print(f"Error: {error_msg}")
        handle_error(state, error_msg, default_webhook)
        return

    all_video_ids, channel_videos, failed_channels = [], {}, set()
    state_changed = False

    # 1. Collect latest videos
    try:
        for channel in channels:
            try:
                ids = get_channel_videos_api(channel["id"])
                channel_videos[channel["id"]] = ids
                all_video_ids.extend(ids)
                print(f"Checked: {channel.get('name', channel['id'])} ({len(ids)} videos)")
            except Exception as error:
                failed_channels.add(channel["id"])
                print(f"Channel error: {channel.get('name', channel['id'])}: {error}")
                if "Quota" in str(error):
                    raise error
    except Exception as e:
        handle_error(state, str(e), default_webhook)
        return

    # 2. Get video and live details
    unique_ids = list(dict.fromkeys(all_video_ids))
    try:
        details = get_video_details(unique_ids) if unique_ids else {}
    except Exception as e:
        handle_error(state, str(e), default_webhook)
        return

    # 3. Process each channel
    for channel in channels:
        channel_id = channel["id"]
        channel_name = channel.get("name", "Unknown Channel")
        if channel_id in failed_channels:
            continue

        ids = channel_videos.get(channel_id, [])
        channel_state = state.get("channels", {}).get(channel_id)

        # First run for a channel
        if channel_state is None:
            live_ids = [
                vid for vid in ids
                if details.get(vid, {}).get("snippet", {}).get("liveBroadcastContent") == "live"
            ]
            state.setdefault("channels", {})[channel_id] = {"seen": ids, "live_notified": live_ids}
            state_changed = True
            print(f"Initialized: {channel_name}")
            continue

        seen = list(channel_state.get("seen", []))
        live_notified = list(channel_state.get("live_notified", []))
        
        webhook_env_key = groups.get(channel["group"], {}).get("webhook_env", "")
        webhook = os.environ.get(webhook_env_key)

        if not webhook:
            print(f"Skipping {channel_name}: Missing environment variable '{webhook_env_key}'")
            continue

        for video_id in ids:
            video = details.get(video_id)
            if video is None:
                continue

            snippet = video["snippet"]
            broadcast = snippet.get("liveBroadcastContent", "none")
            live_details = video.get("liveStreamingDetails")

            raw_duration = video.get("contentDetails", {}).get("duration", "")
            duration = parse_iso_duration(raw_duration)

            # ดึงเวลาเริ่มไลฟ์ หรือเวลาปล่อยคลิป
            if broadcast == "live":
                event_time = (live_details.get("actualStartTime") if live_details else None) or snippet.get("publishedAt")
                if video_id not in live_notified:
                    send_discord(webhook, video_id, "live", channel["group"], channel_name, duration, event_time)
                    live_notified.append(video_id)
                    state_changed = True

            elif video_id not in seen and broadcast == "none" and live_details is None:
                event_time = snippet.get("publishedAt")
                send_discord(webhook, video_id, "video", channel["group"], channel_name, duration, event_time)

            if video_id not in seen:
                seen.append(video_id)
                state_changed = True

        channel_state["seen"] = seen[-10:]
        channel_state["live_notified"] = live_notified[-10:]

    # 4. Clear Error on Success
    if "last_error" in state:
        del state["last_error"]
        if "last_error_time" in state:
            del state["last_error_time"]
        state_changed = True
        print("Previous error cleared as run succeeded.")

    # 5. Save state
    if state_changed:
        state["last_run"] = now.isoformat()
        save_state(state)
        print("State updated and saved.")
    else:
        print("No new updates. Skipping state save.")

    if failed_channels:
        print("Some channels failed. Retrying next run.")

    print("Monitor completed successfully.")


if __name__ == "__main__":
    main()