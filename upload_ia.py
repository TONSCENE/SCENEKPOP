#!/usr/bin/env python3
"""Upload a folder or video/subtitle files to Internet Archive using the ia CLI."""
import argparse
import os
import subprocess
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
VENV_IA = os.path.join(os.path.dirname(SCRIPT_DIR), ".venv", "bin", "ia")
IA_BIN = VENV_IA if os.path.exists(VENV_IA) else "ia"


def is_configured() -> bool:
    for path in [
        os.path.expanduser("~/.config/internetarchive/ia.ini"),
        os.path.expanduser("~/.ia"),
    ]:
        if os.path.exists(path):
            return True
    return False


def main():
    parser = argparse.ArgumentParser(description="Upload videos & VTT subtitles to archive.org")
    parser.add_argument("identifier", help="Unique archive.org item ID (e.g. h2h-sumbakkokjil-ep4)")
    parser.add_argument("files", nargs="+", help="Files or directory to upload")
    parser.add_argument("--title", required=True, help="Item title")
    parser.add_argument("--desc", default="", help="Item description")
    parser.add_argument("--subject", default="SCENEKPOP,K-Pop", help="Comma-separated tags")
    parser.add_argument("--creator", default="SCENEKPOP", help="Creator name")
    args = parser.parse_args()

    if not is_configured():
        print("❌ ยังไม่ได้ล็อกอิน Internet Archive CLI")
        print(f"กรุณารันคำสั่งนี้ใน Terminal เพื่อล็อกอิน (ใช้ครั้งเดียว):")
        print(f"  \"{IA_BIN}\" configure")
        print("หรือดู S3 Keys ได้ที่: https://archive.org/account/s3.php")
        sys.exit(1)

    upload_files = []
    for p in args.files:
        if os.path.isdir(p):
            for fname in sorted(os.listdir(p)):
                fpath = os.path.join(p, fname)
                if os.path.isfile(fpath) and not fname.startswith("."):
                    upload_files.append(fpath)
        elif os.path.isfile(p):
            upload_files.append(p)

    if not upload_files:
        print("❌ ไม่พบไฟล์สำหรับอัปโหลด")
        sys.exit(1)

    cmd = [
        IA_BIN, "upload", args.identifier,
        *upload_files,
        "--metadata", "mediatype:movies",
        "--metadata", "collection:opensource_movies",
        "--metadata", f"title:{args.title}",
        "--metadata", f"creator:{args.creator}",
        "--metadata", f"description:{args.desc or args.title}",
        "--metadata", f"subject:{args.subject}",
        "--checksum", "--verify", "--retries", "10", "--sleep", "5",
    ]

    print(f"🚀 Uploading {len(upload_files)} files to https://archive.org/details/{args.identifier} ...")
    subprocess.run(cmd, check=True)
    print(f"\n✅ Upload complete!")
    print(f"Details: https://archive.org/details/{args.identifier}")
    print(f"Embed:   https://archive.org/embed/{args.identifier}")


if __name__ == "__main__":
    main()
