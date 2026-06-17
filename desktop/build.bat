@echo off
chcp 65001 >nul
cd /d "%~dp0"

if not exist node_modules (
  echo 正在安装依赖...
  call npm install
  if errorlevel 1 exit /b 1
)

echo 正在打包 Windows 安装程序...
call npm run build:win

if errorlevel 1 (
  echo 打包失败
  exit /b 1
)

echo.
echo 完成！安装包目录: desktop\release\
pause
