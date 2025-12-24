#!/usr/bin/env python3

import os
import re
import argparse
import sys
from pathlib import Path

# Ensure UTF-8 output for terminal
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

def parse_date(date_str):
    # Convert YYYY-MM-DD or YYYY-MM or YYYY to YYYYMMDD prefix format
    return date_str.replace("-", "")

def get_id_from_filename(filename):
    # Extract ID between [ and ] at the end before extension.
    # Use [^\[\]]+ to ensure we don't capture multiple sets of brackets.
    # We want the LAST set of brackets.
    match = re.search(r'\[([^\[\]]+)\]\.srt$', filename)
    if match:
        return match.group(1)
    return None

def main():
    parser = argparse.ArgumentParser(description="Delete transcript files and clean archive based on date.")
    parser.add_argument("date", help="Date in YYYY-MM-DD, YYYY-MM, or YYYY format.")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be deleted without actually deleting.")
    args = parser.parse_args()

    date_prefix = parse_date(args.date)
    transcript_dir = Path("Transcript")
    archive_file = Path("yt-dlp-archive.txt")
    
    allowed_types = {"Stream", "Video", "TwitchVod"}
    
    matched_files = []
    matched_ids = set()

    if not transcript_dir.exists():
        print(f"Error: Transcript directory '{transcript_dir}' not found.")
        return

    # Walk through transcripts
    for root, dirs, files in os.walk(transcript_dir):
        for file in files:
            if not file.endswith(".srt"):
                continue
            
            # Check date prefix
            if not file.startswith(date_prefix):
                continue
                
            # Split filename to get stream type
            # Format: 20240101 - Stream Type - Title - [ID].srt
            parts = file.split(" - ")
            if len(parts) < 2:
                continue
                
            stream_type = parts[1]
            if stream_type not in allowed_types:
                continue
                
            video_id = get_id_from_filename(file)
            if video_id:
                matched_files.append(Path(root) / file)
                matched_ids.add(video_id)

    if not matched_files:
        print(f"No matching files found for date prefix '{date_prefix}'.")
        return

    print(f"Found {len(matched_files)} matching files.")
    for f in matched_files:
        print(f"  {f}")

    if args.dry_run:
        print("\n[DRY RUN] Would delete the files listed above.")
        print(f"[DRY RUN] Would remove {len(matched_ids)} IDs from {archive_file}.")
        return

    # Actual deletion
    # 1. Update archive file
    if archive_file.exists():
        print(f"Cleaning up {archive_file}...")
        with open(archive_file, "r", encoding="utf-8") as f:
            lines = f.readlines()
        
        original_count = len(lines)
        # yt-dlp-archive.txt format: "extractor ID"
        new_lines = []
        for line in lines:
            parts = line.strip().split()
            if len(parts) >= 2 and parts[1] in matched_ids:
                continue
            new_lines.append(line)
        
        removed_count = original_count - len(new_lines)
        
        with open(archive_file, "w", encoding="utf-8") as f:
            f.writelines(new_lines)
        print(f"Removed {removed_count} lines from {archive_file}.")
    else:
        print(f"Warning: {archive_file} not found, skipping archive cleanup.")

    # 2. Delete files
    print("Deleting files...")
    for f in matched_files:
        try:
            f.unlink()
            print(f"  Deleted: {f}")
        except Exception as e:
            print(f"  Error deleting {f}: {e}")

    print("Done.")

if __name__ == "__main__":
    # Ensure we are in the root directory relative to the script if needed
    # (The tool calls are usually relative to the workspace root)
    main()
