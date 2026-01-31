#!/usr/bin/env python3

import gzip
import json
import os
import re
import requests
import sys
from datetime import datetime, timedelta
from tqdm import tqdm
import yaml # Import tqdm

# --- Configuration ---

# The root folder containing your streamer transcripts
BASE_DIR = "Transcript"

# Config file name
CONFIG_FILE = "config.yaml"

# Regex to parse the filename:
# {YYYYMMDD} - {StreamType} - {StreamName} - [{id}].srt
FILENAME_PATTERN = re.compile(r"^(\d{8}) - (.+?) - (.+) - \[([^\]]+)\]\.srt$")

# --- End Configuration ---

def load_config():
    if not os.path.exists(CONFIG_FILE):
        print(f"Error: Configuration file '{CONFIG_FILE}' not found.")
        sys.exit(1)
        
    try:
        with open(CONFIG_FILE, 'r') as f:
            config = yaml.safe_load(f)
            
        if not config or 'api_key' not in config:
            print(f"Error: 'api_key' not found in '{CONFIG_FILE}'.")
            print("Please ensure the file has the line: api_key: YOUR_KEY")
            sys.exit(1)

        if not config or 'server_url' not in config:
            print(f"Error: 'server_url' not found in '{CONFIG_FILE}'.")
            print("Please ensure the file has the line: server_url: YOUR_SERVER")
            sys.exit(1)
            
        api_key = config['api_key']
        server_url = config['server_url']
            
        return api_key, server_url
        
    except yaml.YAMLError as e:
        print(f"Error parsing '{CONFIG_FILE}': {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Error reading '{CONFIG_FILE}': {e}")
        sys.exit(1)

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
        'success' if uploaded
        'skipped' if skipped due to date
        'failed' if an error occurred
    """
    match = FILENAME_PATTERN.match(file)
    if not match:
        # Use tqdm.write to print without breaking the bar
        tqdm.write(f"-> Skipping file (does not match pattern): {file}")
        return 'failed'

    # Extract data from regex groups
    date_str = match.group(1)       # This is 'YYYYMMDD'
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
        return 'failed'


    if month_filter:
        if not date_str.startswith(month_filter):
            return 'skipped_date'

    if cutoff_date:
        # Use the date object we already parsed
        if file_date_obj < cutoff_date:
            # File is too old, skip it
            return 'skipped_date'

    full_path = os.path.join(root, file)
    try:
        with open(full_path, 'r', encoding='utf-8') as f:
            srt_content = f.read()
    except Exception as e:
        tqdm.write(f"-> ERROR reading file {full_path}: {e}")
        return 'failed'

    payload = {
        "streamer": streamer_name,
        "date": formatted_date,
        "streamType": stream_type,
        "streamTitle": stream_title,
        "id": stream_id,
        "srt": srt_content
    }

    try:
        # Compress payload
        json_data = json.dumps(payload).encode('utf-8')
        compressed_data = gzip.compress(json_data)
        
        # Add compression header to a copy of headers to avoid side effects
        req_headers = headers.copy()
        req_headers['Content-Encoding'] = 'gzip'

        uri = f"{server_url}/transcript"
        response = session.post(uri, data=compressed_data, headers=req_headers, timeout=30)
        response.raise_for_status()  # Raise exception for 4xx/5xx errors
        
        return 'success'
        
    except requests.exceptions.HTTPError as e:
        tqdm.write(f"-> HTTP ERROR for {file}: {e.response.status_code} - {e.response.text}")
    except requests.exceptions.RequestException as e:
        tqdm.write(f"-> ERROR uploading {file}: {e}")
    
    return 'failed'


def main():
    """
    Main function to walk the directory and process files.
    """

    print(f"Loading configuration from {CONFIG_FILE}...")
    api_key, server_url = load_config()
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
        "X-API-Key": api_key,  # <-- Use the loaded key
        "Content-Type": "application/json"
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

    # Create a session for persistent connections
    with requests.Session() as session:
        # Wrap the list with tqdm for the progress bar
        for root, file, streamer_name in tqdm(files_to_process, desc="Uploading Transcripts", unit="file"):
            result = process_and_upload(session, root, file, streamer_name, cutoff_date, month_filter, headers, server_url)

            if result == 'success':
                success_count += 1
            elif result == 'failed':
                fail_count += 1
            elif result == 'skipped_date':
                skipped_date_count += 1

    print("\n--- Upload Complete ---")
    print(f"Successfully uploaded: {success_count}")
    if fail_count > 0:
        print(f"Failed to upload:   	{fail_count}")
    if cutoff_date or month_filter:
        print(f"Skipped (non-matching): {skipped_date_count}")


if __name__ == "__main__":
    main()
