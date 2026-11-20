#!/usr/bin/env python3
"""Sync (optional) and deploy SCENEKPOP+ to GitHub Pages."""
import argparse
import os
import subprocess
import sys

REPO_URL = "https://github.com/TONSCENE/SCENEKPOP"
PAGES_URL = "https://tonscene.github.io/SCENEKPOP/"
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))


def run(cmd, check=True):
    return subprocess.run(cmd, cwd=SCRIPT_DIR, check=check)


def main():
    parser = argparse.ArgumentParser(description="Deploy SCENEKPOP+ to GitHub Pages")
    parser.add_argument("message", nargs="?", default="Update SCENEKPOP+ content", help="Git commit message")
    parser.add_argument("--sync", action="store_true", help="Run sync_channel.py before committing")
    args = parser.parse_args()

    if args.sync:
        print("🔄 Syncing latest videos & playlists from @SCENEKPOP...")
        run([sys.executable, "sync_channel.py"])

    remotes = subprocess.run(["git", "remote"], cwd=SCRIPT_DIR, capture_output=True, text=True).stdout.split()
    if "origin" not in remotes:
        print("⚠️ ยังไม่ได้ตั้งค่า git remote 'origin'")
        print(f"1. สร้าง Repository ใหม่ชื่อ SCENEKPOP บน GitHub ({REPO_URL})")
        print("2. รันคำสั่ง:")
        print(f"   git -C \"{SCRIPT_DIR}\" remote add origin {REPO_URL}.git")
        print(f"   git -C \"{SCRIPT_DIR}\" push -u origin main")
        print("3. เปิด Settings -> Pages -> Deploy from a branch (main / root)")
        print(f"   จากนั้นเว็บจะใช้งานได้ที่: {PAGES_URL}")
        sys.exit(1)

    print(f"🚀 Deploying SCENEKPOP+ to {PAGES_URL} ...")
    run(["git", "add", "index.html", "db.js", "group_config.json", "patreon_posts.json", "custom_videos.json", "images/", "subs/", "sync_channel.py", "upload_ia.py", "deploy.py", "README.md", ".gitignore"])

    status = subprocess.run(["git", "status", "--porcelain"], cwd=SCRIPT_DIR, capture_output=True, text=True)
    if status.stdout.strip():
        run(["git", "commit", "-m", args.message])
        run(["git", "push", "-u", "origin", "main"])
        print(f"✅ Pushed changes to {REPO_URL}")
    else:
        print("ℹ️ No new changes to commit; pushing existing commits...")
        run(["git", "push", "-u", "origin", "main"])

    print(f"🎉 Live URL: {PAGES_URL}")


if __name__ == "__main__":
    main()
