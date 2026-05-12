@echo off
cd /d z:\SHIFQ

git add app/templates/patients/detail.html app/templates/lab_results/index.html
git commit -m "Fix token key: use medisys_token instead of token for localStorage"
git push origin main

echo Done
git log --oneline -3
pause
