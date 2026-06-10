# 打包「可上传纯代码」到 zip，排除 node_modules / .venv / .env 等
$ErrorActionPreference = "Stop"
$Root = Split-Path $PSScriptRoot -Parent
$Staging = Join-Path $env:TEMP "zhengtongrenhe-upload-staging"
$ZipOut = Join-Path ([Environment]::GetFolderPath("Desktop")) "zhengtongrenhe-upload.zip"

$ExcludeDirNames = @(
    "node_modules", ".next", ".venv", "__pycache__", "out",
    "data", ".git", ".idea", ".vscode"
)
$ExcludeFileNames = @(
    ".env", ".env.local", "tsconfig.tsbuildinfo"
)

function Should-Skip($relPath) {
    $parts = $relPath -split "[\\/]"
    foreach ($p in $parts) {
        if ($ExcludeDirNames -contains $p) { return $true }
    }
    $name = Split-Path $relPath -Leaf
    if ($ExcludeFileNames -contains $name) { return $true }
    if ($name -match "\.pyc$") { return $true }
    if ($relPath -match "backend\\scripts\\output\\" -and $name -ne ".gitkeep") { return $true }
    return $false
}

if (Test-Path $Staging) { Remove-Item $Staging -Recurse -Force }
New-Item -ItemType Directory -Path $Staging | Out-Null

$files = Get-ChildItem -Path $Root -Recurse -File -Force | Where-Object {
    $rel = $_.FullName.Substring($Root.Length + 1)
    -not (Should-Skip $rel)
}

foreach ($f in $files) {
    $rel = $f.FullName.Substring($Root.Length + 1)
    $dest = Join-Path $Staging $rel
    $destDir = Split-Path $dest -Parent
    if (-not (Test-Path $destDir)) { New-Item -ItemType Directory -Path $destDir -Force | Out-Null }
    Copy-Item $f.FullName $dest -Force
}

if (Test-Path $ZipOut) { Remove-Item $ZipOut -Force }
Compress-Archive -Path (Join-Path $Staging "*") -DestinationPath $ZipOut -CompressionLevel Optimal
Remove-Item $Staging -Recurse -Force

$mb = [math]::Round((Get-Item $ZipOut).Length / 1MB, 1)
Write-Host ""
Write-Host "已生成: $ZipOut  ($mb MB)" -ForegroundColor Green
Write-Host "上传到服务器 /www/wwwroot/ 解压后按 docs/手动上传清单.md 配置 .env 并 docker compose up" -ForegroundColor Cyan
