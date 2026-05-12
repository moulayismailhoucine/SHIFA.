import subprocess

cwd = 'z:/SHIFQ'

# Add only the patient detail file
r = subprocess.run(['git', 'add', 'app/templates/patients/detail.html'], capture_output=True, text=True, cwd=cwd)
print('ADD rc:', r.returncode)

# Commit
r = subprocess.run(
    ['git', 'commit', '-m', 'Fix patient detail: remove undefined Auth, use localStorage token and hardcoded doctor role'],
    capture_output=True, text=True, cwd=cwd
)
print('COMMIT rc:', r.returncode)
print('COMMIT out:', r.stdout[:500] if r.stdout else '(none)')
print('COMMIT err:', r.stderr[:500] if r.stderr else '(none)')

# Push
r = subprocess.run(['git', 'push', 'origin', 'main'], capture_output=True, text=True, cwd=cwd)
print('PUSH rc:', r.returncode)
print('PUSH out:', r.stdout[:500] if r.stdout else '(none)')
print('PUSH err:', r.stderr[:500] if r.stderr else '(none)')
