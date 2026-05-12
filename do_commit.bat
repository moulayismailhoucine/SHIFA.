@echo off
cd /d z:\SHIFQ
git add -A
git commit -m "Fix token key mismatch: use medisys_token everywhere"
git push origin main
echo DONE
