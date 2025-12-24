import os
import re
import sys
from pathlib import Path

# Ensure UTF-8 output for terminal
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

def is_multi_line_srt(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # SRT blocks are usually separated by one or more blank lines
        blocks = re.split(r'\n\s*\n', content.strip())
        
        for block in blocks:
            lines = [l for l in block.split('\n') if l.strip()]
            if len(lines) < 2:
                continue
            
            # Line 0 is usually index, Line 1 is timestamp
            # We check if there are more than 2 lines (index, timestamp, then text)
            # Or specifically, more than one line of text.
            # Entry usually:
            # 1
            # 00:00:00,000 --> 00:00:01,000
            # Text line 1
            # Text line 2
            
            # Find the timestamp line
            timestamp_idx = -1
            for i, line in enumerate(lines):
                if "-->" in line:
                    timestamp_idx = i
                    break
            
            if timestamp_idx != -1:
                # Count lines after timestamp
                text_lines = lines[timestamp_idx + 1:]
                if len(text_lines) > 1:
                    return True
    except Exception as e:
        # Skip files that can't be read (e.g. encoding issues, though we try utf-8)
        pass
    return False

def main():
    transcript_dir = Path("Transcript")
    
    if not transcript_dir.exists():
        print(f"Error: {transcript_dir} not found.")
        return

    print(f"Searching for the first multi-line .srt file in {transcript_dir}...")
    
    for root, dirs, files in os.walk(transcript_dir):
        for file in files:
            if file.endswith(".srt"):
                full_path = Path(root) / file
                if is_multi_line_srt(full_path):
                    print(f"\nMatch found: {full_path}")
                    return

    print("\nNo multi-line .srt files found.")

if __name__ == "__main__":
    main()
