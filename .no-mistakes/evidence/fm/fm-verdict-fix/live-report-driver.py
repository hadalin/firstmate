import os,json,subprocess,shutil
from pathlib import Path
root=Path.cwd(); home=root/'.test-verdict-home'
evidence=Path('/Users/primoz/.no-mistakes/evidence/01M5M31SA0Z85QJ919A5527S3Q/report-live.txt')
env=os.environ.copy()
for k in list(env):
 if k.startswith('FM_') or k in ('TASKS_AXI_FILE','TASKS_AXI_BACKEND'): env.pop(k)
env['FM_HOME']=str(home)
def run(*args,code=0):
 p=subprocess.run(args,env=env,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
 log.append('$ '+' '.join(args)+'\n'+p.stdout+'exit='+str(p.returncode)+'\n')
 assert p.returncode==code,p.stdout
 return p.stdout
log=[]
try:
 run('bin/fm-lab-home.sh','create',str(home))
 env.update(FM_SUPERVISION_ACTOR='branch',FM_BRANCH_REPORT_TURN='live1')
 def turn(posture,scouts):
  (home/'state/.supervision-host-turn').write_text(f'turn=live1\nrows=1\ntasks=scout\nunscoped=0\nwake=signal: scout.status done\nposture={posture}\nfinished_scouts={scouts}\n')
 def report(summary):
  run('bin/fm-branch-report.sh','--task','scout','--verdict','routine','--summary',summary,'--silent','true')
  row=json.loads((home/'state/branch-outcomes.jsonl').read_text().splitlines()[-1]); log.append('Stored outcome: '+json.dumps(row)+'\n'); return row
 turn('attended','scout')
 assert not (home/'state/scout.meta').exists()
 r=report('Finished report survives removal of scout records'); assert (r['verdict'],r['silent'])==('captain',False)
 turn('attended','')
 r=report('Unfinished scout routine update'); assert (r['verdict'],r['silent'])==('routine',True)
 turn('away','scout')
 r=report('Away-started turn remains routine'); assert (r['verdict'],r['silent'])==('routine',True)
 env.pop('FM_SUPERVISION_ACTOR'); run('bin/fm-afk-contract.sh','enter','--words','disposable validation away mode'); env['FM_SUPERVISION_ACTOR']='branch'
 turn('attended','scout')
 r=report('Captain went away during this attended turn'); assert (r['verdict'],r['silent'])==('routine',True)
 run('bin/fm-branch-report.sh','--task','other','--verdict','routine','--summary','out of scope',code=3)
 env['FM_BRANCH_REPORT_TURN']='ended'
 run('bin/fm-branch-report.sh','--task','scout','--verdict','routine','--summary','stale turn',code=3)
 log.append('All live CLI assertions passed.\n')
finally:
 evidence.write_text(''.join(log)); shutil.rmtree(home,ignore_errors=True)
