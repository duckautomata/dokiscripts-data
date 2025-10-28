#!/usr/bin/env python3

import subprocess
import sys
import os

# --- Configuration ---

# This is the command to run.
# Assumes 'yt-dlp' is in your system's PATH.
# On Windows, this will correctly find 'yt-dlp.exe'.
YT_DLP_CMD = "yt-dlp"

# The root folder for transcripts
BASE_DIR = "Transcript"

# --- End Configuration ---


def get_audio(url, download_type, channel):
    """
    Calls yt-dlp to download audio for a given URL,
    matching the settings from the PowerShell script.

    Args:
        url (str): The URL to download from.
        download_type (str): The type of content (e.g., "Members", "Video").
        channel (str): The streamer's name, used for the folder.
    """

    # 1. Create the output path template.
    output_template = (
        f"{BASE_DIR}/{channel}/%(upload_date)s - {download_type} - "
        f"%(title)s - [%(id)s].%(ext)s"
    )

    # 2. Build the base command
    command = [YT_DLP_CMD]

    # 3. Add conditional arguments based on download_type
    if download_type == "Members":
        print(f"Downloading (Members): {channel}")
        command.extend(
            [
                "--download-archive", "yt-dlp-archive-members.txt",
                "--cookies-from-browser", "firefox",
            ]
        )
    else:
        print(f"Downloading (Regular): {channel} - {download_type}")
        command.extend(["--download-archive", "yt-dlp-archive-regular.txt"])

    # 4. Add common arguments
    command.extend(
        [
            "--ignore-errors",
            "--match-filter",
            "!is_live",
            "-f",
            "ba",
            "-o",
            output_template,
            "--windows-filenames",
            "--sleep-requests",
            "1",
            "--sleep-interval",
            "15",
        ]
    )

    # 5. Conditionally add/remove arguments based on URL
    if "twitch.tv" in url.lower():
        print("-> Twitch URL detected, skipping thumbnail.")
    else:
        print("-> YouTube URL detected, adding thumbnail.")
        command.append("--write-thumbnail")

    # 6. Add the URL as the final argument
    command.append(url)

    # 7. Run the command
    try:
        subprocess.run(command)

    except FileNotFoundError:
        # This error happens if 'yt-dlp' isn't installed or not in PATH
        print(f"\n[Error] '{YT_DLP_CMD}' command not found.")
        print("Please ensure yt-dlp is installed and in your system's PATH.")
        sys.exit(1)  # Exit the script
    except Exception as e:
        # Catch other potential errors
        print(f"\nAn error occurred while processing {url}: {e}")


def main():
    """
    Main function to update yt-dlp and run all downloads.
    """

    # 1. Update yt-dlp (equiv. of .\yt-dlp.exe -U)
    print("Attempting to update yt-dlp...")
    try:
        # check=True will raise an error if the update fails
        subprocess.run([YT_DLP_CMD, "-U"], check=True)
    except FileNotFoundError:
        print(f"\n[Error] '{YT_DLP_CMD}' command not found.")
        print("Please ensure yt-dlp is installed and in your system's PATH.")
        sys.exit(1)  # Exit if yt-dlp isn't found
    except subprocess.CalledProcessError as e:
        # This error means the update command failed
        print(f"Failed to update yt-dlp (command failed): {e}")
        # We can continue, but it's good to notify the user
    except Exception as e:
        print(f"An unknown error occurred during update: {e}")

    print("\n--- Starting Downloads ---")

    # 2. Run the downloads in the specified order
    # Order:
    #  - members
    #  - videos
    #  - twitch vods
    #  - stream vods
    #  - anything else

    # --- Dokibird ---
    get_audio(
        url="https://www.youtube.com/Dokibird/membership",
        download_type="Members",
        channel="Dokibird",
    )
    get_audio(
        url="https://www.youtube.com/Dokibird/videos",
        download_type="Video",
        channel="Dokibird",
    )
    get_audio(
        url="https://www.youtube.com/@DokibirdVODs/videos",
        download_type="TwitchVod",
        channel="Dokibird",
    )
    get_audio(
        url="https.www.twitch.tv/dokibird/videos?filter=archives&sort=time",
        download_type="Twitch",
        channel="Dokibird",
    )
    get_audio(
        url="https://www.youtube.com/Dokibird/streams",
        download_type="Stream",
        channel="Dokibird",
    )

    # --- MintFantome ---
    get_audio(
        url="https://www.youtube.com/@mintfantome/membership",
        download_type="Members",
        channel="MintFantome",
    )
    get_audio(
        url="https://www.youtube.com/@mintfantome/videos",
        download_type="Video",
        channel="MintFantome",
    )
    get_audio(
        url="https://www.youtube.com/@mintfantome/streams",
        download_type="Stream",
        channel="MintFantome",
    )

    # --- Commented out call ---
    # get_audio(
    #     url="https.www.twitch.tv/videos/2240830475",
    #     download_type="External",
    #     channel="Dokibird"
    # )

    print("\n--- Download process finished. ---")


if __name__ == "__main__":
    # Ensure the base 'Transcript' directory exists
    os.makedirs(BASE_DIR, exist_ok=True)
    main()
