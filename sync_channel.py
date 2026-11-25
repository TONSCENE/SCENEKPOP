#!/usr/bin/env python3
"""
Sync all videos and playlists from https://www.youtube.com/@SCENEKPOP
and generate db.js for SCENEKPOP+ (grouped by K-Pop group, playlist, and content type).
"""
import argparse
import base64
import concurrent.futures
import json
import os
import re
import subprocess
import sys
import urllib.error
import urllib.request
from datetime import datetime

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(SCRIPT_DIR, "group_config.json")
PATREON_PATH = os.path.join(SCRIPT_DIR, "patreon_posts.json")
CUSTOM_VIDEOS_PATH = os.path.join(SCRIPT_DIR, "custom_videos.json")
DESC_CACHE_PATH = os.path.join(SCRIPT_DIR, ".desc_cache.json")
VISION_CACHE_PATH = os.path.join(SCRIPT_DIR, ".vision_cache.json")
OUTPUT_DB_PATH = os.path.join(SCRIPT_DIR, "db.js")


def load_gemini_api_key() -> str:
    """Load GEMINI_API_KEY from environment or parent/local .env file."""
    if os.environ.get("GEMINI_API_KEY"):
        return os.environ["GEMINI_API_KEY"].strip()
    for env_path in [os.path.join(SCRIPT_DIR, ".env"), os.path.join(os.path.dirname(SCRIPT_DIR), ".env")]:
        if os.path.exists(env_path):
            with open(env_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line.startswith("GEMINI_API_KEY="):
                        return line.split("=", 1)[1].strip().strip('"').strip("'")
    return ""


def classify_thumbnail_with_gemini(vid: str, title: str, thumb_url: str, groups_cfg: list, api_key: str) -> list:
    """Use Gemini Vision on the video thumbnail + title to identify K-Pop group(s)."""
    if not api_key:
        return []
    try:
        with urllib.request.urlopen(thumb_url, timeout=15) as resp:
            img_b64 = base64.b64encode(resp.read()).decode("ascii")
    except Exception:
        return []

    valid_ids = [g["id"] for g in groups_cfg]
    group_list_str = "\n".join(f"- {g['id']}: {g['name']} ({g.get('thaiName', '')})" for g in groups_cfg)
    prompt = (
        "You are classifying K-Pop YouTube videos by inspecting the video thumbnail image and title.\n"
        f"Video title: {title}\n\n"
        "Look at any text, logos, or people in the thumbnail image and match them to one or more group IDs from this list:\n"
        f"{group_list_str}\n\n"
        "Respond ONLY with a JSON array of matching group IDs (for example [\"qwer\"] or [\"hearts2hearts\"]). "
        "If it does not clearly belong to any specific group in the list, respond with [\"other_kpop\"]."
    )

    payload = {
        "contents": [{
            "parts": [
                {"text": prompt},
                {"inline_data": {"mime_type": "image/jpeg", "data": img_b64}},
            ]
        }],
        "generationConfig": {"temperature": 0.1, "responseMimeType": "application/json"},
    }
    data = json.dumps(payload).encode("utf-8")

    for model in ("gemini-2.5-flash", "gemini-2.0-flash"):
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
        req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=25) as resp:
                body = json.loads(resp.read().decode("utf-8"))
                txt = body["candidates"][0]["content"]["parts"][0]["text"]
                parsed = json.loads(txt)
                if isinstance(parsed, list):
                    return [gid for gid in parsed if gid in valid_ids]
        except Exception:
            continue
    return []


def run_yt_dlp_json(url: str, playlist_end: int = 0) -> dict:
    """Fetch flat-playlist metadata JSON for a YouTube channel tab or playlist."""
    cmd = [
        "yt-dlp",
        "--no-update",
        "--flat-playlist",
    ]
    if playlist_end > 0:
        cmd.extend(["--playlist-end", str(playlist_end)])
    cmd.extend(["--dump-single-json", url])
    res = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if res.returncode != 0:
        raise RuntimeError(f"yt-dlp failed for {url}: {res.stderr.strip()}")
    return json.loads(res.stdout)


def fetch_video_detail(vid: str) -> dict:
    """Fetch full metadata (description/tags) for a single video when title alone is ambiguous."""
    cmd = [
        "yt-dlp",
        "--no-update",
        "--skip-download",
        "--dump-json",
        f"https://www.youtube.com/watch?v={vid}",
    ]
    res = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if res.returncode != 0:
        return {}
    data = json.loads(res.stdout)
    return {
        "title": data.get("title") or "",
        "duration": data.get("duration"),
        "description": data.get("description") or "",
        "tags": data.get("tags") or [],
    }


def format_duration(seconds) -> str:
    """Format duration in seconds into MM:SS or H:MM:SS."""
    if not seconds:
        return ""
    sec = int(seconds)
    h, rem = divmod(sec, 3600)
    m, s = divmod(rem, 60)
    if h > 0:
        return f"{h}:{m:02d}:{s:02d}"
    return f"{m}:{s:02d}"


def detect_sub_badge(title: str) -> str:
    """Detect subtitle language tag from video title."""
    t = title.lower()
    has_th = any(k in t for k in ["ซับไทย", "แปลไทย", "thai sub", "[th]", "(th)"])
    has_en = any(k in t for k in ["eng sub", "english sub", "[en]", "[eng]", "(en)"])
    if has_th and has_en:
        return "TH / EN SUB"
    if has_th:
        return "ซับไทย"
    if has_en:
        return "ENG SUB"
    # Default for Thai-titled videos on @SCENEKPOP
    if re.search(r"[\u0e00-\u0e7f]", title):
        return "ซับไทย"
    return "SUBBED"


def detect_content_type(title: str, playlist_titles: list) -> str:
    """Classify video into live, radio, stage, or variety."""
    text = f"{title} {' '.join(playlist_titles)}".lower()
    if any(k in text for k in ["weverse live", "weverse", "ig live", "live ig", "hbd live", "syncroom live", "birthday", "christmas day"]):
        if "studio choom" not in text and "cultwo" not in text:
            return "live"
    if any(k in text for k in ["radio", "cultwo", "youngstreet", "young street", "volume up", "kiss the radio", "gayo plaza", "yoon sang", "mbc radio", "heartspod", "bae sung-jae", "you in radio"]):
        return "radio"
    if any(k in text for k in ["awards", "bonsang", "m countdown", "busking", "rocketlaunch", "concert", "fanmeeting", "fan meeting", "showcase", "show case", "studio choom", "kcon", "live vocal", "dingo attack"]):
        return "stage"
    return "variety"


def match_text_to_groups(text: str, playlist_ids: set, groups_cfg: list) -> list:
    """Return matching group IDs for a given text blob and playlist membership."""
    t = text.lower()
    matched = []
    for grp in groups_cfg:
        gid = grp["id"]
        if gid == "other_kpop":
            continue
        # Exclusions (checked before playlist or keyword match)
        if any(ex.lower() in t for ex in grp.get("exclude_if", [])):
            continue
        # Direct playlist assignment
        if any(pid in playlist_ids for pid in grp.get("playlist_ids", [])):
            matched.append(gid)
            continue
        # Substring keywords
        hit = any(kw.lower() in t for kw in grp.get("keywords", []))
        # Regex keywords
        if not hit:
            for pattern in grp.get("regex_keywords", []):
                if re.search(pattern, t, flags=re.IGNORECASE):
                    hit = True
                    break
        if hit:
            matched.append(gid)
    return matched


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    parser = argparse.ArgumentParser(description="Sync @SCENEKPOP YouTube channel to db.js")
    parser.add_argument("--videos-json", help="Optional path to pre-fetched videos JSON")
    parser.add_argument("--playlists-json", help="Optional path to pre-fetched playlists JSON")
    parser.add_argument("--pl-map-json", help="Optional path to pre-fetched playlist->videos map JSON")
    parser.add_argument("--skip-detail-lookup", action="store_true", help="Skip fetching descriptions for unmatched videos")
    parser.add_argument("--no-vision", action="store_true", help="Disable Gemini Vision thumbnail classification for unmatched videos")
    args = parser.parse_args()

    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        cfg = json.load(f)

    channel_url = cfg["channel"]["url"]
    groups_cfg = cfg["groups"]
    overrides = cfg.get("video_overrides", {})

    desc_cache = {}
    if os.path.exists(DESC_CACHE_PATH):
        with open(DESC_CACHE_PATH, "r", encoding="utf-8") as f:
            desc_cache = json.load(f)

    # 1. Fetch videos
    if args.videos_json and os.path.exists(args.videos_json):
        print(f"Loading cached videos from {args.videos_json}...")
        videos_raw = json.load(open(args.videos_json, "r", encoding="utf-8"))
    else:
        print(f"Fetching videos from {channel_url}/videos ...")
        videos_raw = run_yt_dlp_json(f"{channel_url}/videos")

    entries = [e for e in videos_raw.get("entries", []) if e and e.get("id")]
    print(f"Found {len(entries)} videos.")

    # 1.5 Check real-time UU uploads playlist for brand-new videos not yet cached on /videos tab
    channel_id = videos_raw.get("channel_id") or ""
    if not (args.videos_json and os.path.exists(args.videos_json)) and channel_id.startswith("UC"):
        uploads_id = "UU" + channel_id[2:]
        try:
            uploads_raw = run_yt_dlp_json(f"https://www.youtube.com/playlist?list={uploads_id}", playlist_end=25)
            short_ids = set()
            try:
                shorts_raw = run_yt_dlp_json(f"{channel_url}/shorts", playlist_end=25)
                short_ids = {s["id"] for s in shorts_raw.get("entries", []) if s and s.get("id")}
            except Exception:
                pass
            existing_ids = {e["id"] for e in entries}
            fresh_uploads = [
                e for e in uploads_raw.get("entries", [])
                if e and e.get("id") and e["id"] not in existing_ids and e["id"] not in short_ids
            ]
            if fresh_uploads:
                print(f"Found {len(fresh_uploads)} newer upload(s) via {uploads_id}: {[e['id'] for e in fresh_uploads]}")
                entries = fresh_uploads + entries
        except Exception as exc:
            print(f"Warning: could not check {uploads_id} uploads playlist ({exc})")

    # 2. Fetch playlists & their video IDs
    if args.playlists_json and os.path.exists(args.playlists_json):
        playlists_raw = json.load(open(args.playlists_json, "r", encoding="utf-8"))
    else:
        print(f"Fetching playlists from {channel_url}/playlists ...")
        playlists_raw = run_yt_dlp_json(f"{channel_url}/playlists")

    pl_entries = [p for p in playlists_raw.get("entries", []) if p and p.get("id")]
    print(f"Found {len(pl_entries)} playlists.")

    if args.pl_map_json and os.path.exists(args.pl_map_json):
        pl_map = json.load(open(args.pl_map_json, "r", encoding="utf-8"))
    else:
        print("Fetching video lists for each playlist in parallel...")
        pl_map = {}

        def _fetch_pl(pl_item):
            pid = pl_item["id"]
            ptitle = pl_item.get("title") or pid
            pdata = run_yt_dlp_json(f"https://www.youtube.com/playlist?list={pid}")
            pl_entries_list = [
                {
                    "id": v["id"],
                    "title": v.get("title") or "",
                    "duration": v.get("duration"),
                }
                for v in pdata.get("entries", [])
                if v and v.get("id") and v.get("title") not in ("[Private video]", "[Deleted video]")
            ]
            return pid, {
                "title": ptitle,
                "videos": [v["id"] for v in pl_entries_list],
                "entries": pl_entries_list,
            }

        with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:
            for pid, pinfo in pool.map(_fetch_pl, pl_entries):
                pl_map[pid] = pinfo
                print(f"  - {pinfo['title']}: {len(pinfo['videos'])} videos")

    # Merge any playlist-only (e.g. unlisted) videos into entries so all 15 playlists work
    seen_entry_ids = {e["id"] for e in entries}
    for pid, pinfo in pl_map.items():
        for pe in pinfo.get("entries", []):
            if pe["id"] not in seen_entry_ids:
                seen_entry_ids.add(pe["id"])
                entries.append(pe)

    # Merge explicit unlisted/extra YouTube video IDs from group_config.json (without duplicating)
    extra_ids = cfg.get("extra_youtube_ids", [])
    if extra_ids:
        cache_dirty = False
        for extra_vid in reversed(extra_ids):
            if not extra_vid or extra_vid in seen_entry_ids:
                continue
            detail = desc_cache.get(extra_vid)
            if not detail or not detail.get("title"):
                detail = fetch_video_detail(extra_vid)
                if detail:
                    desc_cache[extra_vid] = detail
                    cache_dirty = True
            if detail and detail.get("title"):
                entries.insert(0, {
                    "id": extra_vid,
                    "title": detail["title"],
                    "duration": detail.get("duration"),
                })
                seen_entry_ids.add(extra_vid)
                print(f"Added extra unlisted/explicit video: {extra_vid} ({detail['title'][:50]})")
        if cache_dirty:
            with open(DESC_CACHE_PATH, "w", encoding="utf-8") as f:
                json.dump(desc_cache, f, ensure_ascii=False, indent=2)

    # Build reverse index: video_id -> list of playlist IDs
    vid_to_pl_ids = {}
    for pid, pinfo in pl_map.items():
        for vid in pinfo.get("videos", []):
            vid_to_pl_ids.setdefault(vid, []).append(pid)

    # 3. Classify videos
    videos_out = []
    unmatched_indices = []
    for idx, entry in enumerate(entries):
        vid = entry["id"]
        title = entry.get("title") or ""
        pl_ids = vid_to_pl_ids.get(vid, [])
        pl_titles = [pl_map[pid]["title"] for pid in pl_ids if pid in pl_map]

        if vid in overrides:
            matched_groups = list(overrides[vid])
        else:
            matched_groups = match_text_to_groups(
                f"{title} {' '.join(pl_titles)}",
                set(pl_ids),
                groups_cfg,
            )

        if not matched_groups:
            # Check description cache first
            cached = desc_cache.get(vid)
            if cached:
                blob = f"{title} {cached.get('description', '')} {' '.join(cached.get('tags', []))}"
                matched_groups = match_text_to_groups(blob, set(pl_ids), groups_cfg)

        if not matched_groups:
            unmatched_indices.append(idx)

        videos_out.append({
            "num": idx + 1,
            "ytId": vid,
            "title": title,
            "duration": format_duration(entry.get("duration")),
            "durationSec": int(entry.get("duration") or 0),
            "thumb": f"https://img.youtube.com/vi/{vid}/hqdefault.jpg",
            "groups": matched_groups,
            "playlists": pl_ids,
            "contentType": detect_content_type(title, pl_titles),
            "subBadge": detect_sub_badge(title),
        })

    # Optionally resolve unmatched videos via description lookup
    if unmatched_indices and not args.skip_detail_lookup:
        print(f"Inspecting descriptions for {len(unmatched_indices)} unmatched videos...")
        for idx in unmatched_indices:
            vid = videos_out[idx]["ytId"]
            detail = desc_cache.get(vid) or fetch_video_detail(vid)
            if detail:
                desc_cache[vid] = detail
                blob = f"{videos_out[idx]['title']} {detail.get('description', '')} {' '.join(detail.get('tags', []))}"
                pl_ids = set(videos_out[idx]["playlists"])
                matched = match_text_to_groups(blob, pl_ids, groups_cfg)
                if matched:
                    videos_out[idx]["groups"] = matched

        with open(DESC_CACHE_PATH, "w", encoding="utf-8") as f:
            json.dump(desc_cache, f, ensure_ascii=False, indent=2)

    # Optionally resolve remaining unmatched videos via Gemini Vision thumbnail inspection
    still_unmatched = [i for i, v in enumerate(videos_out) if not v["groups"]]
    if still_unmatched and not args.no_vision:
        vision_cache = {}
        if os.path.exists(VISION_CACHE_PATH):
            with open(VISION_CACHE_PATH, "r", encoding="utf-8") as f:
                vision_cache = json.load(f)
        api_key = load_gemini_api_key()
        if api_key:
            print(f"Checking thumbnails with Gemini Vision for {len(still_unmatched)} unmatched videos...")
            for idx in still_unmatched:
                v = videos_out[idx]
                vid = v["ytId"]
                if vid in vision_cache:
                    matched = vision_cache[vid]
                else:
                    matched = classify_thumbnail_with_gemini(vid, v["title"], v["thumb"], groups_cfg, api_key)
                    if matched:
                        vision_cache[vid] = matched
                if matched:
                    v["groups"] = matched
                    print(f"  [Vision] {vid} -> {matched} ({v['title'][:50]})")
            with open(VISION_CACHE_PATH, "w", encoding="utf-8") as f:
                json.dump(vision_cache, f, ensure_ascii=False, indent=2)

    # Final fallback to "other_kpop"
    for v in videos_out:
        v["source"] = "youtube"
        if not v["groups"]:
            v["groups"] = ["other_kpop"]

    # Track initial group thumbnails from YouTube videos before adding Patreon items
    group_thumbs = {}
    for v in videos_out:
        for gid in v["groups"]:
            if gid not in group_thumbs:
                group_thumbs[gid] = v["thumb"]

    # 3.5 Merge Patreon posts if patreon_posts.json exists
    patreon_count = 0
    if os.path.exists(PATREON_PATH):
        with open(PATREON_PATH, "r", encoding="utf-8") as f:
            patreon_posts = json.load(f)
        for p in patreon_posts:
            title = p.get("title") or ""
            pid_key = f"patreon_{p.get('index', patreon_count + 1)}"
            matched_groups = match_text_to_groups(title, set(), groups_cfg)
            if not matched_groups:
                matched_groups = ["other_kpop"]
            is_public = (p.get("status") == "public")
            thumb = p.get("localThumb") or ""
            if not thumb:
                # Fallback to group's YouTube thumbnail or first Patreon thumbnail
                for gid in matched_groups:
                    if gid in group_thumbs:
                        thumb = group_thumbs[gid]
                        break
            if not thumb:
                thumb = "images/patreon/p_01.jpg"
            for gid in matched_groups:
                if gid not in group_thumbs and thumb:
                    group_thumbs[gid] = thumb

            videos_out.append({
                "num": len(videos_out) + 1,
                "ytId": pid_key,
                "title": title,
                "duration": p.get("date") or "Patreon",
                "durationSec": 0,
                "thumb": thumb,
                "groups": matched_groups,
                "playlists": [],
                "contentType": "patreon",
                "subBadge": "Patreon ดูฟรี" if is_public else "Patreon สมาชิก",
                "source": "patreon",
                "patreonUrl": p.get("url") or "https://www.patreon.com/c/SCENEKPOP/posts",
                "patreonStatus": "public" if is_public else "locked",
                "date": p.get("date") or "",
            })
            patreon_count += 1

    # 3.6 Merge custom hosted videos (Cloudflare R2 / Artplayer / archive.org / OneDrive)
    if os.path.exists(CUSTOM_VIDEOS_PATH):
        with open(CUSTOM_VIDEOS_PATH, "r", encoding="utf-8") as f:
            custom_list = json.load(f)
        for c in custom_list:
            if not c or not c.get("id"):
                continue
            grps = c.get("groups") or match_text_to_groups(c.get("title", ""), set(), groups_cfg) or ["other_kpop"]
            src_type = c.get("source") or ("artplayer" if c.get("videoUrl") else "embed")
            thumb = c.get("thumb") or group_thumbs.get(grps[0], "")
            videos_out.insert(0, {
                "num": 0,
                "ytId": c["id"],
                "title": c.get("title", c["id"]),
                "duration": c.get("duration", ""),
                "durationSec": int(c.get("durationSec") or 0),
                "thumb": thumb,
                "groups": grps,
                "playlists": c.get("playlists", []),
                "contentType": c.get("contentType", "variety"),
                "subBadge": c.get("subBadge", "MULTI SUBS"),
                "source": src_type,
                "videoUrl": c.get("videoUrl", ""),
                "embedUrl": c.get("embedUrl", ""),
                "directUrl": c.get("directUrl", ""),
                "subtitles": c.get("subtitles", []),
            })
        for i, v in enumerate(videos_out, 1):
            v["num"] = i

    # 4. Build group summaries sorted by count (keep other_kpop at the end)
    vid_by_id = {v["ytId"]: v for v in videos_out}
    group_counts = {g["id"]: 0 for g in groups_cfg}
    for v in videos_out:
        for gid in v["groups"]:
            group_counts[gid] = group_counts.get(gid, 0) + 1
            if gid not in group_thumbs:
                group_thumbs[gid] = v["thumb"]

    groups_out = []
    for g in groups_cfg:
        gid = g["id"]
        cnt = group_counts.get(gid, 0)
        if cnt == 0:
            continue
        groups_out.append({
            "id": gid,
            "name": g["name"],
            "thaiName": g.get("thaiName", ""),
            "accent": g.get("accent", "#a855f7"),
            "tagline": g.get("tagline", ""),
            "count": cnt,
            "thumb": g.get("thumb") or group_thumbs.get(gid, ""),
            "playlistIds": g.get("playlist_ids", []),
        })

    groups_out.sort(key=lambda x: (x["id"] == "other_kpop", -x["count"]))

    # 5. Build playlists / series output
    playlists_out = []
    for pl_item in pl_entries:
        pid = pl_item["id"]
        pinfo = pl_map.get(pid, {})
        pl_vids = [vid for vid in pinfo.get("videos", []) if vid in vid_by_id]
        if not pl_vids:
            continue
        # Infer primary group for playlist
        g_tally = {}
        for vid in pl_vids:
            for gid in vid_by_id[vid]["groups"]:
                g_tally[gid] = g_tally.get(gid, 0) + 1
        primary_group = max(g_tally.items(), key=lambda kv: kv[1])[0] if g_tally else "other_kpop"
        playlists_out.append({
            "id": pid,
            "title": pinfo.get("title", pid),
            "count": len(pl_vids),
            "thumb": vid_by_id[pl_vids[0]]["thumb"],
            "groupId": primary_group,
            "groupIds": [primary_group],
            "videoIds": pl_vids,
        })

    # 5.5 Auto-group multi-episode Patreon series into playlists
    patreon_series_defs = [
        ("pt_hyemilee", "HyeMiLeeYeChaePa S01 ซับไทย (Patreon)", "hyemileeyechaepa", ["hyemileeyechaepa", "le_sserafim", "idle"], lambda v: "hyemileeyechaepa" in v["title"].lower()),
        ("pt_smtm12", "Show Me The Money 12 ซับไทย (Patreon)", "smtm12_milli", ["smtm12_milli"], lambda v: "smtm12" in v["title"].lower()),
        ("pt_wonhee", "Hello Twenty Wonhee S01 ซับไทย (Patreon)", "illit", ["illit"], lambda v: "hello twenty wonhee" in v["title"].lower()),
        ("pt_idol_bingo", "Idol Bingo x ILLIT ซับไทย (Patreon)", "illit", ["illit"], lambda v: "idol bingo" in v["title"].lower()),
        ("pt_mzine_h2h", "TV Asahi - MZINE Hearts2Hearts (Patreon)", "hearts2hearts", ["hearts2hearts"], lambda v: "mzine hearts2hearts" in v["title"].lower()),
        ("pt_kawaii_h2h", "Kawaii Lab. vs Hearts2Hearts (Patreon)", "hearts2hearts", ["hearts2hearts"], lambda v: "kawaii lab" in v["title"].lower()),
        ("pt_veiled_full", "Veiled Cup EP1-4 FULL ซับไทย (Patreon)", "veiled_cup", ["veiled_cup"], lambda v: "veiled cup" in v["title"].lower()),
    ]
    patreon_items = [v for v in videos_out if v.get("source") == "patreon"]
    for sid, stitle, main_grp, all_grps, pred in patreon_series_defs:
        matched_vids = [v["ytId"] for v in patreon_items if pred(v)]
        if matched_vids:
            # Reverse if episodes are numbered descending (e.g., E012 -> E01)
            if any("e01" in vid_by_id[x]["title"].lower() or "ep1" in vid_by_id[x]["title"].lower() for x in matched_vids[-1:]):
                matched_vids.reverse()
            playlists_out.append({
                "id": sid,
                "title": stitle,
                "count": len(matched_vids),
                "thumb": vid_by_id[matched_vids[0]]["thumb"],
                "groupId": main_grp,
                "groupIds": all_grps,
                "videoIds": matched_vids,
                "source": "patreon",
            })

    # 5.6 Auto-group custom SUMBAKKOKJIL / archive series into playlists
    custom_items = [v for v in videos_out if v.get("source") in ("artplayer", "embed")]
    custom_series_defs = [
        ("custom_sumbakkokjil_2", "SUMBAKKOKJIL 2 — Hearts2Hearts (Full VOD ซับไทย)", "hearts2hearts", "images/custom/sumbakkokjil_2_cover.webp"),
        ("custom_illit_sumbakkokjil_2", "SUMBAKKOKJIL 2 — ILLIT (Full VOD ซับไทย)", "illit", "images/custom/illit_sumbakkokjil_2_cover.webp"),
        ("custom_rescene_sumbakkokjil_2", "SUMBAKKOKJIL 2 — RESCENE (Full VOD ซับไทย)", "rescene", "images/custom/rescene_sumbakkokjil_2_cover.webp"),
    ]
    for sid, stitle, gid, poster in custom_series_defs:
        matched_vids = sorted(
            v["ytId"] for v in custom_items
            if "sumbakkokjil" in v["title"].lower() and gid in v["groups"]
        )
        if matched_vids:
            playlists_out.insert(0, {
                "id": sid,
                "title": stitle,
                "count": len(matched_vids),
                "thumb": poster if os.path.exists(os.path.join(SCRIPT_DIR, poster)) else vid_by_id[matched_vids[0]]["thumb"],
                "groupId": gid,
                "groupIds": [gid],
                "videoIds": matched_vids,
                "source": "custom",
            })

    # Pick channel avatar from channel thumbnails if present
    channel_thumbs = videos_raw.get("thumbnails") or []
    avatar_url = ""
    for th in channel_thumbs:
        if th.get("url") and "yt3.googleusercontent" in th["url"]:
            avatar_url = th["url"]
            break

    db = {
        "channel": {
            "handle": cfg["channel"]["handle"],
            "url": cfg["channel"]["url"],
            "name": cfg["channel"]["name"],
            "subtitle": cfg["channel"]["subtitle"],
            "avatar": avatar_url,
            "totalVideos": len(videos_out),
            "totalYoutube": len(videos_out) - patreon_count,
            "totalPatreon": patreon_count,
            "totalGroups": len(groups_out),
            "totalPlaylists": len(playlists_out),
            "updatedAt": datetime.now().strftime("%Y-%m-%d %H:%M"),
        },
        "groups": groups_out,
        "playlists": playlists_out,
        "videos": videos_out,
    }

    with open(OUTPUT_DB_PATH, "w", encoding="utf-8") as f:
        f.write("// Auto-generated by sync_channel.py — Do not edit manually\n")
        f.write("const sceneDatabase = ")
        json.dump(db, f, ensure_ascii=False, indent=2)
        f.write(";\n")

    print(f"\nGenerated {OUTPUT_DB_PATH}")
    print(f"Summary: {len(videos_out)} videos across {len(groups_out)} groups & {len(playlists_out)} playlists:")
    for g in groups_out:
        print(f"  - {g['name']:18s} ({g['id']}): {g['count']} videos")


if __name__ == "__main__":
    main()
