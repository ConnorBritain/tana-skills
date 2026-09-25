"""Kata 02 scoped batch helper. Fixed host, metadata-only callbacks."""
import json
import os
from pathlib import Path
import re
import subprocess
import sys
ROOT=Path.home()/'.kata02'
HEX=re.compile(r'[a-f0-9]{64}\Z')
ID=re.compile(r'[A-Za-z0-9_-]{1,160}\Z')
UUID=re.compile(r'[0-9a-f]{8}(?:-[0-9a-f]{4}){3}-[0-9a-f]{12}\Z')
def valid(p,v): return isinstance(v,str) and p.fullmatch(v) is not None
def read_input():
 raw=sys.stdin.buffer.read(32769)
 if len(raw)>32768: raise ValueError('Oversized input')
 return json.loads(raw)
def save(name,value):
 ROOT.mkdir(mode=0o700,parents=True,exist_ok=True)
 fd=os.open(ROOT/name,os.O_WRONLY|os.O_CREAT|os.O_TRUNC,0o600)
 with os.fdopen(fd,'w') as f: json.dump(value,f)
def instance():
 value=json.loads((ROOT/'instance.json').read_text())
 if not isinstance(value,dict) or not valid(ID,value.get('workspaceId')) or not isinstance(value.get('callbackBase'),str) or not re.fullmatch(r'https://[a-z0-9-]+\.[a-z0-9-]+\.workers\.dev',value['callbackBase']):
  raise ValueError('Invalid private instance')
 return value
def request(body):
 r=subprocess.run(['curl','--silent','--fail','--max-time','70','--connect-timeout','3','--proto','=https','--request','POST','--header','Content-Type: application/json','--data-binary','@-',instance()['callbackBase']+'/nightly-call'],input=json.dumps(body).encode(),stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,timeout=72,check=False)
 if r.returncode or len(r.stdout)>262144: raise RuntimeError('Operation unavailable')
 return json.loads(r.stdout)
def validate_event(e):
 if not isinstance(e,dict) or set(e)!={'version','kind','workspaceId','dateKey','mode','runId','runToken'} or e['version']!=1 or e['kind']!='kata.reconcile' or e['workspaceId']!=instance()['workspaceId'] or e['mode'] not in ('apply','validate') or not valid(UUID,e['runId']) or not valid(HEX,e['runToken']) or not isinstance(e['dateKey'],str) or not re.fullmatch(r'\d{4}-\d{2}-\d{2}(?:-test-[a-f0-9-]{36})?',e['dateKey']): raise ValueError('Invalid event')
 return e
def call(grant,operation,payload):
 return request({'version':1,'runId':grant['event']['runId'],'runToken':grant['event']['runToken'],'sessionId':grant['sessionId'],'operation':operation,'payload':payload})
def claim(e):
 e=validate_event(e)
 session=json.loads((ROOT/'session.json').read_text())['sessionId']
 if not valid(ID,session): raise ValueError('Missing session')
 grant={'event':e,'sessionId':session,'reported':False}
 if (ROOT/'grant.json').exists():
  old=json.loads((ROOT/'grant.json').read_text())
  if old['event']!=e or old['sessionId']!=session or old['reported']: raise ValueError('Grant already used')
 save('grant.json',grant)
 reply=call(grant,'claim',{})
 if reply.get('status')!='claimed' or any(reply.get(k)!=e[k] for k in ('runId','dateKey','mode')): raise ValueError('Claim rejected')
 print(json.dumps(reply))
def operation(body):
 if not isinstance(body,dict) or set(body)!={'operation','payload'} or body['operation'] not in ('list','inspect','begin','finish','hold'): raise ValueError('Invalid operation')
 grant=json.loads((ROOT/'grant.json').read_text())
 if grant['reported']: raise ValueError('Run already reported')
 if grant['event']['mode']=='validate' and body['operation'] not in ('list','inspect'): raise ValueError('Validation is read only')
 print(json.dumps(call(grant,body['operation'],body['payload'])))
def stop_result(data,grant):
 if data.get('agent_id') or data.get('hook_event_name')!='Stop' or data.get('session_id')!=grant['sessionId']: return None
 message=data.get('last_assistant_message','')
 matches=re.findall(r'<kata02-result>\s*(.*?)\s*</kata02-result>',message,re.S)
 if len(matches)!=1 or len(matches[0])>20000: raise ValueError('Missing final result')
 result=json.loads(matches[0])
 if not isinstance(result,dict) or set(result)!={'version','runId','checked','completeCoverage','writesPerformed','unknownEffects'} or result['version']!=1 or result['runId']!=grant['event']['runId'] or any(type(result[k]) is not bool for k in ('completeCoverage','writesPerformed','unknownEffects')) or not isinstance(result['checked'],list) or len(result['checked'])>100 or any(not valid(ID,x) for x in result['checked']) or len(set(result['checked']))!=len(result['checked']): raise ValueError('Invalid final result')
 if grant['event']['mode']=='validate' and result['writesPerformed']: raise ValueError('Validation wrote data')
 return {'backgroundEmpty':data.get('background_tasks')==[] and data.get('session_crons')==[],'result':result}
def hook(data):
 if data.get('agent_id'): return
 if data.get('hook_event_name')=='SessionStart':
  if not valid(ID,data.get('session_id')): raise ValueError('Invalid session')
  save('session.json',{'sessionId':data['session_id']})
 elif data.get('hook_event_name')=='Stop' and (ROOT/'grant.json').exists():
  grant=json.loads((ROOT/'grant.json').read_text());payload=stop_result(data,grant)
  if payload is None: return
  reply=call(grant,'stop',payload)
  if reply.get('status') not in ('reported','duplicate'): raise ValueError('Report rejected')
  if payload['backgroundEmpty']: grant['reported']=True;save('grant.json',grant)
def install():
 p=Path.home()/'.claude/settings.json';p.parent.mkdir(parents=True,exist_ok=True)
 settings=json.loads(p.read_text()) if p.exists() else {};hooks=settings.setdefault('hooks',{})
 command='python3 "$HOME/.kata02/nightly-runner.py" hook'
 for event in ('SessionStart','Stop'):
  entries=[]
  for entry in hooks.get(event,[]):
   kept=[h for h in entry.get('hooks',[]) if h.get('command')!=command]
   if kept: entries.append({**entry,'hooks':kept})
  hooks[event]=entries+[{'hooks':[{'type':'command','command':command,'timeout':75}]}]
 p.write_text(json.dumps(settings,indent=2)+'\n')
if __name__=='__main__':
 try:
  if os.environ.get('CLAUDE_CODE_REMOTE')!='true': raise ValueError('Cloud environment required')
  mode=sys.argv[1]
  if mode=='install': install()
  elif mode=='claim': claim(read_input())
  elif mode=='op': operation(read_input())
  elif mode=='hook': hook(read_input())
  else: raise ValueError('Unsupported command')
 except Exception:
  print('Kata 02 operation unavailable. Do not retry destination writes without reconciliation.',file=sys.stderr)
  raise SystemExit(1)
