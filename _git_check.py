import subprocess
import os
os.chdir('z:/SHIFQ')

# Check status
r = subprocess.run(['git', 'status', '--short'], capture_output=True, text=True)
print('STATUS:', r.stdout if r.stdout else 'clean')

# Check log
r = subprocess.run(['git', 'log', '--oneline', '-5'], capture_output=True, text=True)
print('LOG:')
print(r.stdout)

# Check uncommitted changes in dependencies.py
r = subprocess.run(['git', 'diff', 'app/dependencies.py'], capture_output=True, text=True)
if r.stdout:
    print('DIFF found in dependencies.py')
else:
    print('No uncommitted changes in dependencies.py')
