# Prompt for confirmation
$confirmation = Read-Host "Are you sure you want to delete all audio files in Transcript? (Y/N)"

if ($confirmation -eq "Y" -or $confirmation -eq "y") {
    $i = 0
    Get-ChildItem -Path ".\Transcript" -Include *.webm, *.m4a, *.mp3, *.mp4 -File -Recurse | ForEach-Object {
        $i += 1
        $_.Delete()
    }
    Write-Host "Deleted $i audio files."
} else {
    Write-Host "Operation canceled."
}
