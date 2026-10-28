import datetime as dt
import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from urllib.error import HTTPError
from urllib.robotparser import RobotFileParser

from src import collector as c
from src.discovery import AccessBlocked, Loader, items_from
from src.engine import execute, permission
from src.relevance import assess
from test_collector import AT, SRC, feed


POLICY = {'status': 'approved', 'scope': 'metadata_only', 'terms_url': 'https://example.org/terms', 'basis': 'Test fixture permission'}


def source(**kwargs):
    return {**SRC, 'publication': dict(POLICY), 'analysis_fields': ['title'], **kwargs}


class DiscoveryV03Tests(unittest.TestCase):
    def test_missing_permission_cannot_publish_direct(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            summary = execute([source(publication={'status': 'review'})], root/'site', root/'state', at=AT, loader=lambda _: feed('국제선 항공노선 확대'))
            self.assertEqual(summary['new_auto_published'], 0)
            candidate = next(iter(json.loads((root/'state/discovery.json').read_text())['candidates'].values()))
            self.assertEqual(candidate['relevance_evidence']['label'], 'Direct')
            self.assertEqual(candidate['publication_status'], 'rights_hold')
            self.assertIsNone(candidate['title'])
            self.assertTrue(candidate['title_sha256'])

    def test_permission_requires_evidence_scope_and_url(self):
        for missing in ('status', 'scope', 'terms_url', 'basis'):
            s = source();s['publication'].pop(missing)
            self.assertFalse(permission(s))

    def test_no_daily_editor_required_for_licensed_direct(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            summary = execute([source()], root/'site', root/'state', at=AT, loader=lambda _: feed('국제선 항공노선 확대'))
            self.assertEqual(summary['new_auto_published'], 1)
            self.assertEqual(summary['total_published'], 1)

    def test_second_run_does_not_recount_publication_or_reset_discovery(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            first = execute([source()], root/'site', root/'state', at=AT, loader=lambda _: feed('국제선 항공노선 확대'))
            old = json.loads((root/'state/archive.json').read_text())['articles'][0]
            later = AT + dt.timedelta(hours=2)
            second = execute([source()], root/'site', root/'state', at=later, loader=lambda _: feed('국제선 항공노선 확대'))
            article = json.loads((root/'state/archive.json').read_text())['articles'][0]
            self.assertEqual(first['new_auto_published'], 1)
            self.assertEqual(second['new_auto_published'], 0)
            self.assertEqual(second['new_discoveries'], 0)
            self.assertEqual(second['duplicate_observations'], 1)
            self.assertEqual(article['first_discovered_at'], old['first_discovered_at'])
            self.assertEqual(article['first_published_by_engine_at'], old['first_published_by_engine_at'])

    def test_atom_modified_is_not_publication(self):
        payload = b'<feed xmlns="http://www.w3.org/2005/Atom"><entry><title>Airline revenue grows</title><link href="https://example.org/a"/><updated>2026-10-25T10:00:00+09:00</updated></entry></feed>'
        item = list(items_from(source(), payload))[0]
        self.assertNotIn('published', item)
        self.assertIn('modified_at', item)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            summary = execute([source()], root/'site', root/'state', at=AT, loader=lambda _: payload)
            self.assertEqual(summary['new_auto_published'], 0)

    def test_gdelt_seen_is_not_publication(self):
        payload = json.dumps({'articles': [{'title': 'Airline revenue grows', 'url': 'https://example.org/a', 'seendate': '20261025T100000Z'}]}).encode()
        item = list(items_from(source(adapter='gdelt'), payload))[0]
        self.assertEqual(item['published'], '')
        self.assertEqual(item['discovered_by_provider_at'], '20261025T100000Z')

    def test_backfill_preserves_original_date_and_is_not_daily_briefing(self):
        pub = (AT - dt.timedelta(days=65)).isoformat()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            summary = execute([source()], root/'site', root/'state', at=AT, loader=lambda _: feed('관광정책 발표', pub=pub))
            article = json.loads((root/'state/archive.json').read_text())['articles'][0]
            self.assertEqual(article['published_at'], pub)
            self.assertTrue(article['is_backfill'])
            self.assertEqual(summary['new_backfilled'], 1)
            self.assertEqual(summary['originally_published_last24h'], 0)
            self.assertEqual(json.loads((root/'site/briefing.json').read_text())['items'], [])

    def test_backfill_does_not_ingest_unprovided_or_over_90_day_articles(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            summary = execute([source()], root/'site', root/'state', at=AT, loader=lambda _: feed('관광정책 발표', pub=(AT-dt.timedelta(days=91)).isoformat()))
            self.assertEqual(summary['new_auto_published'], 0)
            self.assertEqual(summary['new_discoveries'], 0)
            self.assertEqual(summary['sources'][0]['outside_window'], 1)

    def test_all_failure_preserves_public_files_and_reports_failure(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            execute([source()], root/'site', root/'state', at=AT, loader=lambda _: feed('관광정책 발표'))
            previous = {n:(root/'site'/n).read_bytes() for n in ('news.json','briefing.json')}
            def fail(_): raise AccessBlocked('robots_disallowed')
            summary = execute([source()], root/'site', root/'state', at=AT, loader=fail)
            self.assertEqual(summary['outcome'], 'all_fetches_failed')
            for name, data in previous.items():self.assertEqual((root/'site'/name).read_bytes(), data)
            self.assertEqual(summary['sources'][0]['success_rate'], 0.5)

    def test_empty_success_differs_from_failed_fetch(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            summary = execute([source()], root/'site', root/'state', at=AT, loader=lambda _: b'<rss><channel/></rss>')
            self.assertEqual(summary['outcome'], 'no_new_publications')
            self.assertEqual(summary['sources'][0]['outcome'], 'no_new_candidate')

    def test_duplicate_sources_deduplicate_canonical_url(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            summary = execute([source(), source(id='two', url='https://example.org/feed2')], root/'site', root/'state', at=AT, loader=lambda _: feed('관광정책 발표'))
            self.assertEqual(summary['new_auto_published'], 1)
            self.assertEqual(summary['new_discoveries'], 1)
            self.assertEqual(summary['duplicate_observations'], 1)

    def test_sec_adapter_uses_filing_date_not_fetch_date_and_never_fetches_body(self):
        data = {'cik': 123, 'name': 'Booking Holdings', 'filings': {'recent': {'form':['10-Q','4'], 'filingDate':['2026-08-20','2026-10-25'], 'accessionNumber':['000123-26-000001','000123-26-000002'], 'primaryDocument':['report.htm','personal.xml']}}}
        items = list(items_from(source(adapter='sec_submissions', cik='123'), json.dumps(data).encode()))
        self.assertEqual(len(items),1)
        self.assertEqual(items[0]['published'],'2026-08-20')
        self.assertEqual(items[0]['record_type'],'regulatory_filing')
        self.assertNotIn('description',items[0])

    def test_sec_identity_mismatch_fails(self):
        with self.assertRaises(ValueError):
            list(items_from(source(adapter='sec_submissions',cik='999'), b'{"cik":123}'))

    def test_civil_date_disclosure_is_excluded_from_intraday_briefing(self):
        data = {'cik':123,'name':'Booking Holdings','filings':{'recent':{'form':['10-Q'],'filingDate':['2026-10-25'],'accessionNumber':['000123-26-000001'],'primaryDocument':['report.htm']}}}
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            execute([source(adapter='sec_submissions',cik='123')],root/'site',root/'state',at=AT,loader=lambda _:json.dumps(data).encode())
            self.assertEqual(json.loads((root/'site/briefing.json').read_text())['items'],[])

    def test_english_industry_requires_change_not_company_name(self):
        for title, expected in [('Booking Holdings financial filing','Direct'),('Hotel revenue increases','Direct'),('Airline opens new route to Seoul','Direct'),('Booking Holdings company profile','Irrelevant'),('New album at a city festival','Irrelevant'),('Oil prices affect travel demand','Indirect')]:
            with self.subTest(title=title): self.assertEqual(assess(title)['label'],expected)

    def test_robots_disallow_never_fetches_target(self):
        loader=Loader();p=RobotFileParser();p.parse(['User-agent: *','Disallow: /private'])
        loader.rules['https://example.org']=p
        with patch.object(loader.opener,'open') as request:
            with self.assertRaises(AccessBlocked):loader('https://example.org/private')
            request.assert_not_called()

    def test_unknown_robots_is_not_bypassed(self):
        loader=Loader();loader.rules['https://example.org']=None
        with patch.object(loader.opener,'open') as request:
            with self.assertRaises(AccessBlocked):loader('https://example.org/feed')
            request.assert_not_called()

    def test_redirect_rechecks_target_robots(self):
        loader=Loader();allow=RobotFileParser();allow.parse([]);deny=RobotFileParser();deny.parse(['User-agent: *','Disallow: /'])
        loader.rules.update({'https://example.org':allow,'https://blocked.example':deny})
        error=HTTPError('https://example.org/feed',302,'Found',{'Location':'https://blocked.example/feed'},None)
        with patch.object(loader.opener,'open',side_effect=error) as request:
            with self.assertRaises(AccessBlocked):loader('https://example.org/feed')
            self.assertEqual(request.call_count,1)

    def test_no_description_persisted_for_rights_uncertain_discovery(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            payload=b'<rss><channel><item><title>Airline revenue grows</title><link>https://example.org/a</link><pubDate>2026-10-25T10:00:00+09:00</pubDate><description>Protected full article body must not be saved</description></item></channel></rss>'
            execute([source(publication={'status':'review'})],root/'site',root/'state',at=AT,loader=lambda _:payload)
            self.assertNotIn('Protected full article', (root/'state/discovery.json').read_text())

    def test_govuk_uses_first_published_not_updated_and_caches_it(self):
        payload = json.dumps({'results':[{'format':'press_release','title':'Airline launches new route to Seoul','link':'/government/news/test','public_timestamp':AT.isoformat()}]}).encode()
        calls=[]
        def load(url):
            calls.append(url)
            if '/api/content/' in url:
                return json.dumps({'first_published_at':(AT-dt.timedelta(days=30)).isoformat(),'public_updated_at':AT.isoformat(),'details':{'body':'PROTECTED FULL BODY NOT TO STORE'}}).encode()
            return payload
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            src=source(adapter='govuk_search',url='https://www.gov.uk/api/search.json?q=aviation')
            execute([src],root/'site',root/'state',at=AT,loader=load)
            article=json.loads((root/'state/archive.json').read_text())['articles'][0]
            self.assertEqual(article['published_at'],(AT-dt.timedelta(days=30)).isoformat())
            self.assertNotIn('PROTECTED FULL BODY', (root/'state/discovery.json').read_text())
            self.assertNotIn('PROTECTED FULL BODY', (root/'site/news.json').read_text())
            execute([src],root/'site',root/'state',at=AT+dt.timedelta(hours=2),loader=load)
            self.assertEqual(sum('/api/content/' in u for u in calls),1)

    def test_existing_v02_database_has_immutable_snapshot(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);(root/'site').mkdir()
            old=c.article_from_item({'title':'관광정책 발표','link':'https://example.org/old','pubDate':AT.isoformat()},SRC,AT)
            original={'schema_version':2,'mode':'live_rss','articles':[old],'count':1}
            c.write_atomic(root/'site/news.json',original)
            execute([source()],root/'site',root/'state',at=AT,loader=lambda _:feed('국제선 운항 확대',link='https://example.org/new'))
            self.assertEqual(json.loads((root/'state/v02_snapshot.json').read_text()),original)
            articles=json.loads((root/'state/archive.json').read_text())['articles']
            self.assertTrue({old['id']}.issubset({a['id'] for a in articles}))

    def test_indirect_cannot_bypass_existing_approval(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            summary=execute([source()],root/'site',root/'state',at=AT,loader=lambda _:feed('환율 상승으로 방한 수요 감소'))
            self.assertEqual(summary['new_auto_published'],0)
            self.assertEqual(json.loads((root/'site/briefing.json').read_text())['items'],[])

    def test_global_briefing_prioritizes_explicit_korea_relevance(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            one=feed('Airline opens new route to Seoul',link='https://example.org/korea').split(b'<channel>')[1].split(b'</channel>')[0]
            two=feed('Airline revenue increases',link='https://example.org/global').split(b'<channel>')[1].split(b'</channel>')[0]
            payload=b'<rss><channel>'+two+one+b'</channel></rss>'
            execute([source()],root/'site',root/'state',at=AT,loader=lambda _:payload)
            self.assertIn('Seoul',json.loads((root/'site/briefing.json').read_text())['items'][0]['title'])

    def test_rendered_monitoring_separates_newly_added_from_newly_issued(self):
        from src.report import render
        result=render({'new_auto_published':5,'originally_published_last24h':0,'outcome':'new_articles_published'})
        self.assertIn('| new_auto_published | 5 |',result)
        self.assertIn('| originally_published_last24h | 0 |',result)
        self.assertIn('NOT necessarily newly issued',result)

    def test_generic_aviation_careers_do_not_inflate_industry_news(self):
        self.assertEqual(assess('Funding to launch aviation careers for school students')['label'],'Irrelevant')
        self.assertEqual(assess('Gatwick to open second runway after government decision')['label'],'Direct')

    def test_private_financial_results_are_direct_but_still_rights_blocked(self):
        title='Trip.com Group Reports Unaudited Quarterly Financial Results'
        self.assertEqual(assess(title)['label'],'Direct')
        self.assertEqual(assess('Hilton introduces employee birthday parties')['label'],'Irrelevant')
        self.assertEqual(assess('Hotel launches discount coupons')['label'],'Irrelevant')
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            summary=execute([source(publication={'status':'review'})],root/'site',root/'state',at=AT,loader=lambda _:feed(title))
            self.assertEqual(summary['new_auto_published'],0)
            self.assertEqual(summary['sources'][0]['rights_holds'],1)

    def test_different_numeric_facts_are_not_fuzzy_merged(self):
        item={'title':'호텔업 객실 매출 25% 증가 발표','link':'https://example.org/a','pubDate':AT.isoformat()}
        one=c.article_from_item(item,SRC,AT)
        two=c.article_from_item({**item,'title':'호텔업 객실 매출 35% 증가 발표','link':'https://example.org/b'},SRC,AT)
        self.assertEqual(len(c.deduplicate([one,two])),2)

    def test_html_challenge_at_robots_does_not_authorize_fetch(self):
        from unittest.mock import MagicMock
        loader=Loader()
        response=MagicMock();response.__enter__.return_value.read.return_value=b'<!doctype html><html>Access denied</html>'
        with patch('urllib.request.urlopen',return_value=response),patch.object(loader.opener,'open') as request:
            with self.assertRaises(AccessBlocked):loader('https://example.org/feed')
            request.assert_not_called()

    def test_named_korean_companies_need_operational_change(self):
        for title,category in [('대한항공 매출 증가','항공·숙박'),('제주항공 국제선 증편','항공·숙박'),('하나투어 영업이익 증가','여행산업'),('야놀자 플랫폼 출시','여행산업')]:
            with self.subTest(title=title):
                self.assertEqual(assess(title)['label'],'Direct')
                self.assertEqual(assess(title)['category'],category)
        self.assertEqual(assess('하나투어 직원 생일행사')['label'],'Irrelevant')

    def test_utc_publication_keeps_the_correct_korean_calendar_date(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            execute([source()],root/'site',root/'state',at=AT,loader=lambda _:feed('국제선 운항 확대',pub='2026-10-24T22:30:00Z'))
            article=json.loads((root/'state/archive.json').read_text())['articles'][0]
            self.assertEqual(article['published_at'],'2026-10-25T07:30:00+09:00')
            self.assertEqual(article['date'],'2026.10.25')

    def test_redirect_loop_stops_without_repeating_same_request(self):
        loader=Loader();allow=RobotFileParser();allow.parse([]);loader.rules['https://example.org']=allow
        error=HTTPError('https://example.org/feed',302,'Found',{'Location':'https://example.org/feed'},None)
        with patch.object(loader.opener,'open',side_effect=error) as request:
            with self.assertRaises(AccessBlocked):loader('https://example.org/feed')
            self.assertEqual(request.call_count,1)
