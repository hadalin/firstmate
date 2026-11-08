import os, pathlib, subprocess, json
root=pathlib.Path.cwd(); home=root/'.test-phase-tmp/report-home3'
subprocess.run(['bin/fm-lab-home.sh','create',str(home)],check=True,capture_output=True)
env={k:v for k,v in os.environ.items() if not k.startswith('FM_') and k not in ('NO_MISTAKES_GATE',)}
env.update(FM_HOME=str(home),FM_SUPERVISION_ACTOR='branch',FM_BRANCH_REPORT_TURN='proof.1')
s=home/'state'
cases=[('finished','attended','finished',False,True,'captain',False),('ordinary','attended','',False,False,'routine',True),('away','away','away',False,False,'routine',True),('leave','attended','leave',True,False,'routine',True)]
for task,posture,finished,afk,cleanup,expected,silent in cases:
    (s/'.supervision-host-turn').write_text(f'turn=proof.1\nrows=1\ntasks={task}\nunscoped=0\nwake=signal: {task}.status\nposture={posture}\nfinished_scouts={finished}\n')
    (s/f'{task}.meta').write_text('kind=scout\n'); (s/f'{task}.status').write_text('done: report ready\n')
    if cleanup:
        (s/f'{task}.meta').unlink(); (s/f'{task}.status').unlink()
    if afk:
        q=subprocess.run(['bin/fm-afk-contract.sh','enter','--words','Disposable validation away posture'],env=env,text=True,capture_output=True)
        print('away-entry:',q.returncode,q.stdout,q.stderr,flush=True); assert q.returncode==0
    p=subprocess.run(['bin/fm-branch-report.sh','--task',task,'--verdict','routine','--silent','true','--summary',f'{task}: report ready'],env=env,text=True,capture_output=True)
    print(f'CASE {task}: posture={posture}, cleanup={cleanup}, away-now={afk}\nexit={p.returncode}\n{p.stdout}{p.stderr}',flush=True)
    assert p.returncode==0
    row=json.loads((s/'branch-outcomes.jsonl').read_text().splitlines()[-1]); print('persisted:',json.dumps(row),flush=True)
    assert row['verdict']==expected and row['silent']==silent
    (s/'.afk').unlink(missing_ok=True)
subprocess.run(['bin/fm-afk-contract.sh','archive'],env=env,check=True,capture_output=True)
(home/'config/supervision-host').touch()
env['FM_SUPERVISION_HOST_PRIMARY']='claude'
env['FM_SUPERVISION_ACTOR']='main'
p=subprocess.run(['bin/fm-wake-drain.sh'],env=env,text=True,capture_output=True)
print('MAIN drain exit=',p.returncode,'\n',p.stdout,p.stderr,flush=True)
assert p.returncode==0 and 'finished: report ready' in p.stdout
