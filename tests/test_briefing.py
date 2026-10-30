"""Artificial metadata only, all writes in temporary directories."""
import copy
import datetime as dt
import json
import tempfile
import unittest
from pathlib import Path
from src.briefing import select,save
from src import collector as c
from src.engine import execute
from test_discovery_v03 import source

AT=dt.datetime(2026,10,30,11,tzinfo=c.KST)
TITLES=['항공 노선 증편 안내','호텔 실적 발표','관광정책 개편 확정','인바운드 시장 조사','여행사 신규 상품','지역관광 지원 사업','OTA 기업 실적']
def article(n=0,**extra):
 return dict(id=str(n),title=TITLES[n],source='테스트',category=['항공·숙박','여행산업','관광정책','인바운드'][n%4],url=f'https://example.org/{n}',published_at=c.iso(AT-dt.timedelta(hours=1)),record_type='news',editorial={'tier':'korea_direct'},**extra)
class BriefingTests(unittest.TestCase):
 def test_counts_and_metadata_only(self):
  for n in [0,1,2,3,4,5,7]:
   with tempfile.TemporaryDirectory() as d:
    p=Path(d);data=save([article(i) for i in range(n)],p,p/'state',AT,c.iso(AT))
    self.assertEqual(len(data['items']),min(n,5))
    for row in data['items']:self.assertEqual(set(row),{'title','source','published_at','url','category','keywords'})
 def test_date_only_unverified_future_old_excluded(self):
  for changes in [dict(date_precision='date'),dict(published_at='2026-10-30'),dict(publication_time_verified_for_news=False),dict(published_at=c.iso(AT+dt.timedelta(minutes=1))),dict(published_at=c.iso(AT-dt.timedelta(hours=25)))]:
   a=article();a.update(changes);self.assertEqual(select([a],AT)[0],[])
 def test_filings_reference_archived_excluded(self):
  for changes in [dict(record_type='regulatory_filing'),dict(record_type='statistics'),dict(archived_only=True),dict(editorial={'tier':'reference'})]:
   a=article();a.update(changes);self.assertEqual(select([a],AT)[0],[])
 def test_duplicate_title_url_and_priority(self):
  a=article();b={**a,'id':'other','url':'https://example.org/other'}
  self.assertEqual(len(select([a,b],AT)[0]),1)
  foreign=article(1);foreign['editorial']={'tier':'global_major'}
  self.assertEqual(select([foreign,a],AT)[0][0]['id'],a['id'])
 def test_category_diversity(self):
  rows=[article(i) for i in range(7)];chosen,_=select(rows,AT)
  self.assertEqual(len({a['category'] for a in chosen[:4]}),4)
 def test_archive_idempotent_and_daily(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d);save([article()],p,p/'state',AT,c.iso(AT));original=(p/'briefing_archive.json').read_bytes()
   save([],p,p/'state',AT+dt.timedelta(hours=1),c.iso(AT));self.assertEqual((p/'briefing_archive.json').read_bytes(),original)
   save([],p,p/'state',AT+dt.timedelta(days=1),c.iso(AT));history=json.loads((p/'briefing_archive.json').read_text())
   self.assertEqual(len(history['briefings']),2);self.assertEqual(history['briefings'][0]['items'][0]['published_at'],article()['published_at'])
 def test_before_schedule_no_history_and_no_fake_past(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d);save([],p,p/'state',AT.replace(hour=9),None);self.assertFalse((p/'briefing_archive.json').exists())
   save([],p,p/'state',AT,None);self.assertEqual(len(json.loads((p/'briefing_archive.json').read_text())['briefings']),1)
 def test_fixture_live_isolation(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d);save([],p,p/'state',AT,None,mode='fixture_demo')
   with self.assertRaises(ValueError):save([],p,p/'state',AT,None,mode='live_rss')
 def test_engine_failure_preserves_all_brief_files(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d);data=p/'public';state=p/'state';data.mkdir();save([article()],data,state,AT,c.iso(AT))
   before={f.name:f.read_bytes() for f in data.glob('brief*.json')}
   def fail(url):raise OSError('synthetic offline')
   execute([source()],data,state,at=AT,loader=fail)
   self.assertEqual(before,{f.name:f.read_bytes() for f in data.glob('brief*.json')})

 def test_corrupt_archive_never_replaced(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d);save([article()],p,p/'state',AT,c.iso(AT))
   current=(p/'briefing.json').read_bytes();(p/'briefing_archive.json').write_text('{broken')
   with self.assertRaises(ValueError):save([],p,p/'state',AT+dt.timedelta(days=1),None)
   self.assertEqual((p/'briefing_archive.json').read_text(),'{broken');self.assertEqual((p/'briefing.json').read_bytes(),current)

 def test_latest_selection_evidence_is_internal_only(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d);state=p/'internal';save([article()],p,state,AT,c.iso(AT))
   evidence=json.loads((state/'briefing_latest_selection.json').read_text())['decisions'][0]
   self.assertEqual(evidence['age_hours'],1);self.assertIn('authorized_newsroom',evidence['basis'])
   self.assertNotIn('decisions',json.loads((p/'briefing.json').read_text()))
