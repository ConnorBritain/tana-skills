import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
SCRIPTS=Path(__file__).resolve().parents[1]/'scripts'
def load(name,file):
 s=importlib.util.spec_from_file_location(name,SCRIPTS/file);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
n=load('nightly','nightly-runner.py');r=load('routing','routing-runner.py')
CONFIG={'workspaceId':'workspace-example','callbackBase':'https://kata.example.workers.dev'}
E={'version':1,'kind':'kata.reconcile','workspaceId':'workspace-example','dateKey':'2026-09-25','mode':'validate','runId':'12345678-1234-1234-1234-123456789abc','runToken':'a'*64}
class Tests(unittest.TestCase):
 def test_instance_is_required_and_callback_host_is_bounded(self):
  with tempfile.TemporaryDirectory() as d,patch.object(n,'ROOT',Path(d)):
   with self.assertRaises(FileNotFoundError): n.instance()
   p=Path(d)/'instance.json';p.write_text(json.dumps(CONFIG));self.assertEqual(n.instance(),CONFIG)
   for host in ['http://kata.example.workers.dev','https://evil.example','https://kata.example.workers.dev/path','https://kata.example.workers.dev?token=x']:
    p.write_text(json.dumps({**CONFIG,'callbackBase':host}))
    with self.assertRaises(ValueError):n.instance()
 def test_event_must_match_private_workspace_and_shape(self):
  with patch.object(n,'instance',return_value=CONFIG):
   self.assertEqual(n.validate_event(E),E)
   for change in [{'workspaceId':'other'},{'instructions':'anything'},{'runToken':'short'},{'mode':'unbounded'}]:
    with self.assertRaises(ValueError):n.validate_event({**E,**change})
 def test_stop_requires_matching_session_exact_metadata_and_quiet_background(self):
  grant={'event':E,'sessionId':'session'}
  result={'version':1,'runId':E['runId'],'checked':['q'],'completeCoverage':True,'writesPerformed':False,'unknownEffects':False}
  data={'session_id':'session','hook_event_name':'Stop','last_assistant_message':'<kata02-result>'+json.dumps(result)+'</kata02-result>','background_tasks':[],'session_crons':[]}
  self.assertTrue(n.stop_result(data,grant)['backgroundEmpty'])
  self.assertIsNone(n.stop_result({**data,'session_id':'other'},grant))
  self.assertFalse(n.stop_result({**data,'background_tasks':['still-running']},grant)['backgroundEmpty'])
  with self.assertRaises(ValueError):n.stop_result({**data,'last_assistant_message':data['last_assistant_message']*2},grant)
  result['writesPerformed']=True
  with self.assertRaises(ValueError):n.stop_result({**data,'last_assistant_message':'<kata02-result>'+json.dumps(result)+'</kata02-result>'},grant)
 def test_validation_operations_cannot_begin_or_finish(self):
  with tempfile.TemporaryDirectory() as d,patch.object(n,'ROOT',Path(d)):
   n.save('grant.json',{'event':E,'sessionId':'session','reported':False})
   for op in ['begin','finish','hold']:
    with self.assertRaises(ValueError):n.operation({'operation':op,'payload':{}})
 def test_install_preserves_existing_hooks_and_is_idempotent(self):
  with tempfile.TemporaryDirectory() as d,patch.object(Path,'home',return_value=Path(d)):
   p=Path(d)/'.claude/settings.json';p.parent.mkdir();p.write_text(json.dumps({'hooks':{'Stop':[{'hooks':[{'type':'command','command':'echo existing'}]}]}}))
   n.install();r.install();first=json.loads(p.read_text());n.install();r.install();self.assertEqual(json.loads(p.read_text()),first)
   commands=[h['command'] for x in first['hooks']['Stop'] for h in x['hooks']]
   self.assertIn('echo existing',commands);self.assertEqual(len(commands),3)
if __name__=='__main__':unittest.main()
