#!/usr/bin/env python3

import json
import os
import re
import sys
import time
from datetime import datetime, timedelta

import requests
import zstandard as zstd
from _common import BASE_DIR, FILENAME_PATTERN, load_config
from requests.adapters import HTTPAdapter
from tqdm import tqdm
from urllib3.util.retry import Retry

# --- End Configuration ---


def build_session() -> requests.Session:
    """
    Create a requests session with retry on transient failures.
    Retries 5xx responses and connection errors; backs off exponentially.
    """
    session = requests.Session()
    retry = Retry(
        total=5,
        backoff_factor=1.0,  # 1s, 2s, 4s, 8s, 16s
        status_forcelist=(408, 429, 500, 502, 503, 504),
        allowed_methods=frozenset(["POST", "GET"]),
        raise_on_status=False,
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session


def get_upload_selection():
    """
    Asks the user how they want to filter the upload.
    Returns (cutoff_days, month_filter) where one is present or both are None.
    """
    while True:
        user_input = input(
            "Upload options:\n"
            " - Enter a number (e.g., 30, 7) for days back\n"
            " - Enter a month (e.g., 2024-12) for a specific month\n"
            " - Enter a year with asterisk (e.g., 2024-*) for a specific year\n"
            " - Press Enter or type 0 to upload ALL transcripts\n"
            "Your choice: "
        ).strip()

        if not user_input or user_input == "0":
            return None, None

        # Check for YYYY-MM
        if re.match(r"^\d{4}-\d{2}$", user_input):
            return None, user_input.replace("-", "")

        # Check for YYYY-*
        if re.match(r"^\d{4}-\*$", user_input):
            return None, user_input.split("-")[0]

        try:
            days = int(user_input)
            if days > 0:
                return days, None
            else:
                print("Please enter a positive number, a month (YYYY-MM), or 0/Enter for all.")
        except ValueError:
            print("Invalid input. Please enter a number, YYYY-MM, or press Enter.")


def process_and_upload(session, root, file, streamer_name, cutoff_date, month_filter, headers, server_url):
    """
    Parses a single transcript file, checks its date/month (if required),
    and uploads it to the server.

    Returns:
        (status_string, original_size, compressed_size, upload_seconds)

        status_string:
            'success' if uploaded
            'skipped' if skipped due to date
            'failed' if an error occurred
    """
    match = FILENAME_PATTERN.match(file)
    if not match:
        # Use tqdm.write to print without breaking the bar
        tqdm.write(f"-> Skipping file (does not match pattern): {file}")
        return "failed", 0, 0, 0.0

    # Extract data from regex groups
    date_str = match.group(1)  # This is 'YYYYMMDD'
    stream_type = match.group(2)
    stream_title = match.group(3).strip()
    stream_id = match.group(4)

    try:
        # Parse the 'YYYYMMDD' string into a date object
        file_date_obj = datetime.strptime(date_str, "%Y%m%d").date()

        # Create the desired 'YYYY-MM-DD' formatted string
        formatted_date = file_date_obj.strftime("%Y-%m-%d")

    except ValueError:
        tqdm.write(f"-> Skipping file (invalid date format): {file}")
        return "failed", 0, 0, 0.0

    if month_filter and not date_str.startswith(month_filter):
        return "skipped_date", 0, 0, 0.0

    if cutoff_date and file_date_obj < cutoff_date:
        # File is too old, skip it
        return "skipped_date", 0, 0, 0.0

    full_path = os.path.join(root, file)
    try:
        with open(full_path, encoding="utf-8") as f:
            srt_content = f.read()
    except Exception as e:
        tqdm.write(f"-> ERROR reading file {full_path}: {e}")
        return "failed", 0, 0, 0.0

    payload = {
        "streamer": streamer_name,
        "date": formatted_date,
        "streamType": stream_type,
        "streamTitle": stream_title,
        "id": stream_id,
        "srt": srt_content,
    }

    try:
        # Compress payload
        json_data = json.dumps(payload).encode("utf-8")
        cctx = zstd.ZstdCompressor(level=22)
        compressed_data = cctx.compress(json_data)

        # Add compression header to a copy of headers to avoid side effects
        req_headers = headers.copy()
        req_headers["Content-Encoding"] = "zstd"

        uri = f"{server_url}/transcript"
        start = time.perf_counter()
        response = session.post(uri, data=compressed_data, headers=req_headers, timeout=30)
        upload_seconds = time.perf_counter() - start
        response.raise_for_status()  # Raise exception for 4xx/5xx errors

        return "success", len(json_data), len(compressed_data), upload_seconds

    except requests.exceptions.HTTPError as e:
        tqdm.write(f"-> HTTP ERROR for {file}: {e.response.status_code} - {e.response.text}")
    except requests.exceptions.RequestException as e:
        tqdm.write(f"-> ERROR uploading {file}: {e}")

    return "failed", 0, 0, 0.0


def main():
    """
    Main function to walk the directory and process files.
    """

    config = load_config()
    api_key = config["api_key"]
    server_url = config["server_url"]
    print("Configuration loaded successfully.")

    if not os.path.isdir(BASE_DIR):
        print(f"Error: Base directory '{BASE_DIR}' not found.")
        print("Please run this script from the correct location.")
        sys.exit(1)

    # Ask user for selection
    days_to_upload, month_filter = get_upload_selection()

    cutoff_date = None
    if days_to_upload:
        today = datetime.now().date()
        cutoff_date = today - timedelta(days=days_to_upload)
        print(f"\nStarting upload: Only files from the last {days_to_upload} days.")
        print(f"Uploading files dated on or after: {cutoff_date.strftime('%Y-%m-%d')}")
    elif month_filter:
        if len(month_filter) == 4:
            print(f"\nStarting upload: Only files from the year {month_filter}.")
        else:
            print(f"\nStarting upload: Only files from {month_filter[:4]}-{month_filter[4:]}.")
    else:
        print("\nStarting upload: Processing ALL transcripts.")

    print(f"Target server: {server_url}")

    headers = {
        "X-API-Key": api_key,
        "Content-Type": "application/json",
    }

    # --- First pass: Collect all files to process ---
    print("Scanning directories to find transcripts...")
    files_to_process = []
    for root, dirs, files in os.walk(BASE_DIR):
        if root == BASE_DIR:
            if not dirs:
                print("No streamer folders found in 'Transcript' directory.")
            continue

        try:
            streamer_name = os.path.relpath(root, BASE_DIR).split(os.path.sep)[0]
        except Exception:
            # This can happen if root == BASE_DIR, which we skip
            continue

        if not streamer_name:
            continue

        for file in files:
            if file.endswith(".srt"):
                # Store (root, file, streamer_name)
                files_to_process.append((root, file, streamer_name))

    if not files_to_process:
        print("No .srt files found to upload.")
        sys.exit(0)

    print(f"Found {len(files_to_process)} total transcripts.")

    # --- Second pass: Process files with progress bar ---
    success_count = 0
    fail_count = 0
    skipped_date_count = 0
    total_original_bytes = 0
    total_compressed_bytes = 0
    upload_times: list[float] = []

    # Session with retry on transient failures
    with build_session() as session:
        # Wrap the list with tqdm for the progress bar
        for root, file, streamer_name in tqdm(files_to_process, desc="Uploading Transcripts", unit="file"):
            result, orig_size, comp_size, upload_seconds = process_and_upload(
                session,
                root,
                file,
                streamer_name,
                cutoff_date,
                month_filter,
                headers,
                server_url,
            )

            if result == "success":
                success_count += 1
                total_original_bytes += orig_size
                total_compressed_bytes += comp_size
                upload_times.append(upload_seconds)
            elif result == "failed":
                fail_count += 1
            elif result == "skipped_date":
                skipped_date_count += 1

    print("\n--- Upload Complete ---")
    print(f"Successfully uploaded: {success_count}")
    if fail_count > 0:
        print(f"Failed to upload:   	{fail_count}")
    if cutoff_date or month_filter:
        print(f"Skipped (non-matching): {skipped_date_count}")

    if total_original_bytes > 0:
        saved_bytes = total_original_bytes - total_compressed_bytes
        savings_percent = (saved_bytes / total_original_bytes) * 100
        print(f"\nTotal Data Sent:   {total_compressed_bytes / 1024:.2f} KB")
        print(f"Original Size:     {total_original_bytes / 1024:.2f} KB")
        print(f"Total Data Saved:  {saved_bytes / 1024:.2f} KB ({savings_percent:.1f}%)")

    if upload_times:
        total_time = sum(upload_times)
        avg_time = total_time / len(upload_times)
        max_time = max(upload_times)
        min_time = min(upload_times)
        print("\n--- Upload Timing ---")
        print(f"Total upload time: {total_time:.2f} s")
        print(f"Average per file:  {avg_time * 1000:.1f} ms")
        print(f"Largest:           {max_time * 1000:.1f} ms")
        print(f"Smallest:          {min_time * 1000:.1f} ms")


if __name__ == "__main__":
    main()
