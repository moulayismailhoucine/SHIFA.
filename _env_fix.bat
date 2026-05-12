@echo off
cd /d z:\SHIFQ

echo Checking if .env is tracked...
git ls-files .env

echo Removing .env from git cache...
git rm --cached .env

echo Staging .gitignore...
git add .gitignore

echo Git status:
git status --short

echo Committing...
git commit -m "Remove .env from git tracking (security)"

echo Pushing...
git push origin main

echo Done.
pause
