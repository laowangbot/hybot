@echo off
chcp 65001
echo 正在恢复GitHub到上一个版本...

REM 切换到项目目录
cd /d "C:\Users\PC\Desktop\会员机器人"

echo 当前目录: %CD%

echo.
echo 查看最近的提交历史...
git log --oneline -5

echo.
echo 恢复到最后一次提交（HEAD~1）...
git reset --hard HEAD~1

echo.
echo 强制推送到GitHub（覆盖远程仓库）...
git push origin main --force

echo.
echo 恢复完成！
echo 仓库地址: https://github.com/laowangbot/hybot

pause


