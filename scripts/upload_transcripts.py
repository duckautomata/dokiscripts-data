#!/usr/bin/env python3

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

def get_day_limit():
    """
    Asks the user how many days back to check.
    Returns an integer or None.
    """
    while True:
        user_input = input(
            "How many days back should we upload? (e.g., 30, 7) "
            "\n[Press Enter or type 0 to upload ALL transcripts]: "
        ).strip()
        
        if not user_input or user_input == "0":
            return None  # Signal to upload all
            
        try:
            days = int(user_input)
            if days > 0:
                return days
            else:
                print("Please enter a positive number, or 0/Enter for all.")
        except ValueError:
            print("Invalid input. Please enter a number (like 30) or press Enter.")


def process_and_upload(root, file, streamer_name, cutoff_date, headers, server_url):
    """
    Parses a single transcript file, checks its date (if required),
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

    if stream_type.strip().lower() == "members":
        return 'skipped_members'

    try:
        # Parse the 'YYYYMMDD' string into a date object
        file_date_obj = datetime.strptime(date_str, "%Y%m%d").date()
        
        # Create the desired 'YYYY-MM-DD' formatted string
        formatted_date = file_date_obj.strftime("%Y-%m-%d")
        
    except ValueError:
        tqdm.write(f"-> Skipping file (invalid date format): {file}")
        return 'failed'


    if cutoff_date:
        # Use the date object we already parsed
        if file_date_obj < cutoff_date:
            # File is too old, skip it
            return 'skipped'

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
        response = requests.post(server_url, json=payload, headers=headers, timeout=30)
        response.raise_for_status()  # Raise exception for 4xx/5xx errors
        
        # Don't print on success, it clutters the output
        # tqdm.write(f"-> SUCCESS: Uploaded {file}")
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

    # Ask user for time limit
    days_to_upload = get_day_limit()
    
    cutoff_date = None
    if days_to_upload:
        today = datetime.now().date()
        cutoff_date = today - timedelta(days=days_to_upload)
        print(f"\nStarting upload: Only files from the last {days_to_upload} days.")
        print(f"Uploading files dated on or after: {cutoff_date.strftime('%Y-%m-%d')}")
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
    skipped_members_count = 0

    # Wrap the list with tqdm for the progress bar
    for root, file, streamer_name in tqdm(files_to_process, desc="Uploading Transcripts", unit="file"):
        
        result = process_and_upload(root, file, streamer_name, cutoff_date, headers, server_url)
        
        if result == 'success':
            success_count += 1
        elif result == 'failed':
            fail_count += 1
        elif result == 'skipped_date':
            skipped_date_count += 1
        elif result == 'skipped_members':
            skipped_members_count += 1

    print("\n--- Upload Complete ---")
    print(f"Successfully uploaded: {success_count}")
    if fail_count > 0:
        print(f"Failed to upload:   	{fail_count}")
    if cutoff_date:
        print(f"Skipped (too old):   {skipped_date_count}")
    if skipped_members_count > 0:
        print(f"Skipped (Members):   {skipped_members_count}")


if __name__ == "__main__":
    main()
