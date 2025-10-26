#!/usr/bin/env python3

import os
import sys
import subprocess
from colorama import init, Fore

# --- Configuration ---

# The command to run whisper.
# This script will first check the local folder (like .\[cmd])
# and if not found, will assume it's in the system's PATH.
WHISPER_EXECUTABLE = "faster-whisper-xxl.exe" if sys.platform == "win32" else "faster-whisper-xxl"

# The default directory to scan
DEFAULT_PATH = "Transcript"

# File types to look for
MEDIA_EXTENSIONS = ('.webm', '.m4a', '.mp3', '.mp4', '.mkv')

# --- End Configuration ---

def find_files_to_process(scan_path):
    """Recursively finds all media files in the given path."""
    files_to_process = []
    print(f"Scanning for media files in: {scan_path}...")
    for root, dirs, files in os.walk(scan_path):
        for file in files:
            if file.endswith(MEDIA_EXTENSIONS):
                files_to_process.append(os.path.join(root, file))
    return files_to_process

def get_whisper_command():
    """Finds the whisper executable, preferring a local one."""
    local_cmd = os.path.join(".", WHISPER_EXECUTABLE)
    
    if os.path.exists(local_cmd):
        print(f"Found local executable: {local_cmd}")
        return local_cmd
    else:
        print(f"Using PATH to find executable: {WHISPER_EXECUTABLE}")
        return WHISPER_EXECUTABLE

def get_scan_path():
    """Asks the user for a path, falling back to the default."""
    # Use os.path.normpath to fix any / or \ issues
    default_normalized = os.path.normpath(DEFAULT_PATH)
    
    try:
        user_input = input(f"Enter folder containing audio [{default_normalized}]: ").strip()
    except KeyboardInterrupt:
        print("\nOperation canceled.")
        sys.exit(0)

    if user_input and os.path.isdir(user_input):
        return os.path.normpath(user_input)
    elif user_input:
        print(f"'{user_input}' is not a valid directory. Using default.")
    else:
        print("No input provided. Using default.")
        
    return default_normalized

def main():
    # Initialize colorama to auto-reset colors after each print
    init(autoreset=True)

    # 1. Get the path to scan
    path_to_scan = get_scan_path()
    if not os.path.isdir(path_to_scan):
        print(Fore.RED + f"Error: Base directory '{path_to_scan}' not found.")
        sys.exit(1)

    # 2. Find the whisper command
    whisper_cmd_path = get_whisper_command()
    try:
        # Run a quick --help command to ensure it's found BEFORE starting the loop
        # Added encoding='utf-8' to fix UnicodeDecodeError on Windows
        subprocess.run(
            [whisper_cmd_path, "--help"],
            capture_output=True,
            check=True,
            text=True,
            encoding='utf-8'
        )
    except FileNotFoundError:
        print(Fore.RED + f"Error: Whisper command '{WHISPER_EXECUTABLE}' not found.")
        print(Fore.RED + "Please make sure it's in your system PATH or in the same folder as this script.")
        sys.exit(1)
    except subprocess.CalledProcessError:
        # This is fine, it just means the command might not be a whisper command
        # or it doesn't like --help. We'll proceed.
        print(Fore.YELLOW + "Could not verify whisper command, but proceeding...")
    except Exception as e:
        print(Fore.RED + f"An unexpected error occurred trying to find whisper: {e}")
        sys.exit(1)


    # 3. Find all media files
    files = find_files_to_process(path_to_scan)
    total_files = len(files)

    if total_files == 0:
        print(Fore.YELLOW + f"No media files found in '{path_to_scan}'.")
        sys.exit(0)
        
    print(f"Found {total_files} files to check.\n")

    # 4. Loop through and process each file
    for i, file_path in enumerate(files):
        # os.path.splitext creates ('path/to/file/basename', '.ext')
        base_name, _ = os.path.splitext(file_path)
        srt_path = base_name + ".srt"

        if os.path.exists(srt_path):
            # File already has a transcript, print in green
            print(Fore.GREEN + file_path)
        else:
            # File needs transcribing, print in red
            print(Fore.RED + file_path)
            print(f"Transcribing {i + 1} out of {total_files}")
            
            # Build the command arguments
            command_args = [
                whisper_cmd_path,
                file_path,
                "-l", "English",
                "--compute_type", "float32",
                "-m", "distil-large-v3.5",
                "--sentence",
                "-o", "source",
                "-pp",
                "--beep_off"
            ]
            
            # Uncomment the line below to run the "translate" task instead
            # command_args.extend(["--task", "translate"])

            try:
                # Run the transcription command
                subprocess.run(command_args, check=False)
            except subprocess.CalledProcessError as e:
                print(Fore.RED + f"Error running whisper on {file_path}: {e}")
            except Exception as e:
                print(Fore.RED + f"An unexpected error occurred: {e}")


if __name__ == "__main__":
    main()