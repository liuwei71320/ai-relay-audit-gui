@echo off
chcp 65001 > nul
title AI Relay Security Audit Tool - Web Console

echo ======================================================
echo    AI 中转站纯度审计工具 - Web 界面启动器
echo ======================================================
echo.

:: 检查 Python 环境
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [错误] 未找到 Python。请确保已安装 Python 并将其添加到系统环境变量 PATH 中。
    pause
    exit /b
)

:: 检查 Streamlit 依赖
python -c "import streamlit" >nul 2>&1
if %errorlevel% neq 0 (
    echo [提示] 未检测到 Streamlit 库，正在为您自动安装...
    pip install streamlit -i https://pypi.tuna.tsinghua.edu.cn/simple
    if %errorlevel% neq 0 (
        echo [错误] Streamlit 安装失败。请检查网络并手动运行:
        echo pip install streamlit
        pause
        exit /b
    )
)

:: 启动 Web 界面
echo [信息] 正在启动 Web 控制台，请稍候...
echo [信息] 如果浏览器没有自动打开，请访问脚本输出的 Local URL 地址。
echo.

python -m streamlit run gui.py

if %errorlevel% neq 0 (
    echo.
    echo [错误] 启动失败。
    pause
)
