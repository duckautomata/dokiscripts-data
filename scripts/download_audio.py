#!/usr/bin/env python3

import argparse
import os
import subprocess
import sys
from datetime import datetime

from _common import BASE_DIR, load_channels

# --- Configuration ---

# Assumes 'yt-dlp' is in your system's PATH.
# On Windows, this will correctly find 'yt-dlp.exe'.
YT_DLP_CMD = "yt-dlp"

VALID_TYPES = {"Video", "Stream", "Members", "Twitch", "TwitchVod", "External"}

# yt-dlp ERROR/WARNING lines are mirrored to this file for post-run debugging.
# The file is truncated at the start of each run.
LOG_FILE = "yt-dlp-errors.log"

# --- End Configuration ---


def _init_log_file():
    """Truncate the log file and write a run-start header."""
    with open(LOG_FILE, "w", encoding="utf-8") as f:
        f.write(f"=== yt-dlp run started at {datetime.now().isoformat(timespec='seconds')} ===\n")


def _run_and_log_stderr(command: list[str], url: str, download_type: str, channel: str) -> int:
    """
    Run `command`, streaming stderr through to the terminal (so yt-dlp progress
    stays visible) while appending every line to LOG_FILE. Returns the count
    of ERROR:/WARNING: lines seen (for summary reporting).
    """
    problem_count = 0
    process = subprocess.Popen(
        command,
        stdout=None,  # pass-through
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        errors="replace",
        bufsize=1,
    )

    assert process.stderr is not None  # PIPE guarantees this; hint for type checkers
    with open(LOG_FILE, "a", encoding="utf-8") as log:
        log.write(f"\n--- {channel} | {download_type} | {url} ---\n")
        for line in process.stderr:
            sys.stderr.write(line)
            sys.stderr.flush()
            log.write(line)
            if "ERROR:" in line or "WARNING:" in line:
                problem_count += 1

    process.wait()
    return problem_count


def get_audio(url: str, download_type: str, channel: str):
    """
    Calls yt-dlp to download audio for a given URL.

    Args:
        url: The URL to download from.
        download_type: The type of content (e.g., "Members", "Video").
        channel: The streamer's name, used for the folder.
    """

    output_template = f"{BASE_DIR}/{channel}/%(upload_date)s - {download_type} - %(title)s - [%(id)s].%(ext)s"

    command = [
        YT_DLP_CMD,
        "--download-archive",
        "yt-dlp-archive.txt",
        "--cookies",
        "cookies.txt",
    ]

    if download_type == "Members":
        print(f"\nDownloading (Members): {channel}")
    else:
        print(f"\nDownloading (Regular): {channel} - {download_type}")

    # Filter for non-members download, it filters out members content.
    # And for members download, it filters only members content.
    # Note: availability filter is for YouTube only.
    match_filter = "!is_live"
    if "youtube.com" in url.lower() or "youtu.be" in url.lower():
        if download_type == "Members":
            match_filter += " & availability = subscriber_only"
        else:
            match_filter += " & availability != subscriber_only"

    command.extend(
        [
            "--ignore-errors",
            "--match-filter",
            match_filter,
            "-f",
            "ba",
            "-o",
            output_template,
            "--windows-filenames",
            "--sleep-requests",
            "1",
            "--sleep-interval",
            "15",
        ]
    )

    if "twitch.tv" in url.lower():
        print("-> Twitch URL detected, skipping thumbnail.")
    else:
        print("-> YouTube URL detected, adding thumbnail.")
        command.append("--write-thumbnail")

    command.append(url)

    try:
        _run_and_log_stderr(command, url, download_type, channel)
    except FileNotFoundError:
        print(f"\n[Error] '{YT_DLP_CMD}' command not found.")
        print("Please ensure yt-dlp is installed and in your system's PATH.")
        sys.exit(1)
    except Exception as e:
        print(f"\nAn error occurred while processing {url}: {e}")
        with open(LOG_FILE, "a", encoding="utf-8") as log:
            log.write(f"PYTHON EXCEPTION: {e}\n")


def update_tools():
    """Update yt-dlp and deno."""
    print("Attempting to update yt-dlp...")
    try:
        subprocess.run([YT_DLP_CMD, "-U"], check=True)
    except FileNotFoundError:
        print(f"\n[Error] '{YT_DLP_CMD}' command not found.")
        print("Please ensure yt-dlp is installed and in your system's PATH.")
        sys.exit(1)
    except subprocess.CalledProcessError as e:
        print(f"Failed to update yt-dlp (command failed): {e}")
    except Exception as e:
        print(f"An unknown error occurred during update: {e}")

    print("Attempting to update deno...")
    try:
        subprocess.run(["deno", "upgrade"], check=True)
    except FileNotFoundError:
        print("\n[Error] 'deno' command not found.")
        print("Please ensure deno is installed and in your system's PATH.")
        print("deno is required for yt-dlp to work.")
        sys.exit(1)
    except subprocess.CalledProcessError as e:
        print(f"Failed to update deno (command failed): {e}")
    except Exception as e:
        print(f"An unknown error occurred during update: {e}")


def main():
    parser = argparse.ArgumentParser(description="Download audio from configured channels.")
    parser.add_argument(
        "--skip-update",
        action="store_true",
        help="Skip updating yt-dlp and deno before downloading.",
    )
    args = parser.parse_args()

    if not args.skip_update:
        update_tools()
    else:
        print("Skipping tool updates (--skip-update).")

    channels = load_channels()

    # Validate config before running any downloads
    for channel in channels:
        name = channel.get("name")
        if not name:
            print("Error: channel entry missing 'name' field.")
            sys.exit(1)
        for source in channel.get("sources", []):
            stype = source.get("type")
            if stype not in VALID_TYPES:
                print(f"Error: invalid type '{stype}' for channel '{name}'. Must be one of {VALID_TYPES}.")
                sys.exit(1)
            if not source.get("url"):
                print(f"Error: source for channel '{name}' missing 'url'.")
                sys.exit(1)

    _init_log_file()
    print(f"Errors/warnings will be logged to '{LOG_FILE}'.")
    print("\n--- Starting Downloads ---")

    for channel in channels:
        name = channel["name"]
        for source in channel.get("sources", []):
            get_audio(url=source["url"], download_type=source["type"], channel=name)

    print("\n--- Download process finished. ---")
    print(f"See '{LOG_FILE}' for any errors/warnings from this run.")


if __name__ == "__main__":
    os.makedirs(BASE_DIR, exist_ok=True)
    main()
