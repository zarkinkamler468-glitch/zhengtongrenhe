# 构建 Windows 安装包
$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

if (-not (Test-Path node_modules)) {
  npm install --registry=https://registry.npmmirror.com
}

Write-Host "==> 构建安装包 (NSIS)..." -ForegroundColor Cyan
npm run build:win

Write-Host ""
Write-Host "完成。安装包目录: desktop\release\" -ForegroundColor Green
Write-Host "开发预览: npm start" -ForegroundColor Green
