# 开发预览（不打包，直接打开线上站点）
$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

if (-not (Test-Path node_modules)) {
  npm install --registry=https://registry.npmmirror.com
}

npm start
