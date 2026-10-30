"""Execute the exact Macro save script with a concurrent news commit."""
import datetime as dt
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
ROOT=Path(__file__).resolve().parents[1]
WORKFLOW=(ROOT/'.github/workflows/macro.yml').read_text()
class MacroWorkflowTests(unittest.TestCase):
    def test_daily_schedule_kst_and_main_only_publication(self):
        t=dt.datetime(2026,10,30,3,20,tzinfo=dt.timezone.utc).astimezone(dt.timezone(dt.timedelta(hours=9)))
        self.assertEqual((t.hour,t.minute),(12,20));self.assertIn("cron: '20 3 * * *'",WORKFLOW);self.assertIn('workflow_dispatch:',WORKFLOW)
        job=WORKFLOW.split('  collect-and-publish:',1)[1];self.assertIn("if: github.ref == 'refs/heads/main'",job);self.assertIn('group: tourism-pulse-publish',job);self.assertIn('ref: main',job)
    def test_exact_save_step_persists_macro_and_preserves_concurrent_news(self):
        block=WORKFLOW.split('      - name: Save Macro data only\n        run: |\n',1)[1].split('      - name:',1)[0]
        script='\n'.join(line[10:] for line in block.rstrip().splitlines())
        def git(*args,cwd):return subprocess.run(['git',*args],cwd=cwd,check=True,capture_output=True)
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);remote=root/'remote.git';writer=root/'macro';news=root/'news';reader=root/'reader'
            git('init','--bare',str(remote),cwd=root);git('init','-b','main',str(writer),cwd=root);git('config','user.name','Macro Workflow Test',cwd=writer);git('config','user.email','test@example.invalid',cwd=writer)
            (writer/'site/data').mkdir(parents=True);(writer/'collector_state').mkdir()
            for name in ['news','newsroom','reports','research','briefing','filings']:(writer/'site/data'/f'{name}.json').write_text(json.dumps({'kind':name,'version':1}))
            (writer/'collector_state/archive.json').write_text('news canonical archive');(writer/'collector_state/reports_archive.json').write_text('research canonical archive')
            git('add','.',cwd=writer);git('commit','-m','Seed existing data',cwd=writer);git('remote','add','origin',str(remote),cwd=writer);git('push','-u','origin','main',cwd=writer)
            git('clone','-b','main',str(remote),str(news),cwd=root);git('config','user.name','News Job',cwd=news);git('config','user.email','news@example.invalid',cwd=news)
            (news/'site/data/news.json').write_text(json.dumps({'kind':'news','version':2}));git('add','site/data/news.json',cwd=news);git('commit','-m','Concurrent news refresh',cwd=news);git('push',cwd=news)
            for name in ['macro','macro_health']:(writer/'site/data'/f'{name}.json').write_text(json.dumps({'workflow_fixture_only':name}))
            for name in ['macro_archive','macro_run_summary']:(writer/'collector_state'/f'{name}.json').write_text(json.dumps({'workflow_fixture_only':name}))
            subprocess.run(['bash','-e','-c',script],cwd=writer,check=True,capture_output=True)
            git('clone','-b','main',str(remote),str(reader),cwd=root)
            self.assertEqual(json.loads((reader/'site/data/news.json').read_text())['version'],2)
            for path in ['site/data/macro.json','site/data/macro_health.json','collector_state/macro_archive.json','collector_state/macro_run_summary.json','collector_state/archive.json','collector_state/reports_archive.json']:
                self.assertEqual((reader/path).read_bytes(),(writer/path).read_bytes())
            self.assertFalse((reader/'site/collector_state').exists())
            for name in ['newsroom','reports','research','briefing','filings']:self.assertEqual(json.loads((reader/'site/data'/f'{name}.json').read_text())['version'],1)
