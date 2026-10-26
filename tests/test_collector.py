import datetime as dt
import json
import tempfile
import unittest
from pathlib import Path
from zoneinfo import ZoneInfo

from src.collector import (
    article_from_item, canonical_url, classify, deduplicate, run,
    similarity, timestamp, xml_items,
)

KST = ZoneInfo('Asia/Seoul')
AT = dt.datetime(2026, 10, 25, 12, 0, tzinfo=KST)
SRC = {'id': 'test', 'name': '시험기관', 'url': 'https://example.org/rss', 'enabled': True, 'reuse_excerpt': False}


def feed(title, pub='Sun, 25 Oct 2026 10:00:00 +0900', link='https://example.org/story'):
    return (f'<rss><channel><item><title>{title}</title><link>{link}</link>'
            f'<pubDate>{pub}</pubDate></item></channel></rss>').encode()


class CollectorTests(unittest.TestCase):
    def test_rss_parser(self):
        a = list(xml_items(feed('관광산업 정책 발표')))
        self.assertEqual(a[0]['title'], '관광산업 정책 발표')

    def test_atom_parser(self):
        x = b'<feed xmlns="http://www.w3.org/2005/Atom"><entry><title>Inbound tourism arrivals</title><link href="https://example.org/x"/><updated>2026-10-25T10:00:00+09:00</updated></entry></feed>'
        self.assertEqual(next(xml_items(x))['link'], 'https://example.org/x')

    def test_tourism_classification(self):
        cat, score = classify('방한 외래관광객 증가 및 관광통계 발표')
        self.assertEqual(cat, '수요')
        self.assertGreaterEqual(score, 4)

    def test_irrelevant_excluded(self):
        self.assertIsNone(classify('배우의 주말 브이로그와 맛집')[0])

    def test_generic_travel_excluded(self):
        self.assertIsNone(classify('주말 여행 가볼 만한 곳')[0])

    def test_url_tracking_removed(self):
        url = canonical_url('https://EXAMPLE.org/path?utm_source=foo&doc=2#fragment')
        self.assertEqual(url, 'https://example.org/path?doc=2')

    def test_unsafe_url_rejected(self):
        self.assertEqual(canonical_url('javascript:alert(1)'), '')

    def test_future_pub_rejected(self):
        data = {'title': '방한 외래관광객 증가', 'link': 'https://example.org/a', 'pubDate': '2030-10-25T10:00:00+09:00'}
        self.assertIsNone(article_from_item(data, SRC, AT))

    def test_missing_date_rejected(self):
        data = {'title': '방한 외래관광객 증가', 'link': 'https://example.org/a'}
        self.assertIsNone(article_from_item(data, SRC, AT))

    def test_old_pub_rejected(self):
        data = {'title': '방한 외래관광객 증가', 'link': 'https://example.org/a', 'pubDate': '2025-10-25T10:00:00+09:00'}
        self.assertIsNone(article_from_item(data, SRC, AT))

    def test_dedup_exact_url(self):
        a = article_from_item({'title': '방한 외래관광객 증가', 'link': 'https://example.org/a', 'pubDate': '2026-10-25T10:00:00+09:00'}, SRC, AT)
        b = dict(a, title='2026년 방한 관광 통계', related_sources=['다른기관'], source='다른기관')
        self.assertEqual(len(deduplicate([a, b])), 1)

    def test_dedup_fuzzy_title(self):
        a = article_from_item({'title': '방한 외래관광객 증가 및 관광수요 발표', 'link': 'https://example.org/a', 'pubDate': '2026-10-25T10:00:00+09:00'}, SRC, AT)
        b = article_from_item({'title': '방한 외래관광객 증가 및 관광수요 발표', 'link': 'https://elsewhere.org/b', 'pubDate': '2026-10-25T10:00:00+09:00'}, SRC, AT)
        self.assertEqual(len(deduplicate([a, b])), 1)

    def test_no_excerpt_without_permission(self):
        data = {'title': '방한 외래관광객 증가', 'link': 'https://example.org/a', 'description': '언론사에서 작성한 문장 그대로', 'pubDate': '2026-10-25T10:00:00+09:00'}
        result = article_from_item(data, SRC, AT)
        self.assertNotIn('언론사에서 작성한', result['desc'])
        self.assertEqual(result['summary_type'], 'metadata_only')

    def test_feed_success_persists(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = run([SRC], fetcher=lambda url: feed('방한 외래관광객 증가'), at=AT, data_dir=Path(tmp))
            self.assertEqual(result['status'], 'ok')
            n = json.loads((Path(tmp) / 'news.json').read_text())
            self.assertEqual(n['count'], 1)
            self.assertEqual(n['mode'], 'live_rss')

    def test_all_fail_preserves_previous(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp)
            run([SRC], fetcher=lambda url: feed('방한 외래관광객 증가'), at=AT, data_dir=path)
            previous = (path / 'news.json').read_bytes()
            def fail(url):
                raise ValueError('simulated feed outage')
            result = run([SRC], fetcher=fail, at=AT + dt.timedelta(hours=2), data_dir=path)
            self.assertEqual(result['status'], 'failed')
            self.assertEqual((path / 'news.json').read_bytes(), previous)
            status = json.loads((path / 'health.json').read_text())
            self.assertEqual(status['status'], 'failed')

    def test_partial_failure_persists_success(self):
        with tempfile.TemporaryDirectory() as tmp:
            src2 = dict(SRC, id='fail', url='https://bad.org/rss')
            def flaky(url):
                if 'bad.org' in url:
                    raise ValueError('down')
                return feed('방한 외래관광객 증가')
            result = run([SRC, src2], fetcher=flaky, at=AT, data_dir=Path(tmp))
            self.assertEqual(result['status'], 'partial')
            self.assertEqual(result['sources_ok'], 1)

    def test_no_new_articles_is_not_fetch_failure(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = run([SRC], fetcher=lambda url: feed('주말 맛집 추천'), at=AT, data_dir=Path(tmp))
            self.assertEqual(result['status'], 'ok')
            self.assertEqual(result['articles'], 0)

    def test_briefing_candidates_within_day(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp)
            run([SRC], fetcher=lambda url: feed('방한 외래관광객 증가'), at=AT, data_dir=p)
            b = json.loads((p / 'briefing.json').read_text())
            self.assertEqual(len(b['items']), 1)
            self.assertEqual(b['status'], 'candidates_ready')


if __name__ == '__main__':
    unittest.main()
