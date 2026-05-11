@echo off
cd /d z:\SHIFQ
git add -A
git commit -m "Fix AI visibility + libgomp1 + delete buttons"
git push origin main
echo Exit code: %ERRORLEVEL%
pause
