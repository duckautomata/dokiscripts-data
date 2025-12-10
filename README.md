# dokiscripts-data
Transcripts for Doki and other vTuber streams. All located in one place for easy reverse searching.

## Overview

_System_

- **[Archived Transcript System](#archived-transcript-system)**
- **[Guide](#guide)**

_Info_

- **[Best Way to Search](#best-way-to-search)**
- **[Types](#types)**
- **[Why this over YouTube's built-in transcripts?](#why-this-over-youtubes-built-in-transcripts)**
- 
_Transcript Collection_
- **[Environment](#environment)**
- **[Prep](#prep)**
- **[Updating Transcripts Process](#updating-transcripts-process)**
- **[Cleanup](#cleanup)**
- **[Uploading to Archive](#uploading-to-archive)**
- **[Verifyinbg Local Transcripts](#verifyinbg-local-transcripts)**

## System

### Archived Transcript System

Archived Transcript is a system that contains three programs:

- Data: [dokiscripts-data](https://github.com/duckautomata/dokiscripts-data)
- Server: [archived-transcript-server](https://github.com/duckautomata/archived-transcript-server)
- Client: [archived-transcript](https://github.com/duckautomata/archived-transcript)

All three programs work together to transcribe all streams/videos/content and allows anyone to search through and view them.

- Data (this) will transcribe the content, stores the `.srt` files in git for safekeeping, and uploads the `.srt` files to the server. All of these steps are manually triggered.
- Server will receive `.srt` files from Data and store them into a database. Upon request from the Client, it will search through the data base and return the requested data.
- Client is the UI that renders the transcript for us to use.

## Info

### Best Way to Search
- Use the website that searches these transcripts: https://duckautomata.github.io/archived-transcript/.
- Search through this repo directly.

### Types
There are 6 types of content
1. Video
    > Videos uploaded to youtube
2. Stream
    > Non-members Livestreams
3. Members
    > Members only content. This should be blocked by gitignore so none of it should end up here.
4. Twitch
    > Streams directly from Twitch
5. TwitchVod
    > Twitch streams that were uploaded to YouTube
6. External
    > Anything that is not on the main channel. E.g. appearing on someone else's stream.

For these channels
- Dokibird
- Maid Mint

### Why this over YouTube's built-in transcripts?
Several reasons why I created this archive.
1. YouTube transcripts censor curse words. Meaning that you can't reverse search something that has the word `fuck` in it.
2. YouTube transcripts are only accurate if one person is talking in a clear understandable way. If two people are talking, or if there is gunfire in the background (for example, any Apex stream). Then the transcripts are not that accurate.
3. YouTube transcripts only work for one language. If people are talking in a different language, then they are worthless. This, on the other hand, can handle any language that is in the model. Even if two people are talking in a different language at the same time, it should be able to pick out both of them correctly.

## Transcript Collection

### Environment
This is built to work with Windows. Mac and Linux is not guaranteed to work. Especially because I use the Windows standalone version of faster-whisper.
Faster-whisper also uses CUDA to compute the transcripts. So an Nvidia-based GPU is needed.

### Prep
Tools you need to download and put into the root dir.
- [yt-dlp](https://github.com/yt-dlp/yt-dlp)
- [ffmpeg](https://github.com/FFmpeg/FFmpeg)
- [faster-whisper](https://github.com/Purfview/whisper-standalone-win)
- [Python](https://www.python.org/downloads/)

### Updating Transcripts Process
1. Create a new branch and checkout said branch.
2. Get the latest audio by running `python .\scripts\download_audio.py`
3. Process all new audio by running `python .\scripts\transcribe_audio.py`
    - Enter the folder you want to transcribe. For Doki, that would be `.\Transcript\Dokibird\`
    - Or enter nothing to run for every folder
4. Commit and push changes to your branch.
5. Open a pull request. Ping me to get it accepted and merged.

### Cleanup
After the transcripts are created. You can remove all audio files by running the script `python .\scripts\cleanup_audio.py`

### Uploading to Archive
To upload any new transcripts to the Archive, you can do so by
1. creating `config.yaml` from the example and enter in the correct configurations
2. run the script `python .\scripts\upload_transcripts.py`

### Verifyinbg Local Transcripts
In the event you want to see what srt transcripts you are missing locally, you can do so by running `python .\scripts\verify_transcript.py`
