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

    # If we are downloading from twitch, we don't want to save the thumbnail
    if ($URL.ToLower().Contains("twitch.tv")) {
        Write-Host "Downloading from twitch, not including thumbnail"
        .\yt-dlp.exe `
            --download-archive yt-dlp-archive-transcript.txt `
            --ignore-errors `
            --match-filter !is_live `
            -f 'ba' `
            -o "Transcript/$Channel/%(upload_date)s - $Type - %(title)s - [%(id)s].%(ext)s" `
            --windows-filenames `
            --sleep-requests 1 `
            --sleep-interval 15 `
            $URL
    } else {
        .\yt-dlp.exe `
            --download-archive yt-dlp-archive-transcript.txt `
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
}

.\yt-dlp.exe -U
Get-Audio -Channel "Dokibird" -URL "https://www.youtube.com/Dokibird/membership" -Type "Members"
Get-Audio -Channel "Dokibird" -URL "https://www.youtube.com/Dokibird/videos" -Type "Video"
Get-Audio -Channel "Dokibird" -URL "https://www.youtube.com/@DokibirdVODs/videos" -Type "TwitchVod"
Get-Audio -Channel "Dokibird" -URL "https://www.twitch.tv/dokibird/videos?filter=archives&sort=time" -Type "Twitch"
Get-Audio -Channel "Dokibird" -URL "https://www.youtube.com/Dokibird/streams" -Type "Stream"
Get-Audio -Channel "MintFantome" -URL "https://www.youtube.com/@mintfantome/membership" -Type "Members"
Get-Audio -Channel "MintFantome" -URL "https://www.youtube.com/@mintfantome/videos" -Type "Video"
Get-Audio -Channel "MintFantome" -URL "https://www.youtube.com/@mintfantome/streams" -Type "Stream"
# Get-Audio -Channel "Dokibird" -URL "https://www.twitch.tv/videos/2240830475" -Type "External"
