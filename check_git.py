import subprocess

cwd = 'z:/SHIFQ'

r = subprocess.run(['git', 'log', '--oneline', '-5'], capture_output=True, text=True, cwd=cwd)
print('GIT LOG:')
print(r.stdout)
print(r.stderr if r.stderr else '')

r2 = subprocess.run(['git', 'status', '--short'], capture_output=True, text=True, cwd=cwd)
print('GIT STATUS:')
print(r2.stdout if r2.stdout else '(clean)')
