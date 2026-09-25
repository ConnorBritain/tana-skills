"""Kata cloud-run correlation. Sends fixed metadata only; never reads transcripts."""
import json
import os
from pathlib import Path
import re
import subprocess
import sys

def instance():
    value=json.loads((Path.home()/'.kata02/instance.json').read_text())
    if not isinstance(value,dict) or not isinstance(value.get('workspaceId'),str) or not re.fullmatch(r'[A-Za-z0-9_-]{1,160}',value['workspaceId']) or not isinstance(value.get('callbackBase'),str) or not re.fullmatch(r'https://[a-z0-9-]+\.[a-z0-9-]+\.workers\.dev',value['callbackBase']):
        raise ValueError('Invalid private instance')
    return value
ROOT = Path.home() / '.kata'
ID = re.compile(r'[A-Za-z0-9_-]{1,160}\Z')
UUID = re.compile(r'[0-9a-f]{8}(?:-[0-9a-f]{4}){3}-[0-9a-f]{12}\Z')
HEX = re.compile(r'[a-f0-9]{64}\Z')

def valid(pattern, value):
    return isinstance(value, str) and pattern.fullmatch(value) is not None

def read_input():
    raw = sys.stdin.buffer.read(1048577)
    if len(raw) > 1048576:
        raise ValueError('Oversized input')
    return json.loads(raw)

def save(name, value):
    ROOT.mkdir(mode=0o700, parents=True, exist_ok=True)
    p = ROOT / name
    fd = os.open(p, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, 'w') as f:
        json.dump(value, f)

def request(path, value):
    # The existing cloud credential proxy may add Authorization; run grants are
    # sent in the bounded JSON body and have no access to queue administration.
    timeout = 70 if path == '/register-decision' else 8
    r = subprocess.run(['curl', '--silent', '--fail', '--max-time', str(timeout),
        '--connect-timeout', '3', '--proto', '=https', '--request', 'POST',
        '--header', 'Content-Type: application/json', '--data-binary', '@-', instance()['callbackBase'] + path],
        input=json.dumps(value).encode(), stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL, timeout=timeout+2, check=False)
    if r.returncode or len(r.stdout) > 4096:
        raise RuntimeError('Callback unavailable')
    return json.loads(r.stdout)

def validate_event(e):
    fields = {'version','kind','workspaceId','nodeId','sourceHash','runId','runToken','mode'}
    if not isinstance(e, dict) or set(e) != fields or e['version'] != 2 or e['kind'] != 'thought.route' or e['workspaceId'] != instance()['workspaceId'] or e['mode'] not in ('validate','route','reconcile'):
        raise ValueError('Invalid event')
    for key, pattern in [('nodeId',ID),('sourceHash',HEX),('runId',UUID),('runToken',HEX)]:
        if not valid(pattern,e[key]):
            raise ValueError('Invalid event identity')
    return e

def validate_result(v, e):
    fields = {'version','runId','nodeId','sourceHash','outcome','receiptNodeId','writesPerformed','unknownEffects','destinations'}
    if not isinstance(v,dict) or set(v) != fields or v['version'] != 1:
        raise ValueError('Invalid result')
    if any(v[k] != e[k] for k in ('runId','nodeId','sourceHash')):
        raise ValueError('Wrong result identity')
    if v['outcome'] not in ('routed','needs_review','not_ready','blocked','uncertain','validated') or type(v['writesPerformed']) is not bool or type(v['unknownEffects']) is not bool:
        raise ValueError('Invalid result state')
    if v['receiptNodeId'] is not None and not valid(ID,v['receiptNodeId']):
        raise ValueError('Invalid receipt')
    ds=v['destinations']
    if not isinstance(ds,list) or len(ds)>30:
        raise ValueError('Invalid destinations')
    for d in ds:
        if not isinstance(d,dict) or set(d) != {'service','id','effect','verified'} or d['service'] not in ('tana','eden','todoist','linear') or not valid(ID,d['id']) or d['effect'] not in ('created','updated','reused') or type(d['verified']) is not bool:
            raise ValueError('Invalid destination')
        if e['mode']=='reconcile' and d['service']!='tana' and d['effect']!='reused':
            raise ValueError('Reconciliation may not modify destinations')
    return v

def claim(e):
    e=validate_event(e)
    session=json.loads((ROOT/'session.json').read_text())['sessionId']
    if not valid(ID,session):
        raise ValueError('Session not initialized')
    if (ROOT/'grant.json').exists():
        prior=json.loads((ROOT/'grant.json').read_text())
        if prior.get('reported') or prior.get('event') != e or prior.get('sessionId') != session:
            raise ValueError('Run already bound or closed')
    save('grant.json', {'event':e,'sessionId':session,'reported':False})
    body={'version':1,'runId':e['runId'],'runToken':e['runToken'],'sessionId':session}
    reply=request('/run-claim',body)
    if reply.get('status') != 'claimed' or any(reply.get(k)!=e[k] for k in ('runId','nodeId','sourceHash','mode')):
        raise ValueError('Run claim rejected')
    print(json.dumps(reply))

def register_decision(identity):
    if not isinstance(identity,dict) or set(identity)!={'thoughtId','questionId','answerNodeId'} or any(not valid(ID,v) for v in identity.values()):
        raise ValueError('Invalid decision identity')
    grant=json.loads((ROOT/'grant.json').read_text())
    e=grant['event']
    if grant['reported'] or e['mode']!='route' or identity['thoughtId']!=e['nodeId']:
        raise ValueError('Registration requires active source route')
    reply=request('/register-decision',{**identity,'runId':e['runId'],'runToken':e['runToken'],'sessionId':grant['sessionId']})
    if reply.get('status')!='registered': raise ValueError('Registration held')
    print(json.dumps(reply))

def result_from_stop(data, grant):
    if data.get('agent_id') or data.get('hook_event_name')!='Stop' or data.get('session_id')!=grant['sessionId']:
        return None
    message=data.get('last_assistant_message')
    if not isinstance(message,str):
        raise ValueError('No final result')
    matches=re.findall(r'<kata-result>\s*(.*?)\s*</kata-result>',message,re.S)
    if len(matches)!=1 or len(matches[0])>8192:
        raise ValueError('Missing or ambiguous final result')
    value=validate_result(json.loads(matches[0]),grant['event'])
    return {'version':1,'runId':grant['event']['runId'],'runToken':grant['event']['runToken'],
        'sessionId':grant['sessionId'],'backgroundEmpty':data.get('background_tasks')==[] and data.get('session_crons')==[],
        'result':value}

def hook(data):
    if data.get('agent_id'):
        return
    if data.get('hook_event_name')=='SessionStart':
        session=data.get('session_id')
        if not valid(ID,session):
            raise ValueError('Invalid session')
        save('session.json',{'sessionId':session})
    elif data.get('hook_event_name')=='Stop' and (ROOT/'grant.json').exists():
        grant=json.loads((ROOT/'grant.json').read_text())
        body=result_from_stop(data,grant)
        if body is None:
            return
        reply=request('/run-result',body)
        if reply.get('status') not in ('reported','duplicate'):
            raise ValueError('Result rejected')
        # The server holds non-quiet results. No hook response can release a job.
        if body['backgroundEmpty']:
            grant['reported']=True
            save('grant.json',grant)

def install():
    p=Path.home()/'.claude/settings.json'
    p.parent.mkdir(parents=True,exist_ok=True)
    settings=json.loads(p.read_text()) if p.exists() else {}
    hooks=settings.setdefault('hooks',{})
    command='python3 "$HOME/.kata/runner.py" hook'
    old='python3 "$HOME/.kata/lifecycle.py"'
    for event in ('SessionStart','Stop','StopFailure','SessionEnd'):
        entries=hooks.get(event,[])
        updated=[]
        for entry in entries:
            kept=[h for h in entry.get('hooks',[]) if h.get('command') not in (old,command)]
            if kept:
                updated.append({**entry,'hooks':kept})
        if event in ('SessionStart','Stop'):
            updated.append({'hooks':[{'type':'command','command':command,'timeout':15}]})
        if updated:
            hooks[event]=updated
        else:
            hooks.pop(event,None)
    p.write_text(json.dumps(settings,indent=2)+'\n')

if __name__=='__main__':
    try:
        if os.environ.get('CLAUDE_CODE_REMOTE')!='true':
            raise ValueError('Cloud environment required')
        mode=sys.argv[1]
        if mode=='install': install()
        elif mode=='claim': claim(read_input())
        elif mode=='hook': hook(read_input())
        elif mode=='register': register_decision(read_input())
        else: raise ValueError('Unsupported command')
    except Exception:
        print('Kata run tracking unavailable; do not perform destination writes.',file=sys.stderr)
        raise SystemExit(1)
