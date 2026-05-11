import subprocess

# Check status
r = subprocess.run(['git', 'status', '--short'], capture_output=True, text=True, cwd='z:/SHIFQ')
print('STATUS:', r.stdout if r.stdout else '(clean)')
print('ERR:', r.stderr if r.stderr else '(none)')

# Add all
r = subprocess.run(['git', 'add', '-A'], capture_output=True, text=True, cwd='z:/SHIFQ')
print('ADD rc:', r.returncode)

# Commit
r = subprocess.run(['git', 'commit', '-m', 'Fix: AI error visibility + libgomp1 + lab delete buttons'], capture_output=True, text=True, cwd='z:/SHIFQ')
print('COMMIT rc:', r.returncode)
print('COMMIT out:', r.stdout[:500] if r.stdout else '(none)')
print('COMMIT err:', r.stderr[:500] if r.stderr else '(none)')

# Push
r = subprocess.run(['git', 'push', 'origin', 'main'], capture_output=True, text=True, cwd='z:/SHIFQ')
print('PUSH rc:', r.returncode)
print('PUSH out:', r.stdout[:500] if r.stdout else '(none)')
print('PUSH err:', r.stderr[:500] if r.stderr else '(none)')

# Log
r = subprocess.run(['git', 'log', '--oneline', '-5'], capture_output=True, text=True, cwd='z:/SHIFQ')
print('LOG:')
print(r.stdout)
