import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from src import collector as c
from src import engine
from src.engine import execute, permission
from src.publication import PUBLIC_FIELDS, public_record
from test_discovery_v03 import source
from test_collector import AT, SRC, feed


class LinkCurationTests(unittest.TestCase):
    def test_only_six_fields_and_title_keywords_survive(self):
        article=c.article_from_item({'title':'대한항공 매출 증가','link':'https://example.org/a','pubDate':AT.isoformat()},SRC,AT)
        article.update(desc='DO NOT PUBLISH EXCERPT',insight='DO NOT PUBLISH AI SUMMARY',photo='image.jpg',thumbnail='thumb.jpg',body='PROTECTED BODY',keywords=['UNTRUSTED PROVIDER SUMMARY'])
        public=public_record(article)
        self.assertEqual(set(public),set(PUBLIC_FIELDS))
        self.assertEqual(public['title'],article['title'])
        self.assertIn('대한항공',public['keywords'])
        self.assertNotIn('DO NOT PUBLISH',json.dumps(public))
        self.assertNotIn('UNTRUSTED',json.dumps(public))

    def test_full_archive_moves_outside_pages_and_second_run_retains_metadata(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            execute([source()],root/'site',root/'state',at=AT,loader=lambda _:feed('대한항공 매출 증가'))
            self.assertFalse((root/'site/archive.json').exists())
            before=json.loads((root/'state/archive.json').read_text())['articles'][0]
            result=execute([source()],root/'site',root/'state',at=AT,loader=lambda _:feed('대한항공 매출 증가'))
            after=json.loads((root/'state/archive.json').read_text())['articles'][0]
            self.assertEqual(before['id'],after['id'])
            self.assertEqual(before['first_discovered_at'],after['first_discovered_at'])
            self.assertEqual(result['new_newsroom_items'],0)
            for filename in ('news','newsroom'):
                for article in json.loads((root/'site'/f'{filename}.json').read_text())['articles']:
                    self.assertEqual(set(article),set(PUBLIC_FIELDS))
            for article in json.loads((root/'site/briefing.json').read_text())['items']:
                self.assertEqual(set(article),set(PUBLIC_FIELDS))

    def test_legacy_public_archive_is_preserved_then_removed_from_pages(self):
        old=c.article_from_item({'title':'관광정책 발표','link':'https://example.org/old','pubDate':AT.isoformat()},SRC,AT)
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            c.write_atomic(root/'site/archive.json',{'schema_version':3,'mode':'live_rss','articles':[old]})
            execute([source()],root/'site',root/'state',at=AT,loader=lambda _:feed('대한항공 매출 증가'))
            saved=json.loads((root/'state/archive.json').read_text())['articles']
            self.assertIn(old['id'],{a['id'] for a in saved})
            self.assertFalse((root/'site/archive.json').exists())

    def test_public_projection_alone_cannot_silently_replace_lost_archive(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            c.write_atomic(root/'site/news.json',{'mode':'live_rss','articles':[{'title':'x','url':'https://example.org/a'}]})
            with self.assertRaisesRegex(ValueError,'requires_internal_archive'):
                execute([source()],root/'site',root/'state',at=AT,loader=lambda _:feed('관광정책 발표'))

    def test_noncommercial_sources_fail_closed_if_mode_or_ads_change(self):
        src=source();src['publication']['noncommercial_only']=True
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'policy.json'
            with patch.object(engine,'OPERATING_POLICY',path):
                self.assertFalse(permission(src))
                for policy in ({'mode':'commercial','ads_enabled':False,'paid_access':False},
                               {'mode':'noncommercial','ads_enabled':True,'paid_access':False},
                               {'mode':'noncommercial','ads_enabled':False,'paid_access':True}):
                    c.write_atomic(path,policy);self.assertFalse(permission(src))
                c.write_atomic(path,{'mode':'noncommercial','ads_enabled':False,'paid_access':False})
                self.assertTrue(permission(src))

    def test_newsroom_does_not_truncate_original_headline(self):
        title='대한항공 매출 증가 '+('공식 발표 '*60)
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            execute([source()],root/'site',root/'state',at=AT,loader=lambda _:feed(title.strip()))
            actual=json.loads((root/'site/newsroom.json').read_text())['articles'][0]
            self.assertEqual(actual['title'],title.strip())

    def test_source_specific_seven_day_limit_does_not_backfill_entire_feed(self):
        import datetime as dt
        src=source();src['backfill']={'max_days':7}
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            result=execute([src],root/'site',root/'state',at=AT,loader=lambda _:feed('관광정책 발표',pub=(AT-dt.timedelta(days=8)).isoformat()))
            self.assertEqual(result['new_newsroom_items'],0)
            self.assertEqual(result['sources'][0]['outside_window'],1)

    def test_title_only_ota_operating_news_is_distinct_from_promotions(self):
        for title in ('아고다 매출 증가', '트립닷컴 영업이익 증가', '세이버 발권 서비스 출시'):
            self.assertEqual(c.assess(title)['label'],'Direct')
        for title in ('아고다 최저가 추천숙소', '트립닷컴 직원 생일행사', '최저가 일본 여행 상품'):
            self.assertEqual(c.assess(title)['label'],'Irrelevant')

    def test_explicit_inbound_and_quantified_hotel_demand_are_not_generic_travel(self):
        self.assertEqual(c.assess('방한 관광객 역대 최다 기록')['category'],'인바운드')
        self.assertEqual(c.assess('한국인 95% “여가 목적의 1박 호텔 숙박 계획”')['category'],'항공·숙박')
        self.assertEqual(c.assess('여가 목적의 호텔 추천')['label'],'Irrelevant')

    def test_source_metrics_count_news_once_and_not_filings_or_statistics(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            result=execute([source(id='publisher')],root/'site',root/'state',at=AT,loader=lambda _:feed('방한 관광객 역대 최다 기록'))
            self.assertEqual(result['newsroom_by_source']['publisher'],{'count':1,'originally_published_last7d':1,'korea_direct':1,'new_this_run':1})
            self.assertEqual(result['newsroom_korea_direct_last7d'],1)

    def test_corrupt_internal_archive_cannot_fall_back_to_six_field_public_view(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            execute([source()],root/'site',root/'state',at=AT,loader=lambda _:feed('대한항공 매출 증가'))
            (root/'state/archive.json').write_text('INVALID')
            before=(root/'site/news.json').read_bytes()
            with self.assertRaises(ValueError):execute([source()],root/'site',root/'state',at=AT,loader=lambda _:feed('관광정책 발표'))
            self.assertEqual((root/'site/news.json').read_bytes(),before)

    def test_named_domestic_airline_in_b2b_ticketing_title_is_not_generic_brand_mention(self):
        from src.editorial import exposure
        title='세이버, 11월부터 대한항공(KE) 발권 서비스 전격 오픈!'
        self.assertEqual(exposure({'title':title,'relevance_label':'Direct'})['tier'],'korea_direct')
        self.assertEqual(exposure({'title':'대한항공이 언급한 미국 여행시장','relevance_label':'Direct'})['tier'],'reference')

    def test_tourism_organization_marketing_action_needs_all_three_signals(self):
        for title in ('서울관광재단, 일본 2050 세대 남성 겨냥 글로벌 캠페인 추진', '서울관광재단 사계절 관광 설명회 성료'):
            self.assertEqual(c.assess(title)['label'],'Direct')
        for title in ('관광재단 직원 생일행사', '일반 지역 축제 개최', '배우 홍보대사 위촉', '한국관광공사 윤리경영 협약'):
            self.assertEqual(c.assess(title)['label'],'Irrelevant')

    def test_ota_policy_change_is_not_a_consumer_tip_or_a_korea_claim(self):
        from src.editorial import exposure
        title='청소비 냈는데 설거지까지? 에어비앤비 퇴실 규정 바뀐다'
        result=c.assess(title)
        self.assertEqual(result['label'],'Direct')
        self.assertEqual(result['category'],'여행산업')
        self.assertEqual(exposure({'title':title,'relevance_label':'Direct'})['tier'],'reference')
        self.assertEqual(c.assess('에어비앤비 퇴실 규정 후기')['label'],'Irrelevant')
