@echo off
cd /d z:\SHIFQ

git add app/templates/patients/detail.html
git commit -m "Fix patient detail: add null token check to prevent infinite spinner"
git push origin main

echo Done
git log --oneline -3
pause
