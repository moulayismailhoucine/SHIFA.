import subprocess, sys

cwd = 'z:/SHIFQ'
log = open('z:/SHIFQ/_commit_log.txt', 'w')

def run(cmd):
    log.write(f'CMD: {cmd}\n')
    r = subprocess.run(cmd, capture_output=True, text=True, cwd=cwd)
    log.write(f'RC: {r.returncode}\n')
    log.write(f'OUT: {r.stdout}\n')
    log.write(f'ERR: {r.stderr}\n\n')
    return r

run(['git', 'status', '--short'])
run(['git', 'add', 'app/templates/patients/detail.html'])
run(['git', 'commit', '-m', 'Fix patient detail: remove undefined Auth, use localStorage token and hardcoded doctor role'])
run(['git', 'push', 'origin', 'main'])
run(['git', 'log', '--oneline', '-3'])
log.close()
print('Done. Check _commit_log.txt')
