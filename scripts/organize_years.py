import os
import shutil
import sys
from pathlib import Path

# Ensure UTF-8 output for terminal
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

def organize_transcripts(dry_run=True):
    transcript_base = Path("Transcript")
    
    if not transcript_base.exists():
        print(f"Error: {transcript_base} directory not found.")
        return

    # Subdirectories like Dokibird, MintFantome
    for item in transcript_base.iterdir():
        if not item.is_dir():
            continue
            
        print(f"Processing directory: {item}")
        
        # Files in the subdirectory
        for entry in item.iterdir():
            if not entry.is_file():
                continue
            
            filename = entry.name
            # Expected format: YYYYMMDD - ...
            if len(filename) >= 4 and filename[:4].isdigit():
                year = int(filename[:4])
                
                if year <= 2024:
                    target_folder_name = "2024"
                elif year == 2025:
                    target_folder_name = "2025"
                else:
                    # Skip 2026 and above
                    target_folder_name = ""
                
                if target_folder_name:
                    target_dir = item / target_folder_name
                    
                    if dry_run:
                        print(f"  [DRY RUN] Would move {filename} to {target_folder_name}/")
                    else:
                        if not target_dir.exists():
                            target_dir.mkdir(parents=True, exist_ok=True)
                        
                        try:
                            shutil.move(str(entry), str(target_dir / filename))
                            print(f"  Moved {filename} to {target_folder_name}/")
                        except Exception as e:
                            print(f"  Error moving {filename}: {e}")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Organize transcript files into year folders.")
    parser.add_argument("--execute", action="store_true", help="Actually move the files (default is dry run).")
    args = parser.parse_args()
    
    organize_transcripts(dry_run=not args.execute)
    print("Dry run complete. To execute, run with --execute.")