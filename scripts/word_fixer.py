#!/usr/bin/env python3

import os
import re
from datetime import datetime, timedelta, date
from tqdm import tqdm

# --- Configuration ---

# Case sensitive. But we replace for both lowercase and uppercase versions.
# So it's best to only have lowercase here.
# "old_word1": "new_word1"
word_map = {
    "f**k": "fuck",
    "f***ing": "fucking",
    "f*****g": "fucking",
    "f******": "fucking",
    "fuck***t": "fucking bullshit",
    "fuck***": "fucking",
    "fuck*d": "fucked",
    "f**ing": "fucking",
    "f*****": "fucker",
    "f***": "fuck",
    "f**": "fuck",
    "sh**": "shit",
    "s**t": "shit",
    "s***": "shit",
    "a**": "ass",
    "b**ch": "bitch",
    "b***h": "bitch",
    "c***": "cunt",
    "p***y": "pussy",
    "d**n": "damn",
    "****": "fuck",
}

directory = "Transcript"

# Regex to parse the filename:
# {YYYYMMDD} - {StreamType} - {StreamName} - [{id}].srt
FILENAME_PATTERN = re.compile(r"^(\d{8}) - (.+?) - (.+) - \[([^\]]+)\]\.srt$")

# --- End Configuration ---


def get_day_limit():
    """
    Asks the user how many days back to check.
    Returns an integer or None (for all).
    """
    while True:
        user_input = input(
            "How many days back should we fix? (e.g., 30, 7) "
            "\n[Press Enter or type 0 to fix ALL transcripts]: "
        ).strip()
        
        if not user_input or user_input == "0":
            return None  # Signal to fix all
            
        try:
            days = int(user_input)
            if days > 0:
                return days
            else:
                print("Please enter a positive number, or 0/Enter for all.")
        except ValueError:
            print("Invalid input. Please enter a number (like 30) or press Enter.")


def replace_words_in_srt_files(word_map: dict[str, str], directory: str, cutoff_date: date | None):
    """
    Finds all .srt files in a directory, filters by date if the filename
    matches the pattern, and replaces words based on a map.
    """
    
    srt_files_to_process = []
    skipped_date = 0

    print("Scanning for .srt files...")
    for root, _, files in os.walk(directory):
        for file in files:
            if not file.endswith(".srt"):
                continue
            
            # --- Date Check ---
            process_this_file = True # Default to processing the file
            if cutoff_date:
                match = FILENAME_PATTERN.match(file)
                if match:
                    # Filename matches, so we *can* check its date
                    try:
                        date_str = match.group(1) # 'YYYYMMDD'
                        file_date_obj = datetime.strptime(date_str, "%Y%m%d").date()
                        
                        if file_date_obj < cutoff_date:
                            # File is too old, skip it
                            skipped_date += 1
                            process_this_file = False 
                    except ValueError:
                        # Filename matched but date was invalid, process it anyway
                        pass 
                # else:
                #   Filename does not match pattern.
                #   We can't check its date, so we'll process it.
                #   (process_this_file remains True)
            # --- End Date Check ---
            
            if process_this_file:
                srt_files_to_process.append(os.path.join(root, file))

    if not srt_files_to_process:
        print(f"No .srt files found in '{directory}' that match the criteria.")
        if cutoff_date:
            print(f"(Skipped {skipped_date} files due to date)")
        return

    print(f"Found {len(srt_files_to_process)} .srt files to process.")
    if cutoff_date:
        print(f"(Skipped {skipped_date} files (too old))")

    for file_path in tqdm(srt_files_to_process, unit="file"):
        try:
            # Open with 'r+' to read and write
            with open(file_path, "r+", encoding="utf-8") as f:
                original_content = f.read()
                content = original_content

                # Apply all replacements
                for old_word, new_word in word_map.items():
                    content = content.replace(
                        old_word.lower(), new_word.lower()
                    )
                    content = content.replace(
                        old_word.capitalize(), new_word.capitalize()
                    )
                
                if content != original_content:
                    f.seek(0)       # Go to the beginning of the file
                    f.write(content)
                    f.truncate()    # Remove leftover content if new file is shorter
        
        except Exception as e:
            # Use tqdm.write to print errors without messing up the progress bar
            tqdm.write(f"Error processing {file_path}: {e}")

if __name__ == "__main__":
    if not os.path.isdir(directory):
        print(f"Error: Directory not found: '{directory}'")
    else:
        # Ask for date and calculate cutoff
        days_to_fix = get_day_limit()
        cutoff_date = None
        
        if days_to_fix:
            today = datetime.now().date()
            cutoff_date = today - timedelta(days=days_to_fix)
            print(f"\nStarting fix: Only files from the last {days_to_fix} days.")
            print(f"Processing files dated on or after: {cutoff_date.strftime('%Y-%m-%d')}")
        else:
            print("\nStarting fix: Processing ALL transcripts.")

        replace_words_in_srt_files(word_map, directory, cutoff_date)
        print("\nReplacement complete.")
