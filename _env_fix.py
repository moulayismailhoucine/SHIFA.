import subprocess
import os
os.chdir('z:/SHIFQ')

with open('env_fix_log.txt', 'w') as log:
    def run(cmd):
        log.write(f"CMD: {cmd}\n")
        r = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        log.write(f"OUT: {r.stdout}\n")
        log.write(f"ERR: {r.stderr}\n")
        log.write(f"RC: {r.returncode}\n\n")
        return r

    # Check if tracked
    run("git ls-files .env")
    
    # Remove from cache
    run("git rm --cached .env")
    
    # Stage gitignore
    run("git add .gitignore")
    
    # Check status
    r = run("git status --short")
    
    if r.stdout.strip():
        # Commit
        run('git commit -m "Remove .env from git tracking (security)"')
        # Push
        run("git push origin main")
        log.write("DONE\n")
    else:
        log.write("NOTHING TO COMMIT\n")
