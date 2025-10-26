#!/usr/bin/env python3

import os
import sys

def clear_media_files():
    """
    Finds and deletes specific media files from the 'Transcript' directory
    after user confirmation.
    """
    
    base_dir = "Transcript"
    # List of file extensions to delete
    media_extensions = ('.webm', '.m4a', '.mp3', '.mp4', '.mkv')

    if not os.path.isdir(base_dir):
        print(f"Error: Directory '{base_dir}' not found.")
        print("Please run this script from the correct location.")
        sys.exit(1)

    try:
        confirmation = input(
            f"Are you sure you want to delete all media files in '{base_dir}'? (Y/N): "
        ).strip().lower()
    except KeyboardInterrupt:
        print("\nOperation canceled by user.")
        sys.exit(0)

    if confirmation == 'y':
        print("Scanning and deleting files...")
        deleted_count = 0
        
        # os.walk recurses through the directory tree
        for root, dirs, files in os.walk(base_dir):
            for file in files:
                # Check if the file ends with any of the target extensions
                if file.endswith(media_extensions):
                    full_path = os.path.join(root, file)
                    
                    try:
                        os.remove(full_path)
                        deleted_count += 1
                        # Optional: print every file deleted
                        # print(f"Deleted: {full_path}")
                    except OSError as e:
                        print(f"Error: Could not delete {full_path}: {e}")
        
        print(f"Deleted {deleted_count} media files.")
        
    else:
        print("Operation canceled.")

if __name__ == "__main__":
    clear_media_files()