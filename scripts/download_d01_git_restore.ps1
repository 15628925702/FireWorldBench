param(
    [string]$Root = (Get-Location).Path,
    [int]$MaxConcurrent = 4,
    [int]$MaxAttempts = 8,
    [int]$RetryDelaySeconds = 3
)

$resolvedRoot = (Resolve-Path -LiteralPath $Root).Path
$treePath = Join-Path $resolvedRoot "artifacts\downloads\D01-tree.json"
$temporaryRoot = (Resolve-Path -LiteralPath (Join-Path $resolvedRoot "artifacts\downloads\D01-files")).Path
$stagingRoot = (Resolve-Path -LiteralPath (Join-Path $resolvedRoot "data\raw\D01_Immersed-Tunnel-CFD")).Path
$tree = Get-Content -LiteralPath $treePath -Raw -Encoding utf8 | ConvertFrom-Json
$files = @($tree.tree | Where-Object { $_.path -like "CFD-Data/*.csv" } | Sort-Object path)

$completed = 0
$queue = [System.Collections.Queue]::new()
foreach ($file in $files) {
    $relative = [string]$file.path
    $expectedSize = [int64]$file.size
    $stagingPath = Join-Path $stagingRoot $relative

    if ((Test-Path -LiteralPath $stagingPath) -and (Get-Item -LiteralPath $stagingPath).Length -eq $expectedSize) {
        $completed++
        continue
    }
    $queue.Enqueue([PSCustomObject]@{ relative = $relative; size = $expectedSize; oid = [string]$file.sha })
}

Write-Output "START completed=$completed queued=$($queue.Count) concurrency=$MaxConcurrent"

$worker = {
    param($TemporaryRoot, $StagingRoot, $Relative, $ExpectedSize, $ObjectId, $MaxAttempts, $RetryDelaySeconds)

    $stagingPath = Join-Path $StagingRoot $Relative
    $temporaryPath = Join-Path $TemporaryRoot (([IO.Path]::GetFileName($Relative)) + ".blob.part")
    $url = "https://cdn.jsdelivr.net/gh/babeteax/Immersed-Tunnel-Fire-Location-Detection-Data@main/$Relative"
    $lastError = ""
    for ($attempt = 1; $attempt -le $MaxAttempts; $attempt++) {
        Remove-Item -LiteralPath $temporaryPath -Force -ErrorAction SilentlyContinue
        curl.exe -L --fail --retry 2 --retry-all-errors --connect-timeout 15 --max-time 180 -sS $url -o $temporaryPath
        $downloadReady = $LASTEXITCODE -eq 0 -and (Test-Path -LiteralPath $temporaryPath) -and (Get-Item -LiteralPath $temporaryPath).Length -eq $ExpectedSize
        if ($downloadReady) {
            $actualObjectId = (git hash-object --no-filters $temporaryPath).Trim()
            $downloadReady = $LASTEXITCODE -eq 0 -and $actualObjectId -eq $ObjectId
            if (-not $downloadReady) { $lastError = "Git blob SHA mismatch" }
        } else {
            $actualSize = if (Test-Path -LiteralPath $temporaryPath) { (Get-Item -LiteralPath $temporaryPath).Length } else { 0 }
            $lastError = "curl or size check failed; bytes=$actualSize expected=$ExpectedSize"
        }
        if ($downloadReady) {
            $destinationDirectory = Split-Path -Parent $stagingPath
            New-Item -ItemType Directory -Force -Path $destinationDirectory | Out-Null
            Copy-Item -LiteralPath $temporaryPath -Destination $stagingPath -Force
            Remove-Item -LiteralPath $temporaryPath -Force
            if ((Get-Item -LiteralPath $stagingPath).Length -eq $ExpectedSize) {
                return [PSCustomObject]@{ success = $true; relative = $Relative; attempts = $attempt }
            }
        }
        Start-Sleep -Seconds $RetryDelaySeconds
    }
    Remove-Item -LiteralPath $temporaryPath -Force -ErrorAction SilentlyContinue
    return [PSCustomObject]@{ success = $false; relative = $Relative; attempts = $MaxAttempts; error = $lastError }
}

$running = @()
$failed = [System.Collections.Generic.List[string]]::new()
while ($queue.Count -gt 0 -or $running.Count -gt 0) {
    while ($running.Count -lt $MaxConcurrent -and $queue.Count -gt 0) {
        $item = $queue.Dequeue()
        $running += Start-Job -ScriptBlock $worker -ArgumentList @(
            $temporaryRoot, $stagingRoot, $item.relative, $item.size, $item.oid, $MaxAttempts, $RetryDelaySeconds
        )
    }
    foreach ($job in @($running)) {
        if ($job.State -in @("Completed", "Failed", "Stopped")) {
            $lines = @(Receive-Job -Job $job -ErrorAction Continue)
            $result = $lines | Where-Object { $_.PSObject.Properties.Name -contains "success" } | Select-Object -Last 1
            if ($null -ne $result -and $result.success) {
                $completed++
                Write-Output "DONE $completed/$($files.Count) $($result.relative) attempts=$($result.attempts)"
            } else {
                $relative = if ($null -ne $result) { [string]$result.relative } else { "job-$($job.Id)" }
                $failed.Add($relative)
                Write-Warning "FAILED $relative"
            }
            Remove-Job -Job $job -Force
            $running = @($running | Where-Object { $_.Id -ne $job.Id })
        }
    }
    if ($running.Count -gt 0) { Start-Sleep -Milliseconds 500 }
}

$verified = @($files | Where-Object {
        $path = Join-Path $stagingRoot ([string]$_.path)
        (Test-Path -LiteralPath $path) -and (Get-Item -LiteralPath $path).Length -eq [int64]$_.size
    }).Count
Write-Output "FINAL verified=$verified missing=$($files.Count - $verified) failed=$($failed.Count)"
if ($verified -ne $files.Count) {
    exit 1
}
