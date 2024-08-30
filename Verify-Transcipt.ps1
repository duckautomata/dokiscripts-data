
$idArchive = ".\yt-dlp-archive-transcript.txt"
$folderPath = ".\Transcript"

# Read the list of ids from the archive
$ids = Get-Content -Path $idArchive
foreach ($line in $ids) {
    # id is in the format "place id". We only want the id
    $lineParts = $line -split ' '
    $id = $lineParts[1]

    $files = Get-ChildItem -Path $folderPath -Filter "*[$id]*.srt" -File -Recurse
    if ($files) {
        if ($files.BaseName -like "*- Members -*") {
            Write-Host "id [$id] exists as members only" -ForegroundColor Yellow
        } else {
            # Write-Host "id [$id] exists" -ForegroundColor Green
        }
    } else {
        if (Get-ChildItem -Path $folderPath -Filter "*[$id]*" -File -Recurse | Where-Object { $_.Name -match "\.(webm|m4a|mp3|mp4|mkv)$" }) {
            Write-Host "Transcript not yet created for id [$id]" -ForegroundColor Blue
        } else {
            Write-Host "No files containing id [$id] found." -ForegroundColor Red
        }
    }
}
