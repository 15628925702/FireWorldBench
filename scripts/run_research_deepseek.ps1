param(
    [string]$EnvironmentName = "fireworldbench-v1"
)

if ([string]::IsNullOrWhiteSpace($env:DEEPSEEK_API_KEY)) {
    throw "DEEPSEEK_API_KEY is not present in this process environment"
}

$environment = (conda env list --json | ConvertFrom-Json).envs |
    Where-Object { (Split-Path -Leaf $_) -eq $EnvironmentName } |
    Select-Object -First 1
if ([string]::IsNullOrWhiteSpace($environment)) {
    throw "Conda environment not found: $EnvironmentName"
}
$python = Join-Path $environment "python.exe"
if (-not (Test-Path -LiteralPath $python)) {
    throw "Python not found in Conda environment: $EnvironmentName"
}

$samples = "artifacts/p5_research_deepseek_18_S063.json"
$config = "configs/deepseek_research_P5-RESEARCH-RUN-001.json"
$predictions = "artifacts/p5_research_deepseek_predictions_S063.json"
$scores = "artifacts/p5_research_deepseek_scores_S063.json"
if ((Test-Path -LiteralPath $predictions) -or (Test-Path -LiteralPath $scores)) {
    throw "DeepSeek research output already exists; refusing a duplicate paid run"
}

& $python -m fireworldbench.cli deepseek-pilot `
    --samples $samples `
    --config $config `
    --output $predictions `
    --max-samples 18
if ($LASTEXITCODE -ne 0) {
    exit $LASTEXITCODE
}

& $python -m fireworldbench.cli score `
    --samples $samples `
    --predictions $predictions `
    --output $scores
exit $LASTEXITCODE
