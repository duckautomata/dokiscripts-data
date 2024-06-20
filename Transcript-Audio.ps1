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
        --sleep-interval 30 `
        $URL
}

function Get-Ragtag {
    param (
        [string]$FilePath
    )

    foreach ($line in Get-Content $FilePath) {
        $match = $line | Select-String -Pattern '(?<=\?v=).*'
        if ($match) {
            .\yt-dlp.exe `
                --ignore-errors `
                --write-thumbnail `
                -f 'ba' `
                -o "Transcript/SelenTatsuki/Stream - %(title)s - [$($match.Matches.Value)].%(ext)s" `
                --windows-filenames `
                --sleep-requests 1 `
                --sleep-interval 30 `
                "https://archive.ragtag.moe/watch?v=$($match.Matches.Value)"
        } else {
            Write-Error "Error could not get video tag from string '$line'."
        }
    }
}

# Get-Audio -Channel "Dokibird" -URL "https://www.youtube.com/playlist?list=PL14fhSPKPOywnhNV76e11OWVyYgRpmTs9" -Type "Members"
Get-Audio -Channel "Dokibird" -URL "https://www.youtube.com/Dokibird/videos" -Type "Video"
Get-Audio -Channel "Dokibird" -URL "https://www.youtube.com/@DokibirdVODs/videos" -Type "Twitch"
Get-Audio -Channel "Dokibird" -URL "https://www.youtube.com/Dokibird/streams" -Type "Stream"
# Get-Ragtag -FilePath .\selen_rtarchive.txt
