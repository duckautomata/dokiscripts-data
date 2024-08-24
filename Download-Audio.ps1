# Order
#  - members
#  - videos
#  - twitch vods
#  - stream vods
#  - anything else

function Get-Audio {
    param (
        [string]$URL,
        [string]$Type,
        [string]$Channel
    )

    .\yt-dlp.exe `
        --download-archive yt-dlp-archive-transcript.txt `
        --cookies-from-browser firefox `
        --ignore-errors `
        --match-filter !is_live `
        --write-thumbnail `
        -f 'ba' `
        -o "Transcript/$Channel/%(upload_date)s - $Type - %(title)s - [%(id)s].%(ext)s" `
        --windows-filenames `
        --sleep-requests 1 `
        --sleep-interval 15 `
        $URL
}

function Get-TwitchAudio {
    param (
        [string]$URL,
        [string]$Type,
        [string]$Channel
    )

    .\yt-dlp.exe `
        --download-archive yt-dlp-archive-transcript.txt `
        --cookies-from-browser firefox `
        --ignore-errors `
        --match-filter !is_live `
        -f 'ba' `
        -o "Transcript/$Channel/%(upload_date)s - $Type - %(title)s - [%(id)s].%(ext)s" `
        --windows-filenames `
        --sleep-requests 1 `
        --sleep-interval 15 `
        $URL
}

.\yt-dlp.exe -U
Get-Audio -Channel "Dokibird" -URL "https://www.youtube.com/playlist?list=PL14fhSPKPOywnhNV76e11OWVyYgRpmTs9" -Type "Members"
Get-Audio -Channel "Dokibird" -URL "https://www.youtube.com/Dokibird/videos" -Type "Video"
Get-Audio -Channel "Dokibird" -URL "https://www.youtube.com/@DokibirdVODs/videos" -Type "TwitchVod"
Get-TwitchAudio -Channel "Dokibird" -URL "https://www.twitch.tv/dokibird/videos?filter=archives&sort=time" -Type "Twitch"
Get-Audio -Channel "Dokibird" -URL "https://www.youtube.com/Dokibird/streams" -Type "Stream"
Get-Audio -Channel "MintFantome" -URL "https://www.youtube.com/playlist?list=PLONZBVo0tPY9aPMNquXbKmmBY-czd6m-x" -Type "Members"
Get-Audio -Channel "MintFantome" -URL "https://www.youtube.com/@mintfantome/videos" -Type "Video"
Get-Audio -Channel "MintFantome" -URL "https://www.youtube.com/@mintfantome/streams" -Type "Stream"
# Get-Audio -Channel "Dokibird" -URL "https://www.youtube.com/live/WNiCnSHK3Gc" -Type "External"
