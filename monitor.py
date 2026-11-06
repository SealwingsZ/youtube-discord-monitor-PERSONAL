import os
import json
import re
import requests
from requests.exceptions import HTTPError
from datetime import datetime, timezone, timedelta
from pathlib import Path
import time

# -------------------------
# CONFIG & CONSTANTS
# -------------------------
API_KEY = os.environ.get("YOUTUBE_API_KEY")
CONFIG_FILE, STATE_FILE = "config.json", "state.json"
BASE_URL = "https://www.googleapis.com/youtube/v3"
MAX_RECOMMENDED_CHANNELS = 30
ICT = timezone(timedelta(hours=7))

DISCORD_HEADERS = {
    ("A", "live"): "🔴 NO WAY?? Unstable SMP MEMBER IS LIVE!!",
    ("A", "video"): "🎬 FEEDING TIME🍗🍗 Unstable SMP NEW VIDEO!!",
    ("B", "live"): "🔴 LIVE NOW!",
    ("B", "video"): "🚨 NEW VIDEO ALERT 🚨",
}

session = requests.Session()


def parse_iso_duration(duration_str):
    """แปลง ISO 8601 Duration (เช่น PT10M15S -> 10:15, PT1H2M30S -> 1:02:30)"""
    if not duration_str or duration_str == "P0D":
        return ""
    m = re.match(r'PT(?:(?P<hours>\d+)H)?(?:(?P<minutes>\d+)M)?(?:(?P<seconds>\d+)S)?', duration_str)
    if not m:
        return ""
    h, m_val, s = [int(v or 0) for v in m.groups()]
    return f"{h}:{m_val:02d}:{s:02d}" if h > 0 else f"{m_val}:{s:02d}"


def post_discord(webhook, payload, timeout=10):
    """Helper สำหรับยิง HTTP POST หา Discord Webhook"""
    if not webhook:
        return False
    try:
        requests.post(webhook, json=payload, timeout=timeout)
        return True
    except Exception as e:
        print(f"Failed to send Discord alert: {e}")
        return False


def generate_channel_summary(channels, groups, state):
    """สร้างตารางสรุปสถานะช่องและการ Route Webhook"""
    total = len(channels)
    lines = [
        f"### YouTube Monitor Status Summary ({total}/{MAX_RECOMMENDED_CHANNELS} Channels)\n",
        *( [f"> ⚠️ **Warning:** Exceeded recommended limit of {MAX_RECOMMENDED_CHANNELS} channels!\n"] if total > MAX_RECOMMENDED_CHANNELS else [] ),
        "| No. | Channel Name | Channel ID | Group | Route / Webhook Status | Memory State |",
        "|---|---|---|---|---|---|"
    ]

    print("\n" + "="*60 + f"\n CHANNEL SUMMARY ({total}/{MAX_RECOMMENDED_CHANNELS})\n" + "="*60)
    for idx, channel in enumerate(channels, 1):
        c_id, c_name, c_group = channel.get("id", "Unknown"), channel.get("name", "Unknown"), channel.get("group", "-")
        w_env = groups.get(c_group, {}).get("webhook_env", "")
        has_webhook = bool(os.environ.get(w_env)) if w_env else False

        route_status = f"no error. `{w_env}`" if has_webhook else f"MISSING `{w_env}`"
        ch_state = state.get("channels", {}).get(c_id)
        state_status = f"Tracking ({len(ch_state.get('seen', []))} videos)" if ch_state else "..Pending First Run"

        lines.append(f"| {idx} | **{c_name}** | `{c_id}` | Group {c_group} | {route_status} | {state_status} |")
        print(f" - [{c_name}] Group: {c_group} | Env: {w_env} ({'OK' if has_webhook else 'MISSING'})")
    print("="*60 + "\n")

    if summary_path := os.environ.get("GITHUB_STEP_SUMMARY"):
        try:
            Path(summary_path).open("a", encoding="utf-8").write("\n".join(lines) + "\n")
        except Exception as e:
            print(f"Failed to write to GITHUB_STEP_SUMMARY: {e}")


def should_send_error_alert(state, error_msg, cooldown_hours=6):
    """ตรวจสอบว่าควรส่งแจ้งเตือน Error หรือไม่ (ป้องกันการส่งซ้ำทุก 5 นาที)"""
    if state.get("last_error") != error_msg:
        return True
    if last_time_str := state.get("last_error_time"):
        try:
            last_time = datetime.fromisoformat(last_time_str)
            return ((datetime.now(timezone.utc) - last_time).total_seconds() / 3600) >= cooldown_hours
        except Exception:
            return True
    return True


def handle_error(state, error_msg, webhook):
    """จัดการส่งแจ้งเตือน Error เข้า Discord พร้อมบันทึก Cooldown ลง state"""
    if not webhook:
        print(f"Cannot send error alert: Webhook missing. Error: {error_msg}")
        return

    if should_send_error_alert(state, error_msg):
        now_ts = int(datetime.now(timezone.utc).timestamp())
        payload = {
            "content": f"> **[🚨 System Alert 🚨] YouTube Discord Monitor Error!** (<t:{now_ts}:F> - <t:{now_ts}:R>)\n\n💥 **Detected Issue:**\n```{error_msg}```",
            "allowed_mentions": {"parse": []}
        }
        if post_discord(webhook, payload):
            print("Sent error alert to Discord.")
        state["last_error"] = error_msg
        state["last_error_time"] = datetime.now(timezone.utc).isoformat()
        save_state(state)
    else:
        print(f"Skipped error alert (Cooldown active): {error_msg}")


def send_recovery_alert(webhook, last_error):
    """ส่งแจ้งเตือนเมื่อระบบกลับมาทำงานเป็นปกติหลังเกิด Error"""
    now_ts = int(datetime.now(timezone.utc).timestamp())
    payload = {
        "content": f"> **[✅ System Status ✅] YouTube Discord Monitor is back to normal!** (<t:{now_ts}:F> - <t:{now_ts}:R>)\n\n🛠️ **Resolved Issue:**\n```{last_error}```",
        "allowed_mentions": {"parse": []}
    }
    if post_discord(webhook, payload):
        print("Sent recovery alert to Discord.")


def send_outage_alert(webhook, pub_dt, now_dt, count):
    """ส่งแจ้งเตือน Outage ในรูปแบบช่วงเวลา (เวลาลงคลิป ➔ เวลาแจ้งเตือนสำเร็จ)"""
    if not webhook:
        return

    pub_ict_str = pub_dt.astimezone(ICT).strftime("%H:%M:%S ICT")
    now_ict_str = now_dt.astimezone(ICT).strftime("%H:%M:%S ICT")
    delay_mins = round((now_dt - pub_dt).total_seconds() / 60)
    now_ts = int(now_dt.timestamp())

    payload = {
        "embeds": [{
            "title": "⚠️ GitHub Actions Outage / Delay Detected",
            "color": 15105570,
            "fields": [
                {
                    "name": "⏱️ Delay Period (Posted ➔ Recovered)",
                    "value": f"`{pub_ict_str}` ➔ `{now_ict_str}` (~{delay_mins} mins)\n<t:{now_ts}:F>",
                    "inline": False
                },
                {
                    "name": "📌 Recovery Status",
                    "value": f"GitHub Actions recovered successfully. Sent **{count}** delayed catch-up notification(s).",
                    "inline": False
                }
            ],
            "footer": {"text": "YouTube Notification Monitor • Auto-Recovery"}
        }]
    }
    if post_discord(webhook, payload):
        print("Sent outage recovery alert to Discord.")


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
# YOUTUBE API
# -------------------------
def get_channel_videos_api(channel_id):
    cid = channel_id.strip()
    playlist_id = "UU" + cid[2:] if cid.startswith("UC") else cid
    try:
        data = api_get("playlistItems", {"part": "snippet", "playlistId": playlist_id, "maxResults": 10})
        return [item["snippet"]["resourceId"]["videoId"] for item in data.get("items", [])]
    except HTTPError as e:
        if e.response is not None and e.response.status_code == 404:
            print(f"Notice: Channel {channel_id} has no upload playlist (404). Returning empty.")
            return []
        raise e


def get_video_details(video_ids):
    result = {}
    for start in range(0, len(video_ids), 50):
        if batch := video_ids[start:start + 50]:
            data = api_get("videos", {"part": "snippet,contentDetails,liveStreamingDetails", "id": ",".join(batch)})
            for video in data.get("items", []):
                result[video["id"]] = video
    return result


# -------------------------
# DISCORD
# -------------------------
def send_discord(webhook, video_id, event_type, group, channel_name, duration="", event_time_iso=None):
    time_tag = ""
    if event_time_iso:
        dt = datetime.fromisoformat(event_time_iso.replace("Z", "+00:00"))
        time_tag = f" (<t:{int(dt.timestamp())}:R>)"

    header = DISCORD_HEADERS.get((group, event_type)) or ("🔴 NEW LIVE STREAM!!" if event_type == "live" else "🎬 NEW VIDEO!!")
    info_line = f"from **{channel_name}**" + (f" | video duration `[{duration}]`" if duration and event_type == "video" else "")
    message = f"{header}{time_tag}\n\n{info_line}\n\n\nhttps://www.youtube.com/watch?v={video_id}"

    requests.post(webhook, json={"content": message, "allowed_mentions": {"parse": []}}, timeout=15).raise_for_status()
    time.sleep(1)
    print(f"Sent {event_type} notification for '{channel_name}' to Group {group}: {video_id}")


# -------------------------
# MAIN MONITOR
# -------------------------
def main():
    config = load_json(CONFIG_FILE, {})
    state = load_json(STATE_FILE, {"channels": {}})

    now = datetime.now(timezone.utc)
    notifications_sent = 0
    delayed_notifications = 0
    if is_delayed:
    delayed_notifications += 1
    if not first_delayed_pub_dt:
        first_delayed_pub_dt = pub_dt

    groups = config.get("groups", {})
    channels = config.get("channels", [])

    default_webhook = None
    if groups:
        first_group = list(groups.values())[0]
        default_webhook = os.environ.get(first_group.get("webhook_env", ""))

    error_webhook = os.environ.get("DISCORD_WEBHOOK_ERROR") or default_webhook

    try:
        generate_channel_summary(channels, groups, state)

        if not API_KEY:
            raise RuntimeError("YOUTUBE_API_KEY is missing from environment variables.")

        all_video_ids, channel_videos, failed_channels = [], {}, set()
        state_changed = False

        # 1. Collect latest videos
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

        # 2. Get video and live details
        unique_ids = list(dict.fromkeys(all_video_ids))
        details = get_video_details(unique_ids) if unique_ids else {}

        # 3. Process each channel
        for channel in channels:
            channel_id = channel["id"]
            channel_name = channel.get("name", "Unknown Channel")
            if channel_id in failed_channels:
                continue

            ids = channel_videos.get(channel_id, [])
            channel_state = state.get("channels", {}).get(channel_id)

            if channel_state is None:
                live_ids = [
                    vid for vid in ids
                    if details.get(vid, {}).get("snippet", {}).get("liveBroadcastContent") == "live"
                ]
                state.setdefault("channels", {})[channel_id] = {
                    "name": channel_name,  # <--- เพิ่มบันทึกชื่อช่องตอนสร้าง State ใหม่
                    "seen": ids,
                    "live_notified": live_ids
                }
                state_changed = True
                print(f"Initialized state for: {channel_name}")
                continue

            # อัปเดตชื่อช่องใน state หากยังไม่มี หรือมีการเปลี่ยนชื่อใน config.json
            if channel_state.get("name") != channel_name:
                channel_state["name"] = channel_name
                state_changed = True

            seen = list(channel_state.get("seen", []))
            live_notified = list(channel_state.get("live_notified", []))

            webhook_env_key = groups.get(channel["group"], {}).get("webhook_env", "")
            webhook = os.environ.get(webhook_env_key)

            if not webhook:
                print(f"Skipping {channel_name}: Missing environment variable '{webhook_env_key}'")
                continue

            for video_id in ids:
                video = details.get(video_id)
                if not video:
                    continue

                snippet = video["snippet"]
                broadcast = snippet.get("liveBroadcastContent", "none")
                live_details = video.get("liveStreamingDetails")
                duration = parse_iso_duration(video.get("contentDetails", {}).get("duration", ""))
                pub_time_str = snippet.get("publishedAt")

                pub_dt = datetime.fromisoformat(pub_time_str.replace("Z", "+00:00")) if pub_time_str else None
                is_delayed = pub_dt and (now - pub_dt).total_seconds() > 420

                should_notify = False

                # 1. กรณีเป็นไลฟ์สดที่กำลังจัดอยู่
                if broadcast == "live":
                    if video_id not in live_notified:
                        event_time = (live_details.get("actualStartTime") if live_details else None) or pub_time_str
                        send_discord(webhook, video_id, "live", channel["group"], channel_name, duration, event_time)
                        live_notified.append(video_id)
                        state_changed = should_notify = True

                # 2. กรณีเป็นคลิปปกติ (ต้องไม่เคยแจ้งเตือนใน seen/live_notified และต้องไม่ใช่ไลฟ์ที่จบแล้ว)
                elif broadcast == "none":
                    is_past_live = live_details is not None  # ถ้ามี liveStreamingDetails แปลว่าเป็นคลิปย้อนหลังไลฟ์สด

                    if video_id not in seen and video_id not in live_notified:
                        if not is_past_live:
                            # เป็นคลิปอัปโหลดปกติจริงๆ ถึงจะส่งแจ้งเตือน
                            send_discord(webhook, video_id, "video", channel["group"], channel_name, duration, pub_time_str)
                            should_notify = True
                        else:
                            print(f"Skipped past live stream archive for '{channel_name}': {video_id}")

                if should_notify:
                    notifications_sent += 1
                    if is_delayed:
                        delayed_notifications += 1

                if video_id not in seen:
                    seen.append(video_id)
                    state_changed = True
                    
            channel_state["seen"] = seen[-10:]
            channel_state["live_notified"] = live_notified[-10:]

        # 4. Clear Error on Success
        if "last_error" in state:
            send_recovery_alert(error_webhook, state.get("last_error", "Unknown error"))
            del state["last_error"]
            state.pop("last_error_time", None)
            state_changed = True
            print("Previous error cleared as run succeeded.")

        # 5. Outage Recovery Alert
        if delayed_notifications > 0 and first_delayed_pub_dt:
            send_outage_alert(error_webhook, first_delayed_pub_dt, now, delayed_notifications)

        # 6. Save state
        if state_changed:
            save_state(state)
            print("State updated and saved.")
        else:
            print("No updates found. Skipping state save to keep Git clean.")

        if failed_channels:
            print("Some channels failed. Retrying next run.")

        print("Monitor completed successfully.")

    except Exception as e:
        print(f"Unhandled Exception Caught: {e}")
        handle_error(state, str(e), error_webhook)
        raise e


if __name__ == "__main__":
    main()
