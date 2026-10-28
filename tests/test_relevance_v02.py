import copy
import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from src.collector import article_from_item, run
from src.relevance import CATEGORIES, LEGACY_CATEGORIES, RULE_VERSION, assess, title_digest
from test_collector import AT, SRC, feed

CASES = json.loads((Path(__file__).resolve().parents[1] / 'fixtures/relevance_cases.json').read_text())['cases']


def indirect_item():
    return {'title': '환율 상승으로 방한 수요 감소', 'link': 'https://example.org/indirect',
            'pubDate': AT.isoformat()}


def approval(item):
    aid = hashlib.sha256(item['link'].encode()).hexdigest()[:18]
    return {aid: {'rule_version': RULE_VERSION, 'title_sha256': title_digest(item['title']),
                  'evidence_url': item['link'], 'reviewed_at': AT.isoformat(),
                  'reason': '공식 원문에서 환율 변화가 방한 관광수요에 미치는 영향을 검토했습니다.'}}


class RelevanceV02Tests(unittest.TestCase):
    def test_labeled_counterexamples(self):
        for case in CASES:
            with self.subTest(title=case['title']):
                result = assess(case['title'], case['description'])
                for key in ('label', 'category', 'decision'):
                    self.assertEqual(result[key], case[key])

    def test_indirect_not_in_news_or_briefing_without_approval(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp)
            result = run([SRC], fetcher=lambda _: feed(indirect_item()['title'], link=indirect_item()['link']), at=AT, data_dir=path)
            self.assertEqual(result['articles'], 0)
            self.assertEqual(result['briefing_candidates'], 0)
            queue = json.loads((path / 'collector_state/review_queue.json').read_text())
            self.assertEqual(queue['articles'][0]['relevance_label'], 'Indirect')

    def test_title_bound_approval_publishes_indirect(self):
        item = indirect_item()
        self.assertIsNone(article_from_item(item, SRC, AT))
        article = article_from_item(item, SRC, AT, approval(item))
        self.assertEqual(article['relevance_label'], 'Indirect')
        self.assertEqual(article['relevance_evidence']['review_status'], 'approved')

    def test_stale_title_cannot_reuse_approval(self):
        item = indirect_item()
        reviews = approval(item)
        item['title'] = '환율 하락으로 방한 수요 증가'
        self.assertIsNone(article_from_item(item, SRC, AT, reviews))

    def test_unrelated_evidence_url_cannot_approve(self):
        item = indirect_item()
        reviews = approval(item)
        next(iter(reviews.values()))['evidence_url'] = 'https://unrelated.example/'
        self.assertIsNone(article_from_item(item, SRC, AT, reviews))

    def test_speculation_cannot_be_marked_confirmed(self):
        item = indirect_item()
        item['title'] += ' 가능성'
        self.assertIsNone(article_from_item(item, SRC, AT, approval(item)))

    def test_future_or_malformed_review_cannot_publish(self):
        item = indirect_item()
        for date in ('2030-01-01T00:00:00+09:00', 'not-a-date', ''):
            reviews = approval(item)
            next(iter(reviews.values()))['reviewed_at'] = date
            self.assertIsNone(article_from_item(item, SRC, AT, reviews))

    def test_evidence_never_copies_description(self):
        description = '서울관광재단이 지역관광 사업을 지원한다. 무단 전재하면 안 되는 긴 원문 문장입니다.'
        item = {'title': '지역 상생 프로그램', 'link': 'https://example.org/a', 'pubDate': AT.isoformat(), 'description': description}
        article = article_from_item(item, SRC, AT)
        self.assertNotIn('무단 전재', json.dumps(article, ensure_ascii=False))
        self.assertTrue(article['relevance_evidence']['signals'])

    def test_legacy_migration_preserves_id_and_archives_original(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp)
            run([SRC], fetcher=lambda _: feed('관광정책 발표'), at=AT, data_dir=path)
            old = json.loads((path / 'news.json').read_text())
            old['articles'][0]['category'] = '정책'
            old['articles'][0].pop('relevance_evidence')
            original = copy.deepcopy(old['articles'][0])
            (path / 'news.json').write_text(json.dumps(old))
            run([SRC], fetcher=lambda _: b'<rss><channel/></rss>', at=AT, data_dir=path)
            migrated = json.loads((path / 'news.json').read_text())['articles'][0]
            self.assertEqual(migrated['id'], original['id'])
            self.assertEqual(migrated['url'], original['url'])
            self.assertEqual(migrated['published_at'], original['published_at'])
            self.assertEqual(migrated['category'], '관광정책')
            self.assertEqual(migrated['legacy_category'], '정책')
            archive = json.loads((path / 'collector_state/legacy_archive.json').read_text())
            self.assertEqual(archive['articles'][0], original)

    def test_legacy_unsupported_is_archived_not_silently_published(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp)
            run([SRC], fetcher=lambda _: feed('관광정책 발표'), at=AT, data_dir=path)
            old = json.loads((path / 'news.json').read_text())
            old['articles'][0].update(title='제목만으로 확인할 수 없는 행사 소식', category='지역')
            old['articles'][0].pop('relevance_evidence')
            (path / 'news.json').write_text(json.dumps(old))
            run([SRC], fetcher=lambda _: b'<rss><channel/></rss>', at=AT, data_dir=path)
            self.assertEqual(json.loads((path / 'news.json').read_text())['count'], 0)
            queue = json.loads((path / 'collector_state/review_queue.json').read_text())
            self.assertEqual(queue['articles'][0]['migration_status'], 'needs_refetch')
            self.assertTrue((path / 'collector_state/legacy_archive.json').exists())

    def test_total_failure_does_not_migrate_or_modify_queue(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp)
            run([SRC], fetcher=lambda _: feed(indirect_item()['title']), at=AT, data_dir=path)
            names = ['news.json', 'briefing.json', 'collector_state/review_queue.json', 'collector_state/decisions.json']
            previous = {n: (path / n).read_bytes() for n in names}
            def fail(_):
                raise ValueError('outage')
            run([SRC], fetcher=fail, at=AT, data_dir=path)
            for name, content in previous.items():
                self.assertEqual((path / name).read_bytes(), content)

    def test_queue_approval_works_when_feed_item_rolls_off(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp)
            item = indirect_item()
            run([SRC], fetcher=lambda _: feed(item['title'], link=item['link']), at=AT, data_dir=path)
            run([SRC], fetcher=lambda _: b'<rss><channel/></rss>', at=AT, data_dir=path, reviews=approval(item))
            self.assertEqual(json.loads((path / 'news.json').read_text())['count'], 1)
            self.assertEqual(json.loads((path / 'collector_state/review_queue.json').read_text())['articles'], [])

    def test_revoking_approval_removes_indirect_from_public_news(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp)
            item = indirect_item()
            run([SRC], fetcher=lambda _: feed(item['title'], link=item['link']), at=AT, data_dir=path, reviews=approval(item))
            run([SRC], fetcher=lambda _: b'<rss><channel/></rss>', at=AT, data_dir=path, reviews={})
            self.assertEqual(json.loads((path / 'news.json').read_text())['count'], 0)
            self.assertEqual(len(json.loads((path / 'collector_state/review_queue.json').read_text())['articles']), 1)

    def test_taxonomy_maps_all_six_legacy_categories(self):
        self.assertEqual(set(LEGACY_CATEGORIES), {'정책', '수요', '산업', '리서치', '지역', 'MICE'})
        self.assertTrue(set(LEGACY_CATEGORIES.values()).issubset(CATEGORIES))
        self.assertEqual(len(CATEGORIES), 6)

    def test_existing_sources_remain_and_new_sources_are_metadata_only(self):
        root = Path(__file__).resolve().parents[1]
        sources = json.loads((root / 'sources.json').read_text())['sources']
        self.assertTrue({'mcst_press', 'korea_net_travel', 'kosis_recent', 'seoul_culture'}.issubset({s['id'] for s in sources}))
        self.assertTrue(all(not s['reuse_excerpt'] for s in sources))
        travel=next(s for s in sources if s['id']=='traveltimes')
        self.assertTrue(travel['publication']['noncommercial_only'])
        self.assertEqual(travel['analysis_fields'],['title'])
        self.assertEqual(travel['publication']['scope'],'metadata_only')
        self.assertEqual(travel['publication']['body_reuse'],'not_authorized')

    def test_health_counts_differ_from_published_and_held(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp)
            run([SRC], fetcher=lambda _: feed(indirect_item()['title']), at=AT, data_dir=path)
            health = json.loads((path / 'health.json').read_text())
            self.assertEqual(health['sources'][0]['relevance_counts']['Indirect'], 1)
            self.assertEqual(health['sources'][0]['matched'], 0)
            self.assertEqual(health['sources'][0]['held'], 1)
            self.assertEqual(sum(health['category_counts'].values()), 0)

    def test_refetched_irrelevant_story_is_not_retained_as_direct(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp)
            run([SRC], fetcher=lambda _: feed('관광정책 발표'), at=AT, data_dir=path)
            run([SRC], fetcher=lambda _: feed('주말 여행 가볼 만한 곳'), at=AT, data_dir=path)
            self.assertEqual(json.loads((path / 'news.json').read_text())['count'], 0)

    def test_rejected_article_has_auditable_reason_without_body(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp)
            run([SRC], fetcher=lambda _: feed('일반 은행 실적'), at=AT, data_dir=path)
            audit = json.loads((path / 'collector_state/decisions.json').read_text())['items'][0]
            self.assertEqual(audit['decision'], 'exclude')
            self.assertEqual(audit['relevance_evidence']['label'], 'Irrelevant')
            self.assertTrue(audit['relevance_evidence']['reason'])
            self.assertNotIn('description', audit)


class ConsumerLeisureRegressionTests(unittest.TestCase):
    def test_live_oct28_tea_story_is_not_news_from_wellness_description_alone(self):
        result=assess("족욕하며 차 마시고, '티 오마카세'까지…차에 빠진 MZ세대", '웰니스관광과 웰니스트래블 체험을 소개한다.')
        self.assertEqual(result['decision'], 'exclude')
        self.assertEqual(result['label'], 'Irrelevant')
        industry=assess('웰니스관광 족욕 프로그램 매출 증가', '웰니스관광 체험 소개')
        self.assertEqual(industry['label'], 'Direct')
