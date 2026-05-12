@echo off
cd /d z:\SHIFQ

git status --short > _push_status.txt 2>&1
git add app/templates/patients/detail.html >> _push_status.txt 2>&1
git commit -m "Fix patient detail: remove undefined Auth, use localStorage token and hardcoded doctor role" >> _push_status.txt 2>&1
git push origin main >> _push_status.txt 2>&1
git log --oneline -3 >> _push_status.txt 2>&1

echo Done >> _push_status.txt
