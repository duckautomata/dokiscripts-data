#!/usr/bin/env python3

import os
import sys
from datetime import datetime
from typing import TypedDict

import requests
from _common import BASE_DIR, FILENAME_PATTERN, load_config

# --- Configuration ---

REPORT_FILE: str = "missing.txt"

# --- Type Definitions ---


class StreamMetadata(TypedDict):
    streamer: str
    date: str
    streamType: str
    streamTitle: str
    id: str


# Local metadata includes the filename, which server data might not have
class LocalStreamMetadata(StreamMetadata):
    filename: str


class MismatchDetail(TypedDict):
    id: str
    filename: str
    diffs: list[str]


# --- End Configuration ---


def fetch_server_info(server_url: str, headers: dict[str, str]) -> dict[str, StreamMetadata]:
    """
    GET {server_url}/info to retrieve the list of known streams.
    Returns a dictionary keyed by ID for easy lookup.
    """
    base = server_url.rstrip("/")
    url = f"{base}/info"

    print(f"Fetching server info from: {url}")
    try:
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        data: list[StreamMetadata] = response.json()

        server_map: dict[str, StreamMetadata] = {}
        for entry in data:
            if "id" in entry:
                server_map[entry["id"]] = entry

        return server_map

    except requests.exceptions.RequestException as e:
        print(f"Error fetching server info: {e}")
        sys.exit(1)


def scan_local_files() -> dict[str, LocalStreamMetadata]:
    """
    Scans the BASE_DIR for .srt files matching the pattern.
    Returns a dictionary keyed by ID containing the parsed metadata.
    """
    local_map: dict[str, LocalStreamMetadata] = {}

    print(f"Scanning '{BASE_DIR}' for local files...")

    files_found = 0

    for root, _, files in os.walk(BASE_DIR):
        if root == BASE_DIR:
            continue

        try:
            streamer_name = os.path.relpath(root, BASE_DIR).split(os.path.sep)[0]
        except Exception:
            continue

        if not streamer_name:
            continue

        for file in files:
            if not file.endswith(".srt"):
                continue

            match = FILENAME_PATTERN.match(file)
            if match:
                files_found += 1

                raw_date = match.group(1)
                stream_type = match.group(2)
                stream_title = match.group(3).strip()
                stream_id = match.group(4)

                formatted_date: str
                try:
                    dt = datetime.strptime(raw_date, "%Y%m%d")
                    formatted_date = dt.strftime("%Y-%m-%d")
                except ValueError:
                    formatted_date = raw_date

                meta: LocalStreamMetadata = {
                    "streamer": streamer_name,
                    "date": formatted_date,
                    "streamType": stream_type,
                    "streamTitle": stream_title,
                    "id": stream_id,
                    "filename": file,
                }

                local_map[stream_id] = meta

    print(f"Found {files_found} valid local transcripts.")
    return local_map


def compare_data(
    server_map: dict[str, StreamMetadata], local_map: dict[str, LocalStreamMetadata]
) -> tuple[list[StreamMetadata], list[LocalStreamMetadata], list[MismatchDetail]]:

    missing_local: list[StreamMetadata] = []  # Server has, We don't
    missing_server: list[LocalStreamMetadata] = []  # We have, Server doesn't
    mismatches: list[MismatchDetail] = []  # Data mismatch

    all_server_ids: set[str] = set(server_map.keys())
    all_local_ids: set[str] = set(local_map.keys())

    # Check Server list against Local
    for s_id in all_server_ids:
        if s_id not in local_map:
            missing_local.append(server_map[s_id])
        else:
            # Check consistency
            s_data = server_map[s_id]
            l_data = local_map[s_id]

            diffs: list[str] = []
            fields_to_check = ["streamer", "date", "streamType", "streamTitle"]

            for field in fields_to_check:
                # Type ignore note: TypedDict keys are known, but iterating strings
                # can trigger strict type checkers.
                s_val = s_data.get(field, "")  # type: ignore
                l_val = l_data.get(field, "")  # type: ignore

                if s_val != l_val:
                    diffs.append(f"{field}: Server='{s_val}' vs Local='{l_val}'")

            if diffs:
                mismatches.append({"id": s_id, "filename": l_data["filename"], "diffs": diffs})

    # Check Local list against Server
    for l_id in all_local_ids:
        if l_id not in server_map:
            missing_server.append(local_map[l_id])

    return missing_local, missing_server, mismatches


def generate_report(
    missing_local: list[StreamMetadata],
    missing_server: list[LocalStreamMetadata],
    mismatches: list[MismatchDetail],
) -> None:
    """
    Prints summary to console and writes details to missing.txt
    """

    # --- Console Output ---
    print("\n" + "=" * 40)
    print(f"{'VERIFICATION SUMMARY':^40}")
    print("=" * 40)
    print(f"Missing Local Files:  {len(missing_local)}")
    print(f"Missing Server Files: {len(missing_server)}")
    print(f"Metadata Mismatches:  {len(mismatches)}")
    print("-" * 40)

    if not missing_local and not missing_server and not mismatches:
        print("SUCCESS: Local files and Server are perfectly synced.")
        return
    else:
        print(f"Detailed report written to: {REPORT_FILE}")

    # --- File Output ---
    try:
        with open(REPORT_FILE, "w", encoding="utf-8") as f:
            f.write("VERIFICATION REPORT\n")
            f.write(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("=" * 60 + "\n\n")

            # Section 1: Missing Local
            f.write(f"--- MISSING LOCAL FILES ({len(missing_local)}) ---\n")
            f.write("(Server has these entries, but no local .srt found)\n\n")
            if missing_local:
                for s_item in missing_local:
                    f.write(f"ID: {s_item.get('id')}\n")
                    f.write(f"  Streamer: {s_item.get('streamer')}\n")
                    f.write(f"  Date:     {s_item.get('date')}\n")
                    f.write(f"  Title:    {s_item.get('streamTitle')}\n")
                    f.write("-" * 20 + "\n")
            else:
                f.write("None.\n\n")

            f.write("\n" + "=" * 60 + "\n\n")

            # Section 2: Missing Server
            f.write(f"--- MISSING SERVER FILES ({len(missing_server)}) ---\n")
            f.write("(We have these .srt files locally, but Server does not list them)\n\n")
            if missing_server:
                for l_item in missing_server:
                    f.write(f"ID: {l_item.get('id')}\n")
                    f.write(f"  File:     {l_item.get('filename')}\n")
                    f.write(f"  Streamer: {l_item.get('streamer')}\n")
                    f.write(f"  Date:     {l_item.get('date')}\n")
                    f.write("-" * 20 + "\n")
            else:
                f.write("None.\n\n")

            f.write("\n" + "=" * 60 + "\n\n")

            # Section 3: Mismatches
            f.write(f"--- METADATA MISMATCHES ({len(mismatches)}) ---\n")
            f.write("(ID exists in both, but specific fields differ)\n\n")
            if mismatches:
                for m_item in mismatches:
                    f.write(f"ID: {m_item['id']}\n")
                    f.write(f"  File: {m_item['filename']}\n")
                    for diff in m_item["diffs"]:
                        f.write(f"  [!] {diff}\n")
                    f.write("-" * 20 + "\n")
            else:
                f.write("None.\n\n")

    except OSError as e:
        print(f"\nError writing to report file: {e}")


def main() -> None:
    # /info is public — no api_key needed
    config = load_config(require_api_key=False)
    server_url = config["server_url"]

    if not os.path.isdir(BASE_DIR):
        print(f"Error: Base directory '{BASE_DIR}' not found.")
        sys.exit(1)

    headers: dict[str, str] = {"Content-Type": "application/json"}

    server_map = fetch_server_info(server_url, headers)
    print(f"Server reported {len(server_map)} streams.")

    local_map = scan_local_files()

    print("Verifying consistency...")
    missing_local, missing_server, mismatches = compare_data(server_map, local_map)
    missing_local.sort(key=lambda d: d["date"])
    missing_server.sort(key=lambda d: d["date"])
    mismatches.sort(key=lambda d: d["filename"])

    generate_report(missing_local, missing_server, mismatches)


if __name__ == "__main__":
    main()
