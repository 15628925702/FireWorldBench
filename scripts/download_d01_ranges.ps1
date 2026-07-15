param(
    [string]$Root = (Get-Location).Path,
    [int]$MaxConcurrent = 8,
    [int]$ChunkSize = 1048576
)

$treePath = Join-Path $Root "artifacts\downloads\D01-tree.json"
$destination = (Resolve-Path (Join-Path $Root "data\raw\D01_Immersed-Tunnel-CFD\CFD-Data")).Path
$temporary = (Resolve-Path (Join-Path $Root "artifacts\downloads\D01-files")).Path
$tree = Get-Content -LiteralPath $treePath -Raw | ConvertFrom-Json
$allFiles = @($tree.tree | Where-Object { $_.path -like "CFD-Data/*.csv" })

Get-ChildItem -LiteralPath $destination -File |
    Where-Object { $_.Length -eq 0 } |
    Remove-Item -Force -ErrorAction SilentlyContinue
Get-ChildItem -LiteralPath $temporary -File |
    Where-Object { $_.Name -match "\.range\.part$|\.chunk$" } |
    Remove-Item -Force -ErrorAction SilentlyContinue

$queue = [System.Collections.Queue]::new()
foreach ($file in $allFiles) {
    $output = Join-Path $destination ([IO.Path]::GetFileName([string]$file.path))
    $complete = (Test-Path -LiteralPath $output) -and ((Get-Item -LiteralPath $output).Length -eq [int64]$file.size)
    if (-not $complete) {
        $queue.Enqueue([PSCustomObject]@{
                path = [string]$file.path
                size = [int64]$file.size
            })
    }
}

Write-Output ("queued=" + $queue.Count)

$worker = {
    param($RelativePath, $ExpectedSize, $Destination, $Temporary, $RangeChunkSize)

    $name = [IO.Path]::GetFileName([string]$RelativePath)
    $expected = [int64]$ExpectedSize
    $output = Join-Path $Destination $name
    $part = Join-Path $Temporary ($name + ".range.part")
    Remove-Item -LiteralPath $part -Force -ErrorAction SilentlyContinue

    $stream = [IO.File]::Open($part, [IO.FileMode]::CreateNew, [IO.FileAccess]::Write, [IO.FileShare]::None)
    try {
        for ($start = [int64]0; $start -lt $expected; $start += $RangeChunkSize) {
            $end = [Math]::Min($start + $RangeChunkSize - 1, $expected - 1)
            $chunkPath = Join-Path $Temporary ($name + "." + $start + ".chunk")
            $succeeded = $false
            for ($attempt = 1; $attempt -le 6 -and -not $succeeded; $attempt++) {
                Remove-Item -LiteralPath $chunkPath -Force -ErrorAction SilentlyContinue
                $url = "https://raw.githubusercontent.com/babeteax/Immersed-Tunnel-Fire-Location-Detection-Data/main/$RelativePath"
                curl.exe -L --fail --retry 2 --retry-all-errors --connect-timeout 20 --max-time 180 `
                    -H ("Range: bytes={0}-{1}" -f $start, $end) -sS $url -o $chunkPath
                $actualSize = if (Test-Path -LiteralPath $chunkPath) { (Get-Item -LiteralPath $chunkPath).Length } else { 0 }
                if ($LASTEXITCODE -eq 0 -and $actualSize -eq ($end - $start + 1)) {
                    $succeeded = $true
                } else {
                    Start-Sleep -Seconds 2
                }
            }

            if (-not $succeeded) {
                throw "chunk failed: $name $start-$end"
            }

            $bytes = [IO.File]::ReadAllBytes($chunkPath)
            $stream.Write($bytes, 0, $bytes.Length)
            Remove-Item -LiteralPath $chunkPath -Force -ErrorAction SilentlyContinue
        }
    } finally {
        $stream.Close()
    }

    if ((Get-Item -LiteralPath $part).Length -ne $expected) {
        throw "assembled size mismatch: $name"
    }

    Move-Item -LiteralPath $part -Destination $output -Force
    Write-Output ("DONE " + $name + " size=" + $expected)
}

$running = @()
$failed = 0
while ($queue.Count -gt 0 -or $running.Count -gt 0) {
    while ($running.Count -lt $MaxConcurrent -and $queue.Count -gt 0) {
        $file = $queue.Dequeue()
        $running += Start-Job -ScriptBlock $worker -ArgumentList @(
            $file.path, $file.size, $destination, $temporary, $ChunkSize
        )
    }

    foreach ($job in @($running)) {
        if ($job.State -in @("Completed", "Failed", "Stopped")) {
            Receive-Job -Job $job -ErrorAction Continue
            if ($job.State -ne "Completed") {
                $failed++
            }
            Remove-Job -Job $job -Force
            $running = @($running | Where-Object { $_.Id -ne $job.Id })
        }
    }

    if ($running.Count -gt 0) {
        Start-Sleep -Seconds 5
    }
}

$completeCount = @($allFiles | Where-Object {
        $output = Join-Path $destination ([IO.Path]::GetFileName([string]$_.path))
        (Test-Path -LiteralPath $output) -and ((Get-Item -LiteralPath $output).Length -eq [int64]$_.size)
    }).Count
Write-Output ("FINAL complete=" + $completeCount + " missing=" + ($allFiles.Count - $completeCount) + " failed_jobs=" + $failed)
