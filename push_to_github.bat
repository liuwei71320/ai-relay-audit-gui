@echo off
setlocal enabledelayedexpansion
:: 设置代码页为 UTF-8 以支持中文显示
chcp 65001 >nul

title AI 中转审计工具 - GitHub 代码提交助手

echo ======================================================
echo           AI Relay Audit 代码提交与推送工具
echo ======================================================
echo.
echo 您好！本工具将引导您将修改后的代码上传到您的 GitHub 仓库。
echo 即使您不熟悉 Git 命令，只需按照以下简单的中文提示操作即可。
echo.

:: 1. 检查状态
echo [第 1 步] 检查文件改动情况
echo ------------------------------------------------------
echo 正在读取本地文件的状态...
echo (英文含义参考：modified = 已修改的文件, untracked = 新创建的文件)
echo.
git status
echo ------------------------------------------------------
echo.
echo 请核对上面的列表。
echo 如果您看到了 audit.py、gui.py 或 update.md 在列表中，说明一切正常。
echo.
set /p confirm="确认这些修改并继续吗？(输入 Y 继续，输入 N 退出): "
if /i "%confirm%" neq "Y" goto :cancel

:: 2. 添加文件
echo.
echo [第 2 步] 准备上传文件...
:: 自动添加所有已知的修改
git add audit.py gui.py Documents/update.md .gitignore push_to_github.bat
echo 已将核心修改放入“待上传”列表。
echo.

:: 3. 提交说明
echo [第 3 步] 编写更新记录
echo ------------------------------------------------------
echo 请输入一句话，描述您这次改了什么（建议直接写中文）。
echo 推荐格式：修复了XXX问题 / 优化了XXX功能
echo.
set /p user_msg="请输入您的更新说明: "
if "!user_msg!"=="" (
    set user_msg="修复 GUI 渲染 Bug 并优化代码结构"
    echo [提示] 您没有输入说明，将使用默认说明: !user_msg!
)
echo.
echo 正在保存记录...
git commit -m "!user_msg!"
echo.

:: 4. 推送
echo [第 4 步] 同步到 GitHub 服务器
echo ------------------------------------------------------
echo 正在尝试连接 GitHub 并上传，请稍候...
echo.
echo 💡 温馨提示：
echo 如果程序在这里卡住，可能是正在等待网络连接。
echo 如果弹出浏览器窗口或登录对话框，请按提示完成 GitHub 账号登录。
echo.
git push origin main

if %errorlevel% equ 0 (
    echo.
    echo ======================================================
    echo ✅ 恭喜！操作成功。您的代码已安全同步到 GitHub。
    echo ======================================================
) else (
    echo.
    echo ❌ 上传失败了。
    echo 可能的原因：
    echo   1. 网络连接不稳定（请检查您的网络）。
    echo   2. 权限不足（请确保您在弹出的窗口中登录了正确的账号）。
    echo   3. 远程仓库有其他更新（可能需要先执行 git pull）。
)

goto :end

:cancel
echo.
echo [已取消] 您终止了操作，代码没有被上传。
echo.

:end
echo.
echo 任务结束，按任意键关闭本窗口...
pause >nul
exit
