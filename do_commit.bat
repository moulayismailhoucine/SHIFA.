@echo off
cd /d z:\SHIFQ

git add app/models/__init__.py
git add app/routers/medicines.py
git add app/main.py
git add app/templates/patients/detail.html
git add seed_medicines.py
git commit -m "Add medicine autocomplete: Medicine model, search API, structured prescription form"
git push origin main

echo DONE
