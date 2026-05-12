#!/usr/bin/env python3
import subprocess
import sys

cwd = "z:/SHIFQ"

# Step 1: Check if .env is tracked
r = subprocess.run(["git", "ls-files", ".env"], capture_output=True, text=True, cwd=cwd)
if r.stdout.strip():
    print(".env is tracked — removing from git cache...")
    r2 = subprocess.run(["git", "rm", "--cached", ".env"], capture_output=True, text=True, cwd=cwd)
    print(r2.stdout)
    if r2.returncode != 0:
        print("ERROR:", r2.stderr)
        sys.exit(1)
else:
    print(".env is NOT tracked — good.")

# Step 2: Stage .gitignore changes
r3 = subprocess.run(["git", "add", ".gitignore"], capture_output=True, text=True, cwd=cwd)
if r3.returncode != 0:
    print("ERROR adding .gitignore:", r3.stderr)
    sys.exit(1)

# Step 3: Check status
r4 = subprocess.run(["git", "status", "--short"], capture_output=True, text=True, cwd=cwd)
print("\nGit status:")
print(r4.stdout if r4.stdout else "(clean)")

# Step 4: Commit
if r4.stdout.strip():
    r5 = subprocess.run(
        ["git", "commit", "-m", "Remove .env from git tracking (security)"],
        capture_output=True, text=True, cwd=cwd
    )
    print(r5.stdout)
    if r5.returncode != 0:
        print("Commit error:", r5.stderr)
        sys.exit(1)
    
    # Step 5: Push
    r6 = subprocess.run(["git", "push", "origin", "main"], capture_output=True, text=True, cwd=cwd)
    print(r6.stdout)
    if r6.returncode != 0:
        print("Push error:", r6.stderr)
        sys.exit(1)
    print("\n✅ Done — .env removed from GitHub")
else:
    print("\nNothing to commit")
