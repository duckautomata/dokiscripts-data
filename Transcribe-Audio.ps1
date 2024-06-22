$folderpath = Read-Host "Enter folder containing audio"

function Green
{
    process { Write-Host $_ -ForegroundColor Green }
}

function Red
{
    process { Write-Host $_ -ForegroundColor Red }
}

$files = Get-ChildItem -Path "$folderpath\*" -Include *.webm, *.m4a, *.mp3, *.mp4
$i = 0
foreach ($file in $files) {
    $i += 1
    if (Test-Path -LiteralPath "$($file.DirectoryName)\$($file.BaseName).srt") {
        Write-Output $file.FullName | Green
    } else {
        Write-Output $file.FullName | Red
        Write-Output "Transcripting $i out of $($files.Count)"
        .\faster-whisper-xxl.exe $file.FullName -l English -m large --sentence -o source --beam_size=1 -pp
    }
}