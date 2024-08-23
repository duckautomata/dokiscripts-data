## dokiscripts-data
Transcripts for Doki and other vTuber streams. All located in one place for easy reverse searching.

### Best Way to Reverse Search
- Clone the repo locally and use something like vscode to search through every file in the folder.
    - to update when new transcripts are added, all you would need to do is run git pull from master.
- Use GitHubs built in search. Though this sucks half the time so good luck.

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

### Environment
This is built to work with Windows. Mac and Linux is not guaranteed to work. Especially because I use the Windows standalone version of faster-whisper.
Faster-whisper also uses CUDA to compute the transcripts. So an Nvidia-based GPU is needed.

### Prep
Tools you need to download and put into the root dir.
- [yt-dlp](https://github.com/yt-dlp/yt-dlp)
- [ffmpeg](https://github.com/FFmpeg/FFmpeg)
- [faster-whisper](https://github.com/Purfview/whisper-standalone-win)
- [PowerShell](https://github.com/PowerShell/PowerShell)

### Updating Transcripts Process
1. Create a new branch and checkout said branch.
2. Get the latest audio by running `./Download-Audio.ps1`
3. Process all new audio by running `./Transcribe-Audio.ps1`
    - Enter the folder you want to transcribe. For Doki, that would be `.\Transcript\Dokibird\`
4. Commit and push changes to your branch.
5. Open a pull request. Ping me to get it accepted and merged.

### Cleanup
After the transcripts are created. You can remove all audio files by running the script `.\Cleanup-Audio.ps1`
