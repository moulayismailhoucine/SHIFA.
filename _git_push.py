import subprocess
import sys

CMDS = [
    ['git', 'add', '-f', 'app/ai/models/bone_fracture_model.h5'],
    ['git', 'add', 'app/ai/inference.py', 'app/ai/predict.py', 'app/ai/config.py', 'app/routers/lab_results.py', 'app/routers/nursing_orders.py', 'app/schemas/__init__.py', 'app/templates/patients/detail.html', '.gitignore'],
    ['git', 'diff', '--cached', '--stat'],
    ['git', 'commit', '-m', 'Fix AI for Render: add model file, make TF graceful, add logging'],
    ['git', 'push', 'origin', 'main'],
]

out = []
for cmd in CMDS:
    r = subprocess.run(cmd, capture_output=True, text=True, cwd='z:/SHIFQ')
    out.append(f'CMD: {" ".join(cmd)}')
    out.append(f'RC: {r.returncode}')
    out.append(f'OUT: {r.stdout}')
    out.append(f'ERR: {r.stderr}')
    out.append('---')

with open('z:/SHIFQ/_git_push_log.txt', 'w') as f:
    f.write('\n'.join(out))
print('Done. Check _git_push_log.txt')
