# Order
#  - members
#  - videos
#  - twitch vods
#  - stream vods

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

# Get-Audio -Channel "Dokibird" -URL "https://www.youtube.com/playlist?list=PL14fhSPKPOywnhNV76e11OWVyYgRpmTs9" -Type "Members"
Get-Audio -Channel "Dokibird" -URL "https://www.youtube.com/Dokibird/videos" -Type "Video"
Get-Audio -Channel "Dokibird" -URL "https://www.youtube.com/@DokibirdVODs/videos" -Type "Twitch"
Get-Audio -Channel "Dokibird" -URL "https://www.youtube.com/Dokibird/streams" -Type "Stream"
# Get-Audio -Channel "Dokibird" -URL "https://www.youtube.com/live/WNiCnSHK3Gc" -Type "External"
