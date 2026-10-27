"""Render existing telemetry for GitHub Actions, without credentials or bodies."""
import json
from pathlib import Path


def render(data):
    rows = ['## Tourism News collection', '', 'Checked: ' + data.get('checked_at', 'unknown'), '',
            '| Metric | Value |', '| --- | ---: |']
    for key in ('received', 'new_discoveries', 'duplicate_observations', 'new_auto_published',
                'total_published', 'new_backfilled', 'auto_published_last24h', 'auto_published_last7d',
                'originally_published_last24h', 'originally_published_last7d'):
        rows.append(f'| {key} | {data.get(key, 0)} |')
    rows += ['', 'Outcome: ' + data.get('outcome', 'unknown'), '',
             '| Source | Status | Received | New | Published | Rights holds | Error |',
             '| --- | --- | ---: | ---: | ---: | ---: | --- |']
    for source in data.get('sources', []):
        values = [source.get('id'), source.get('status'), source.get('received', 0),
                  source.get('new_discoveries', 0), source.get('new_auto_published', 0),
                  source.get('rights_holds', 0), source.get('error', '')]
        rows.append('| ' + ' | '.join(str(v).replace('|', '/').replace('\n', ' ') for v in values) + ' |')
    rows += ['', 'Newly added items are NOT necessarily newly issued news. See original publication dates and date precision.']
    return '\n'.join(rows) + '\n'


if __name__ == '__main__':
    path = Path(__file__).resolve().parents[1] / 'site/data/health.json'
    if path.exists():
        data = json.loads(path.read_text()).get('discovery')
        print(render(data) if data else 'No v0.3 telemetry available; inspect collector logs and health.json.')
    else:
        print('No collection health file available; inspect collector logs.')
