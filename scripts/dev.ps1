# 教育政策监测平台 - 本地开发脚本
# 用法: .\scripts\dev.ps1 [start|stop|restart|setup]
param(
    [ValidateSet("start", "stop", "restart", "setup")]
    [string]$Action = "start"
)

$ErrorActionPreference = "Stop"
$Root = Split-Path $PSScriptRoot -Parent
$Backend = Join-Path $Root "backend"
$Frontend = Join-Path $Root "frontend"
$BackendPort = 8000
$FrontendPort = 3001

function Write-Title($msg) {
    Write-Host "`n=== $msg ===" -ForegroundColor Cyan
}

function Stop-Port($Port) {
    $pids = @()
    try {
        $pids += @(Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue |
            Select-Object -ExpandProperty OwningProcess -Unique)
    } catch { }
    if ($pids.Count -eq 0) {
        $lines = netstat -ano 2>$null | Select-String ":$Port\s+.*LISTENING"
        $pids += @($lines | ForEach-Object { ($_.Line -split '\s+')[-1] } | Sort-Object -Unique)
    }
    foreach ($procId in ($pids | Sort-Object -Unique)) {
        if ($procId -match '^\d+$') {
            cmd /c "taskkill /PID $procId /F /T >nul 2>&1"
        }
    }
}

function Ensure-Setup {
    if (-not (Test-Path (Join-Path $Backend ".venv"))) {
        Write-Host "创建 Python 虚拟环境..." -ForegroundColor Yellow
        python -m venv (Join-Path $Backend ".venv")
    }
    if (-not (Test-Path (Join-Path $Frontend "node_modules"))) {
        Write-Host "安装前端依赖..." -ForegroundColor Yellow
        Push-Location $Frontend
        npm.cmd install
        Pop-Location
    }
    if (-not (Test-Path (Join-Path $Frontend ".env.local"))) {
        Copy-Item (Join-Path $Frontend ".env.example") (Join-Path $Frontend ".env.local")
    }
    New-Item -ItemType Directory -Force -Path (Join-Path $Backend "data") | Out-Null
}

function Start-Services {
    Write-Title "启动服务"
    Stop-Port $BackendPort
    Stop-Port $FrontendPort
    Start-Sleep -Milliseconds 500

    $uvicorn = Join-Path $Backend ".venv\Scripts\uvicorn.exe"
    if (-not (Test-Path $uvicorn)) {
        Write-Host "未找到后端环境，请先运行: .\scripts\dev.ps1 setup" -ForegroundColor Red
        exit 1
    }

    $backendCmd = "cd '$Backend'; Write-Host '后端 http://127.0.0.1:$BackendPort' -ForegroundColor Green; & '$uvicorn' app.main:app --reload --host 127.0.0.1 --port $BackendPort"
    $frontendCmd = "cd '$Frontend'; Write-Host '前端 http://localhost:$FrontendPort' -ForegroundColor Green; npm.cmd run dev"

    Start-Process powershell -ArgumentList "-NoExit", "-Command", $backendCmd | Out-Null
    Start-Sleep -Seconds 1
    Start-Process powershell -ArgumentList "-NoExit", "-Command", $frontendCmd | Out-Null

    Write-Host ""
    Write-Host "  前端  http://localhost:$FrontendPort" -ForegroundColor Green
    Write-Host "  后端  http://localhost:$BackendPort/docs" -ForegroundColor Green
    Write-Host "  账号  admin / admin123" -ForegroundColor Green
    Write-Host ""
    Write-Host "已在新窗口启动。停止请运行: .\scripts\dev.ps1 stop" -ForegroundColor Cyan
}

function Stop-Services {
    Write-Title "停止服务"
    Stop-Port $BackendPort
    Stop-Port $FrontendPort
    Write-Host "已停止端口 $BackendPort / $FrontendPort 上的服务" -ForegroundColor Green
}

switch ($Action) {
    "setup" {
        Write-Title "首次安装"
        Ensure-Setup
        Write-Host "安装后端依赖..." -ForegroundColor Yellow
        & (Join-Path $Backend ".venv\Scripts\pip.exe") install -r (Join-Path $Backend "requirements-local.txt") -q
        Write-Host "安装完成。运行 .\start.bat 启动项目" -ForegroundColor Green
    }
    "stop" { Stop-Services }
    "restart" { Stop-Services; Start-Sleep -Seconds 1; Start-Services }
    default { Ensure-Setup; Start-Services }
}
