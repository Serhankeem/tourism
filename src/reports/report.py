"""Render Research collection telemetry without report contents or secrets."""
import json
from pathlib import Path
from ..collector import ROOT

def render(data):
    lines=['## Research Library v0.4','',f"Checked: {data.get('checked_at','unknown')} · {data.get('status','unknown')}",'','| Metric | Value |','| --- | ---: |']
    for key in ('target_sources','source_coverage','connected_sources','publishing_sources','candidate_reports','verified_reports','published_reports','new_reports_this_run','new_reports_last30d','automatic_reports','manual_reports','duplicate_reports','duplicate_observations'):
        lines.append(f'| {key} | {data.get(key,0)} |')
    lines+=['','| Publisher | Published | Issued last 30d | Latest publication | Last collection | Success rate |','| --- | ---: | ---: | --- | --- | --- |']
    for name,row in data.get('by_publisher',{}).items():
        values=[name,row['published'],row['new_last30d'],row.get('latest_publication') or 'unverified',row.get('last_collection') or 'not attempted',f"{row['success_rate']:.0%}" if row.get('success_rate') is not None else 'not attempted']
        lines.append('| '+' | '.join(str(v).replace('|','/') for v in values)+' |')
    lines+=['','Automatic and manual entries are counted separately. Year/month precision is preserved; registration/modification timestamps are not publication dates. Catalog duplicates and merged report editions are separate metrics.']
    for row in data.get('sources',[]):
        if row['status'] in ('blocked','error','partial'):lines.append(f"- {row['publisher']}: {row['status']} — {row.get('error',row.get('reason','some metadata checks failed'))}")
    return '\n'.join(lines)+'\n'

if __name__=='__main__':
    path=ROOT/'collector_state/reports_run_summary.json'
    print(render(json.loads(path.read_text())) if path.exists() else 'No Research collection telemetry yet.')
