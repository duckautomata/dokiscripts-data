#!/usr/bin/env python3

import os
import sys
from colorama import init, Fore

# --- Configuration ---
ID_ARCHIVE = "yt-dlp-archive-transcript.txt"
FOLDER_PATH = "Transcript"
MEDIA_EXTENSIONS = ('.webm', '.m4a', '.mp3', '.mp4', '.mkv')
# --- End Configuration ---


def find_srt_file(root_path, video_id):
    """
    Recursively scans for an SRT file matching the video ID.
    Returns:
        (str, bool) or None: A tuple of (filename, is_member) if found, else None.
    """
    id_pattern = f"[{video_id}]"
    for root, _, files in os.walk(root_path):
        for file in files:
            # Check for ID pattern and .srt extension
            if id_pattern in file and file.endswith(".srt"):
                is_member = "- Members -" in file
                return (file, is_member)
    return None

def find_media_file(root_path, video_id):
    """
    Recursively scans for a media file matching the video ID.
    Returns:
        str or None: The filename if found, else None.
    """
    id_pattern = f"[{video_id}]"
    for root, _, files in os.walk(root_path):
        for file in files:
            # Check for ID pattern and a media extension
            if id_pattern in file and file.endswith(MEDIA_EXTENSIONS):
                return file
    return None

def main():
    # Initialize colorama to auto-reset colors after each print
    init(autoreset=True)

    # --- 1. Check if files and folders exist ---
    if not os.path.isfile(ID_ARCHIVE):
        print(Fore.RED + f"Error: Archive file not found at '{ID_ARCHIVE}'")
        sys.exit(1)
        
    if not os.path.isdir(FOLDER_PATH):
        print(Fore.RED + f"Error: Transcript folder not found at '{FOLDER_PATH}'")
        sys.exit(1)
        
    print(f"Checking archive '{ID_ARCHIVE}' against folder '{FOLDER_PATH}'...")
    
    # --- 2. Read archive file and process each line ---
    try:
        with open(ID_ARCHIVE, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue # Skip empty lines

                # Line is "place id", e.g., "youtube 12345abc"
                parts = line.split()
                if len(parts) < 2:
                    print(Fore.MAGENTA + f"Skipping malformed line: '{line}'")
                    continue
                
                video_id = parts[1] # Get the ID
                
                # --- 3. Replicate PowerShell logic ---
                
                # First, try to find an SRT file
                srt_result = find_srt_file(FOLDER_PATH, video_id)
                
                if srt_result:
                    # An SRT file was found
                    file_name, is_member = srt_result
                    if is_member:
                        print(Fore.YELLOW + f"id [{video_id}] exists as members only")
                    else:
                        # This was commented out in the original PS1
                        # print(Fore.GREEN + f"id [{video_id}] exists")
                        pass 
                
                else:
                    # No SRT file, so now check for a media file
                    if find_media_file(FOLDER_PATH, video_id):
                        print(Fore.BLUE + f"Transcript not yet created for id [{video_id}]")
                    else:
                        print(Fore.RED + f"No files containing id [{video_id}] found.")

    except FileNotFoundError:
        # This check is technically redundant due to the os.path.isfile
        # but it's good practice.
        print(Fore.RED + f"Error: Failed to open '{ID_ARCHIVE}'")
        sys.exit(1)
    except Exception as e:
        print(Fore.RED + f"An unexpected error occurred: {e}")

    print("\nCheck complete.")

if __name__ == "__main__":
    main()
