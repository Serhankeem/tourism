"""Synthetic test fixtures only. None are seeded into the public report DB."""
import copy
import datetime as dt
import json
import tempfile
import unittest
from pathlib import Path
from src import collector as c
from src.reports import engine
from src.reports.adapters import verify
from src.reports.model import FIELDS,TYPES,CATEGORIES,parse_date,classify
from src.reports.transport import CatalogLoader
from src.discovery import AccessBlocked

AT=dt.datetime(2026,10,29,12,tzinfo=c.KST)
CATALOG='https://reports.example/publications/'
URL='https://reports.example/reports/airport-study/'
TITLE='Air transport market outlook 2026'

def source(**kwargs):
    return {'id':'example','name':'Synthetic Test Institute','region':'해외','adapter':'etc','enabled':True,
            'homepage':'https://reports.example/','allowed_hosts':['reports.example'],'catalog_urls':[CATALOG],
            'max_catalog_pages':1,'max_details':20,'interval_days':7,'lookback_months':24,
            'publication':{'status':'approved','scope':'bibliographic_metadata_only','basis':'Synthetic fixture metadata permission','terms_url':'https://reports.example/terms'},**kwargs}

def catalog(urls=(URL,)):
    return ('<html>'+''.join('<h3><a href="'+u+'">'+TITLE+'</a></h3>' for u in urls)+'</html>').encode()

def landing(title=TITLE,date='2026-10-01',free=True):
    date_tag='' if date is None else '<meta property="article:published_time" content="'+date+'">'
    return ('<html><head><meta property="og:title" content="'+title+'">'+date_tag+'</head><body><h1>'+title+'</h1><p>PROTECTED_REPORT_BODY_NEVER_STORE</p><img src="cover.jpg">'+('<a href="https://reports.example/private.pdf">Download</a>' if free else '')+'</body></html>').encode()

def loader_for(mapping, calls=None):
    def load(url,form=None):
        if calls is not None:calls.append((url,form))
        result=mapping[url]
        if isinstance(result,Exception):raise result
        return result
    return lambda source:load

class ReportsTests(unittest.TestCase):
    def run_collect(self,root,mapping,at=AT,**kw):
        return engine.collect([source()],root/'data',root/'state',at=at,loader_factory=loader_for(mapping),**kw)

    def test_eight_public_fields_and_no_protected_content_or_binary_requests(self):
        calls=[]
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            s=engine.collect([source()],root/'data',root/'state',at=AT,loader_factory=loader_for({CATALOG:catalog(),URL:landing()},calls))
            record=json.loads((root/'data/reports.json').read_text())['reports'][0]
            self.assertEqual(set(record),set(FIELDS));self.assertEqual(record['title'],TITLE)
            self.assertEqual(s['published_reports'],1);self.assertEqual(s['new_reports_last30d'],1)
            self.assertEqual([x[0] for x in calls],[CATALOG,URL])
            for p in root.rglob('*.json'):
                self.assertNotIn('PROTECTED_REPORT_BODY',p.read_text());self.assertNotIn('cover.jpg',p.read_text())

    def test_repeated_execution_does_not_add_or_reset_first_discovery(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);mapping={CATALOG:catalog(),URL:landing()}
            self.run_collect(root,mapping)
            first=json.loads((root/'state/reports_archive.json').read_text())['reports'][0]
            s=self.run_collect(root,mapping,at=AT+dt.timedelta(hours=2),force=True)
            after=json.loads((root/'state/reports_archive.json').read_text())['reports'][0]
            self.assertEqual(s['new_reports_this_run'],0);self.assertEqual(s['published_reports'],1)
            self.assertEqual(first['first_discovered_at'],after['first_discovered_at'])
            self.assertEqual(first['id'],after['id'])

    def test_repost_aliases_merge_without_primary_link_or_access_flapping(self):
        other='https://reports.example/reports/repost/'
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);mapping={CATALOG:catalog((URL,other)),URL:landing(),other:landing(free=False)}
            s=self.run_collect(root,mapping)
            self.assertEqual(s['published_reports'],1);self.assertEqual(s['duplicate_reports'],1)
            s=self.run_collect(root,mapping,force=True)
            record=json.loads((root/'state/reports_archive.json').read_text())['reports'][0]
            self.assertEqual(record['url'],URL);self.assertEqual(record['access_type'],'무료 공개')
            self.assertEqual(s['new_reports_this_run'],0)
            self.assertEqual(set(record['aliases']),{URL,other});self.assertEqual(record['versions'],[])

    def test_quarter_editions_not_merged(self):
        second='https://reports.example/reports/q2/'
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            s=self.run_collect(root,{CATALOG:catalog((URL,second)),URL:landing('European Tourism Q1/2026'),second:landing('European Tourism Q2/2026')})
            self.assertEqual(s['published_reports'],2)

    def test_all_failure_preserves_archive_and_public_bytes(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);self.run_collect(root,{CATALOG:catalog(),URL:landing()})
            paths=[root/'data/reports.json',root/'state/reports_archive.json'];before={p:p.read_bytes() for p in paths}
            s=self.run_collect(root,{CATALOG:OSError('test source outage')},force=True)
            self.assertEqual(s['status'],'failed')
            for p,b in before.items():self.assertEqual(p.read_bytes(),b)
            self.assertEqual(s['by_publisher'][source()['name']]['success_rate'],.5)

    def test_one_failed_detail_retains_old_report(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);self.run_collect(root,{CATALOG:catalog(),URL:landing()})
            s=self.run_collect(root,{CATALOG:catalog(),URL:OSError('failed detail')},force=True)
            self.assertEqual(s['status'],'partial');self.assertEqual(s['published_reports'],1)
            self.assertEqual(s['new_reports_this_run'],0)

    def test_corrupt_archive_never_falls_back_to_public_view(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);self.run_collect(root,{CATALOG:catalog(),URL:landing()})
            public=(root/'data/reports.json').read_bytes();(root/'state/reports_archive.json').write_text('INVALID')
            with self.assertRaises(ValueError):self.run_collect(root,{CATALOG:catalog(),URL:landing()})
            self.assertEqual((root/'data/reports.json').read_bytes(),public)

    def test_missing_archive_does_not_silently_recreate_nonempty_public_db(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);c.write_atomic(root/'data/reports.json',{'count':1,'reports':[{'title':'Synthetic'}]})
            with self.assertRaises(ValueError):self.run_collect(root,{CATALOG:catalog(),URL:landing()})

    def test_year_and_month_are_not_invented_january_first_dates(self):
        self.assertEqual(parse_date('2025',AT.date())[0:2],('2025','year'))
        self.assertEqual(parse_date('2026-10',AT.date())[0:2],('2026-10','month'))
        for value in ('unknown','2027-01-01','2026-02-30','2026-11'):
            with self.assertRaises(ValueError):parse_date(value,AT.date())

    def test_missing_date_does_not_become_today(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);s=self.run_collect(root,{CATALOG:catalog(),URL:landing(date=None)})
            self.assertEqual(s['published_reports'],0);self.assertEqual(s['verified_reports'],0)

    def test_official_publication_year_is_distinct_from_written_date(self):
        src=source(id='kcti',adapter='kcti')
        item={'title':'Synthetic policy study','url':URL,'provider_id':'1'}
        payload=b'<h3>Synthetic policy study</h3><dl><dt>\xeb\xb0\x9c\xea\xb0\x84\xeb\x85\x84\xeb\x8f\x84</dt><dd>2025</dd><dt>\xec\x9e\x91\xec\x84\xb1\xec\x9d\xbc</dt><dd>2026-01-12</dd></dl><img src="new_img_opencode4.jpg">'
        metadata=verify(src,item,payload)
        self.assertEqual(metadata['published_at'],'2025');self.assertEqual(metadata['kogl_type'],4)

    def test_blocked_sources_and_force_never_bypass_permissions(self):
        blocked=source(enabled=False)
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            def forbidden(src):raise AssertionError('Blocked source must not be accessed')
            s=engine.collect([blocked],root/'data',root/'state',at=AT,force=True,loader_factory=forbidden)
            self.assertEqual(s['sources'][0]['status'],'blocked');self.assertEqual(s['published_reports'],0)

    def test_weekly_due_dates_tolerate_scheduler_jitter(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);mapping={CATALOG:catalog(),URL:landing()};self.run_collect(root,mapping)
            skipped=self.run_collect(root,{},at=AT+dt.timedelta(days=1))
            self.assertEqual(skipped['sources'][0]['status'],'not_due')
            monday=self.run_collect(root,mapping,at=AT+dt.timedelta(days=4))
            self.assertEqual(monday['sources'][0]['status'],'ok')
            due=self.run_collect(root,mapping,at=AT+dt.timedelta(days=7,minutes=-10),force=True)
            self.assertEqual(due['sources'][0]['status'],'ok')

    def test_ordinary_promotion_event_and_hiring_not_report(self):
        for title in ('채용 안내','행사 안내: 학술대회','Press release: Corporate launch','Webinar registration'):
            self.assertIsNone(classify(title,source(),{'url':URL}))
        result=classify('Hotel market outlook 2026',source(),{'url':URL})
        self.assertEqual(result['category'],'숙박·호텔산업');self.assertIn(result['report_type'],TYPES)

    def test_binary_and_unapproved_hosts_are_never_requested(self):
        loader=CatalogLoader(['reports.example'])
        for url in ('https://reports.example/report.pdf','https://elsewhere.example/catalog','http://reports.example/catalog'):
            with self.assertRaises(AccessBlocked):loader(url)

    def test_catalog_form_endpoint_is_explicitly_allowlisted(self):
        loader=CatalogLoader(['reports.example'])
        with self.assertRaises(AccessBlocked):loader('https://reports.example/admin',form={'x':'y'})

    def test_existing_news_stats_filing_and_archive_files_untouched(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            paths=[root/'data'/f'{n}.json' for n in ('news','newsroom','briefing','research','filings')]+[root/'state/archive.json']
            for p in paths:c.write_atomic(p,{'original':p.name})
            before={p:p.read_bytes() for p in paths};self.run_collect(root,{CATALOG:catalog(),URL:landing()})
            for p,b in before.items():self.assertEqual(p.read_bytes(),b)

    def test_manual_registration_is_separate_and_requires_evidence(self):
        src=source(enabled=False)
        manual={'source_id':src['id'],'title':TITLE,'publisher':src['name'],'published_at':'2026-10-01',
                'report_type':TYPES[0],'category':CATEGORIES[3],'keywords':['air transport'],'url':URL,
                'access_type':'미확인','verified_by':'Synthetic operator','verification_note':'Synthetic original metadata checked','evidence_url':URL}
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            s=engine.collect([src],root/'data',root/'state',at=AT,manual=[manual])
            self.assertEqual(s['automatic_reports'],0);self.assertEqual(s['manual_reports'],1)
            self.assertEqual(s['verified_manual_reports'],1)
            s=engine.collect([src],root/'data',root/'state',at=AT,manual=[manual])
            self.assertEqual(s['new_reports_this_run'],0)
            invalid={k:v for k,v in manual.items() if k!='verification_note'}
            with self.assertRaises(ValueError):engine.collect([src],root/'data',root/'state',at=AT,manual=[invalid])

    def test_coarse_publication_year_not_counted_as_recent_thirty_days(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);s=self.run_collect(root,{CATALOG:catalog(),URL:landing(date='2025')})
            self.assertEqual(s['published_reports'],1);self.assertEqual(s['new_reports_last30d'],0)
            record=json.loads((root/'data/reports.json').read_text())['reports'][0]
            self.assertEqual(record['published_at'],'2025')

    def test_registration_date_is_not_silently_relabelled_publication(self):
        src=source(id='yanolja',adapter='yanolja',allow_registered_date=False)
        url='https://reports.example/trend/view/1?lang=kr'
        listing=b'<script>let lists = [{"RESEARCH_IDX":"1","TITLE":"Synthetic hotel report","INS_DATE":"2026.10.01"}];</script><a href="'+url.encode()+b'">Synthetic hotel report</a>'
        detail=b'<h3 class="title">Synthetic hotel report</h3><dl><dt>\xeb\x93\xb1\xeb\xa1\x9d\xec\x9d\xbc</dt><dd>2026.10.01</dd></dl>'
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            s=engine.collect([src],root/'data',root/'state',at=AT,loader_factory=loader_for({CATALOG:listing,url:detail}))
            self.assertEqual(s['published_reports'],0);self.assertEqual(s['sources'][0]['date_holds'],1)
            src['allow_registered_date']=True
            s=engine.collect([src],root/'data',root/'state',at=AT,force=True,loader_factory=loader_for({CATALOG:listing,url:detail}))
            self.assertEqual(s['published_reports'],1)
            self.assertEqual(s['new_reports_last30d'],0)  # registration != publication
            self.assertIsNone(s['by_publisher'][src['name']]['latest_publication'])
            self.assertEqual(s['by_publisher'][src['name']]['latest_registration'],'2026-10-01')
            public=json.loads((root/'data/reports.json').read_text())
            self.assertEqual(public['date_basis'][url]['kind'],'registered')

    def test_ko_gl_scope_removal_holds_publication_without_deleting_record(self):
        src=source(id='kcti',adapter='kcti',detail_url='https://reports.example/detail')
        url='https://reports.example/detail?board_id=2&contents_id=abc'
        listing=b'<ul><li><a class="thumbnaillist_txt" href="javascript:contentsView(\'abc\')"><h4>Synthetic policy study</h4></a></li></ul>'
        detail=b'<h3>Synthetic policy study</h3><dl><dt>\xeb\xb0\x9c\xea\xb0\x84\xeb\x85\x84\xeb\x8f\x84</dt><dd>2025</dd></dl>'
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            s=engine.collect([src],root/'data',root/'state',at=AT,loader_factory=loader_for({CATALOG:listing,url:detail+b'<img src="new_img_opencode4.jpg">'}))
            self.assertEqual(s['published_reports'],1)
            s=engine.collect([src],root/'data',root/'state',at=AT,force=True,loader_factory=loader_for({CATALOG:listing,url:detail}))
            self.assertEqual(s['published_reports'],0);self.assertEqual(s['archived_reports'],1)
            saved=json.loads((root/'state/reports_archive.json').read_text())['reports'][0]
            self.assertEqual(saved['publication_status'],'rights_review_required')

    def test_manual_and_automatic_updates_preserve_original_discovery_route(self):
        manual={'source_id':'example','title':TITLE,'publisher':source()['name'],'published_at':'2026-10-01',
                'report_type':TYPES[0],'category':CATEGORIES[3],'keywords':['air transport'],'url':URL,
                'access_type':'미확인','verified_by':'Synthetic operator','verification_note':'Original metadata checked','evidence_url':URL}
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            engine.collect([source(enabled=False)],root/'data',root/'state',at=AT,manual=[manual])
            result=self.run_collect(root,{CATALOG:catalog(),URL:landing()},force=True)
            self.assertEqual(result['manual_reports'],1);self.assertEqual(result['automatic_reports'],0)
            self.assertEqual(result['verified_reports'],1)
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);self.run_collect(root,{CATALOG:catalog(),URL:landing()})
            modified={**manual,'title':TITLE+' (metadata correction)'}
            result=engine.collect([source()],root/'data',root/'state',at=AT,manual=[modified])
            self.assertEqual(result['manual_reports'],0);self.assertEqual(result['automatic_reports'],1)
            self.assertEqual(result['new_reports_this_run'],0);self.assertEqual(result['verified_reports'],1)
            record=json.loads((root/'state/reports_archive.json').read_text())['reports'][0]
            self.assertEqual(record['versions'][-1]['metadata']['title'],TITLE)

    def test_http_200_challenge_is_failure_not_a_normal_empty_catalog(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);self.run_collect(root,{CATALOG:catalog(),URL:landing()})
            before=(root/'data/reports.json').read_bytes()
            result=self.run_collect(root,{CATALOG:b'<html><h1>Access denied</h1>Challenge</html>'},force=True)
            self.assertEqual(result['status'],'failed')
            self.assertIn('catalog_schema_missing',result['sources'][0]['error'])
            self.assertEqual((root/'data/reports.json').read_bytes(),before)

    def test_explicit_empty_catalog_does_not_erase_existing_reports(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);self.run_collect(root,{CATALOG:catalog(),URL:landing()})
            result=self.run_collect(root,{CATALOG:b'<div class="js-wpv-loop"></div>'},force=True)
            self.assertEqual(result['status'],'ok');self.assertEqual(result['candidates_this_run'],0)
            self.assertEqual(result['new_reports_this_run'],0);self.assertEqual(result['published_reports'],1)
