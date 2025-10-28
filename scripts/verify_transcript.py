import os
import sys

# --- Configuration ---
TRANSCRIPT_DIR = 'Transcript'
MEMBERS_FILE = 'yt-dlp-archive-members.txt'
REGULAR_FILE = 'yt-dlp-archive-regular.txt'
# --- End Configuration ---

# ANSI color codes for terminal output
class bcolors:
    RED = '\033[91m'
    GREEN = '\033[92m'
    ENDC = '\033[0m'

def build_srt_map(directory):
    """
    Recursively scans the directory and builds a map of
    video IDs to their stream_type. This is our "ground truth".
    """
    print(f"Scanning '{directory}' to build verification map...")
    srt_map = {} # key: video_id, value: stream_type
    
    if not os.path.isdir(directory):
        print(f"{bcolors.RED}Error: Transcript directory not found at: {directory}{bcolors.ENDC}", file=sys.stderr)
        return None

    for root, dirs, files in os.walk(directory):
        for filename in files:
            if not filename.endswith('.srt'):
                continue
                
            parts = filename.split(' - ')
            if len(parts) >= 4:
                try:
                    stream_type = parts[1].strip()
                    id_part = parts[-1] # This should be "[{id}].srt"
                    
                    if id_part.startswith('[') and id_part.endswith('].srt'):
                        video_id = id_part[1:-5]
                        if video_id in srt_map and srt_map[video_id] != stream_type:
                            print(f"Warning: Duplicate ID '{video_id}' found with different StreamTypes. "
                                  f"This may cause verification errors.")
                        srt_map[video_id] = stream_type
                except Exception:
                    # Ignore parsing errors, same as the first script
                    pass
            
    print(f"Scan complete. Found {len(srt_map)} unique .srt files to check against.")
    return srt_map

def extract_id_from_line(line):
    """Helper to get the last word (the ID) from an archive line."""
    try:
        return line.strip().split()[-1]
    except IndexError:
        #Likely a blank line
        return None

def main():
    srt_map = build_srt_map(TRANSCRIPT_DIR)
    if srt_map is None:
        sys.exit(1) # Exit if the transcript directory wasn't found

    errors_found = False
    
    # --- 1. Check Members File ---
    # It should ONLY contain IDs where srt_map[id] == "Members"
    print(f"\nVerifying {MEMBERS_FILE}...")
    try:
        with open(MEMBERS_FILE, 'r', encoding='utf-8') as f:
            for i, line in enumerate(f):
                video_id = extract_id_from_line(line)
                if not video_id:
                    continue
                
                if video_id in srt_map:
                    stream_type = srt_map[video_id]
                    if stream_type != "Members":
                        print(f"{bcolors.RED}ERROR:{bcolors.ENDC} Line {i+1}: ID '{video_id}' is in {MEMBERS_FILE} "
                              f"but its type is '{stream_type}'.")
                        errors_found = True
                else:
                    # If an ID is in the members file, it MUST have a matching .srt
                    # The first script defaults non-found to 'regular'
                    print(f"{bcolors.RED}ERROR:{bcolors.ENDC} Line {i+1}: ID '{video_id}' is in {MEMBERS_FILE} "
                          f"but has no matching .srt file.")
                    errors_found = True

    except FileNotFoundError:
        print(f"Warning: {MEMBERS_FILE} not found. Skipping its verification.")

    # --- 2. Check Regular File ---
    # It should NOT contain any IDs where srt_map[id] == "Members"
    print(f"\nVerifying {REGULAR_FILE}...")
    try:
        with open(REGULAR_FILE, 'r', encoding='utf-8') as f:
            for i, line in enumerate(f):
                video_id = extract_id_from_line(line)
                if not video_id:
                    continue
                
                if video_id in srt_map:
                    stream_type = srt_map[video_id]
                    if stream_type == "Members":
                        print(f"{bcolors.RED}ERROR:{bcolors.ENDC} Line {i+1}: ID '{video_id}' is in {REGULAR_FILE} "
                              f"but it is a 'Members' video.")
                        errors_found = True
                # else:
                    # If video_id is not in srt_map, it's correct to be in regular.
                    # No error.
                    
    except FileNotFoundError:
        print(f"Warning: {REGULAR_FILE} not found. Skipping its verification.")

    # --- 3. Final Report ---
    print("\n--- Verification Complete ---")
    if errors_found:
        print(f"{bcolors.RED}❌ VERIFICATION FAILED: Errors were found in your archive files.{bcolors.ENDC}")
    else:
        print(f"{bcolors.GREEN}✅ SUCCESS: All files are sorted correctly according to the .srt map.{bcolors.ENDC}")

if __name__ == "__main__":
    main()
