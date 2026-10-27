"""Offline execution of the real workflow save step against a temporary Git remote."""
import json
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = (ROOT / '.github/workflows/collect.yml').read_text()


class WorkflowContractTests(unittest.TestCase):
    def test_manual_schedule_and_main_only_deployment_remain(self):
        self.assertIn('workflow_dispatch:', WORKFLOW)
        self.assertIn("cron: '17 */2 * * *'", WORKFLOW)
        self.assertIn("cron: '30 1 * * *'", WORKFLOW)
        self.assertIn("if: github.ref == 'refs/heads/main'", WORKFLOW)
        self.assertIn('uses: actions/deploy-pages@v4', WORKFLOW)
        self.assertIn('          path: site\n', WORKFLOW)
        self.assertIn("      - 'relevance_reviews.json'", WORKFLOW)

    def test_news_and_review_state_survive_fresh_checkout(self):
        block = WORKFLOW.split('      - name: Save data and failure health records\n        run: |\n', 1)[1].split('      - name:', 1)[0]
        script = '\n'.join(line[10:] for line in block.rstrip().splitlines())
        def git(*args, cwd):
            return subprocess.run(['git', *args], cwd=cwd, check=True, capture_output=True)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            remote, writer, reader = [root / x for x in ('remote.git', 'writer', 'reader')]
            git('init', '--bare', str(remote), cwd=root)
            git('init', '-b', 'main', str(writer), cwd=root)
            git('config', 'user.name', 'Workflow Test', cwd=writer)
            git('config', 'user.email', '41898282+github-actions[bot]@users.noreply.github.com', cwd=writer)
            (writer / 'site/data').mkdir(parents=True)
            (writer / 'site/index.html').write_text('TOURISM PULSE')
            for name in ('archive', 'news', 'newsroom', 'filings', 'research', 'briefing', 'health'):
                (writer / f'site/data/{name}.json').write_text(json.dumps({'retained': name}))
            git('add', 'site', cwd=writer)
            git('commit', '-m', 'Seed', cwd=writer)
            git('remote', 'add', 'origin', str(remote), cwd=writer)
            git('push', '-u', 'origin', 'main', cwd=writer)
            (writer / 'collector_state').mkdir()
            for name in ('review_queue', 'legacy_archive', 'decisions', 'discovery', 'source_metrics', 'run_summary', 'v02_snapshot'):
                (writer / f'collector_state/{name}.json').write_text(json.dumps({'state': name}))
            (writer / 'site/data/health.json').write_text(json.dumps({'status': 'failed'}))
            subprocess.run(['bash', '-e', '-c', script], cwd=writer, check=True, capture_output=True)
            git('clone', '-b', 'main', str(remote), str(reader), cwd=root)
            for path in list((writer / 'site').rglob('*')) + list((writer / 'collector_state').glob('*.json')):
                if path.is_file():
                    self.assertEqual(path.read_bytes(), (reader / path.relative_to(writer)).read_bytes())
            self.assertFalse((reader / 'site/collector_state').exists())
