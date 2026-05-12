import subprocess

cwd = 'z:/SHIFQ'

r = subprocess.run(['git', 'log', '--oneline', '-3'], capture_output=True, text=True, cwd=cwd)
print(r.stdout)
