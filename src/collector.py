"""Tourism Pulse auto RSS collector: stdlib only, safe metadata-first processing.

This tool does not fetch article bodies. Publisher terms must be reviewed before
turning on reusable excerpts or integrating an AI summarizer.
"""
from __future__ import annotations

import argparse
import calendar
import datetime as dt
import email.utils
import hashlib
import html
import json
import os
from pathlib import Path
import re
import sys
import tempfile
import unicodedata
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from difflib import SequenceMatcher
from zoneinfo import ZoneInfo

KST = ZoneInfo('Asia/Seoul')
ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'site' / 'data'
USER_AGENT = 'TourismPulseRSS/0.1 (+metadata-only; contact repository maintainer)'
TRACKING = {'fbclid', 'gclid', 'ref', 'spm', 'source', 'igshid'}
KEYWORDS = {
    '정책': ['관광정책', '관광진흥', '국가관광', '관광산업', '관광부', '관광공사', '관광예산', '관광기금', '관광비자', '무비자', '관광세', 'tourism policy', 'tourism strategy'],
    '수요': ['방한', '외래관광객', '입국 관광객', '인바운드', '해외관광객', '출입국 관광', '관광수요', '관광객 수', '관광객 증가', '관광객 감소', 'inbound tourism', 'visitor arrivals'],
    '산업': ['호텔업', '호텔시장', '관광숙박', '여행업', '여행사', '관광기업', '관광스타트업', '항공노선', '국제선', '여객수요', '저비용항공', 'ota 플랫폼', '관광플랫폼', '여행플랫폼', 'hospitality', 'travel agency', 'airline routes'],
    '리서치': ['관광통계', '관광수입', '관광지출', '관광소비', '관광데이터', '관광연구', '관광산업동향', '관광지수', 'tourism statistics', 'tourism research', 'tourism receipts'],
    '지역': ['지역관광', '관광특구', '관광도시', '관광개발', '관광콘텐츠', '관광축제', '관광지', '관광활성화', 'regional tourism', 'tourist attraction'],
    'MICE': ['마이스', 'mice 산업', '컨벤션', '국제회의', '전시산업', '국제전시회', 'convention industry', 'conference tourism']
}
WEAK = ['관광', 'travel', 'tourism', '여행', 'tourist', 'visitor', '호텔', '항공', '크루즈', '축제', '숙박', '관광객']
EXCLUDE = ['연예인 여행', '연예 여행', '영화 줄거리', '여행 예능', '단순 여행 후기', '여행 블로그']
CAT_ORDER = ['수요', '정책', '리서치', '산업', '지역', 'MICE']


def now_kst():
    return dt.datetime.now(tz=KST)


def iso(value):
    return value.astimezone(KST).isoformat(timespec='seconds')


def stripped(value):
    v = html.unescape(re.sub(r'<[^>]+>', ' ', str(value or '')))
    return re.sub(r'\s+', ' ', v).strip()


def timestamp(value, fallback=None):
    fallback = fallback or now_kst()
    if isinstance(value, dt.datetime):
        found = value
    else:
        raw = stripped(value)
        if not raw:
            return fallback
        try:
            found = dt.datetime.fromisoformat(raw.replace('Z', '+00:00'))
        except ValueError:
            try:
                found = email.utils.parsedate_to_datetime(raw)
            except (ValueError, TypeError):
                return fallback
    if found.tzinfo is None:
        found = found.replace(tzinfo=KST)
    return found.astimezone(KST)


def canonical_url(value):
    value = stripped(value)
    try:
        p = urllib.parse.urlsplit(value)
        if p.scheme.lower() not in ('https', 'http') or not p.hostname:
            return ''
        query = urllib.parse.parse_qsl(p.query, keep_blank_values=True)
        query = [(k, v) for k, v in query if not k.lower().startswith('utm_') and k.lower() not in TRACKING]
        return urllib.parse.urlunsplit((p.scheme.lower(), p.netloc.lower(), p.path or '/', urllib.parse.urlencode(query), ''))
    except ValueError:
        return ''


def normalized_title(value):
    s = unicodedata.normalize('NFKC', stripped(value)).casefold()
    s = re.sub(r'\[[^]]{1,20}\]|\([^)]{1,14}\)', ' ', s)
    return re.sub(r'[^\w가-힣]+', '', s)


def similarity(a, b):
    na, nb = normalized_title(a), normalized_title(b)
    return SequenceMatcher(None, na, nb).ratio() if na and nb else 0.0


def classify(title, description=''):
    title, description = stripped(title).lower(), stripped(description).lower()
    if any(bad in title for bad in EXCLUDE):
        return None, 0
    scores = {k: sum((4 if term in title else 0) + (1 if term in description else 0) for term in terms)
              for k, terms in KEYWORDS.items()}
    weak_title = sum(1 for term in WEAK if term in title)
    weak_desc = sum(1 for term in WEAK if term in description)
    best = max(CAT_ORDER, key=lambda name: (scores[name], -CAT_ORDER.index(name)))
    score = scores[best] + min(weak_title, 2) + (1 if weak_desc else 0)
    # A generic travel story without an industry signal does not qualify.
    if scores[best] < 4 and not (scores[best] >= 1 and weak_title >= 1):
        return None, score
    if score < 4:
        return None, score
    return best, score


def xml_items(xml_bytes):
    root = ET.fromstring(xml_bytes)
    # Defensive limits: no HTML body retrieval, 1MB maximum payload enforced at fetch.
    for node in root.iter():
        tag = node.tag.rsplit('}', 1)[-1]
        if tag not in ('item', 'entry'):
            continue
        data = {}
        for child in node:
            key = child.tag.rsplit('}', 1)[-1]
            value = (child.text or '').strip()
            if key == 'link':
                value = value or child.attrib.get('href', '')
                if child.attrib.get('rel', 'alternate') not in ('alternate', ''):
                    continue
            if key in ('title', 'link', 'pubDate', 'published', 'updated', 'description', 'summary') and value:
                data[key] = value
        yield data


def fetch_feed(url, timeout=15):
    safe = canonical_url(url)
    if not safe:
        raise ValueError('Invalid RSS URL')
    request = urllib.request.Request(safe, headers={'User-Agent': USER_AGENT, 'Accept': 'application/rss+xml, application/atom+xml, application/xml, text/xml, */*'})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        payload = response.read(1024 * 1024 + 1)
        if len(payload) > 1024 * 1024:
            raise ValueError('RSS response too large')
        return payload


def article_from_item(item, source, at=None):
    at = at or now_kst()
    title = stripped(item.get('title', ''))
    description = stripped(item.get('description', item.get('summary', '')))
    url = canonical_url(item.get('link', ''))
    if not title or not url:
        return None
    date_value = item.get('pubDate') or item.get('published') or item.get('updated')
    if not date_value:
        return None  # Unknown publication date must never be labeled as fresh news.
    published = timestamp(date_value, at)
    if published > at + dt.timedelta(days=2) or published < at - dt.timedelta(days=45):
        return None
    category, relevance = classify(title, description)
    if not category:
        return None
    reusable = bool(source.get('reuse_excerpt'))
    # Metadata-only by default; do not republish an unlicensed publisher excerpt.
    if reusable and description:
        desc = (description[:240].rstrip(' .') + ('…' if len(description) > 240 else ''))
        summary_type = 'rss_excerpt'
    else:
        desc = '원문 링크에서 보도자료 또는 기사 내용을 확인하세요. (본문 자동 분석 전)'
        summary_type = 'metadata_only'
    aid = hashlib.sha256(url.encode('utf-8')).hexdigest()[:18]
    return {
        'id': aid, 'published_at': iso(published), 'date': published.strftime('%Y.%m.%d'),
        'category': category, 'source': source['name'], 'source_id': source['id'],
        'title': title[:240], 'desc': desc, 'insight': '원문을 확인한 후 산업적 시사점을 판단해 주세요.',
        'summary_type': summary_type, 'url': url, 'relevance': relevance,
        'related_sources': [source['name']]
    }


def deduplicate(items):
    out = []
    for article in sorted(items, key=lambda a: a['published_at'], reverse=True):
        match = next((old for old in out if (old['url'] == article['url']) or
            (similarity(old['title'], article['title']) >= .92 and
             abs((timestamp(old['published_at']) - timestamp(article['published_at'])).total_seconds()) < 72 * 3600)), None)
        if match:
            for src in article.get('related_sources', [article['source']]):
                if src not in match['related_sources']:
                    match['related_sources'].append(src)
        else:
            out.append(article)
    return out


def read_json(path, fallback):
    try:
        return json.loads(path.read_text(encoding='utf-8'))
    except (FileNotFoundError, ValueError):
        return fallback


def write_atomic(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(prefix='tmp-', suffix='.json', dir=path.parent)
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as file:
            json.dump(data, file, ensure_ascii=False, indent=2)
            file.write('\n')
        os.replace(name, path)
    finally:
        if os.path.exists(name):
            os.unlink(name)


def run(sources, fetcher=fetch_feed, at=None, demo=False, data_dir=DATA):
    at = at or now_kst()
    news_file, brief_file, health_file = [data_dir / f for f in ('news.json', 'briefing.json', 'health.json')]
    old = read_json(news_file, {})
    prior_articles = old.get('articles', []) if old.get('mode') != 'fixture_demo' else []
    found, health, ok = [], [], 0
    for source in sources:
        if not source.get('enabled', True):
            continue
        try:
            payload = fetcher(source['url'])
            items = list(xml_items(payload))
            news = [article_from_item(item, source, at) for item in items]
            found.extend(a for a in news if a is not None)
            health.append({'id': source['id'], 'name': source['name'], 'status': 'ok', 'rss_items': len(items), 'matched': sum(a is not None for a in news)})
            ok += 1
        except (ET.ParseError, ValueError, urllib.error.URLError, TimeoutError, OSError) as exc:
            health.append({'id': source['id'], 'name': source['name'], 'status': 'error', 'error': f'{type(exc).__name__}: {exc}'[:250]})
    status = 'ok' if ok == len(health) and ok else ('partial' if ok else 'failed')
    previous_success = old.get('last_successful_fetch')
    last_success = iso(at) if ok else previous_success
    write_atomic(health_file, {'checked_at': iso(at), 'last_successful_fetch': last_success, 'status': status, 'sources': health, 'source_count': len(health), 'successful_sources': ok})
    if not ok:
        # All sources failed: NEVER erase existing news or replace existing briefing.
        return {'status': 'failed', 'articles': len(prior_articles), 'sources_ok': 0}
    candidates = found + ([] if demo else prior_articles)
    combined = deduplicate(candidates)
    cutoff = at - dt.timedelta(days=45)
    combined = [x for x in combined if timestamp(x['published_at']) >= cutoff][:450]
    mode = 'fixture_demo' if demo else 'live_rss'
    write_atomic(news_file, {'generated_at': iso(at), 'last_successful_fetch': last_success, 'count': len(combined), 'mode': mode, 'articles': combined})
    within_day = [x for x in combined if timestamp(x['published_at']) >= at - dt.timedelta(hours=24)]
    selected = sorted(within_day, key=lambda x: (-x['relevance'], x['published_at']))[:5]
    write_atomic(brief_file, {
        'generated_at': iso(at), 'status': 'demo' if demo else ('candidates_ready' if selected else 'no_recent_articles'),
        'mode': mode, 'title': '관광산업 주요 뉴스 브리핑 후보',
        'items': [{'id': x['id'], 'title': x['title'], 'source': x['source'], 'category': x['category'], 'url': x['url'], 'published_at': x['published_at'], 'desc': x['desc'], 'summary_type': x['summary_type']} for x in selected],
        'notice': '브리핑 후보만 자동 생성. 카카오톡 발송 및 본문 기반 AI 요약은 미구현.'
    })
    return {'status': status, 'articles': len(combined), 'sources_ok': ok, 'briefing_candidates': len(selected), 'mode': mode}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--demo', action='store_true', help='Use clearly labeled synthetic test RSS instead of live sources')
    parser.add_argument('--dir', default=str(DATA), help='Destination for site JSON')
    args = parser.parse_args()
    sources = json.loads((ROOT / 'sources.json').read_text(encoding='utf-8'))['sources']
    if args.demo:
        from functools import partial
        demo_file = ROOT / 'fixtures' / 'sample.xml'
        sources = [{'id': 'fixture', 'name': '가상 테스트 피드', 'url': 'https://example.org/rss.xml', 'enabled': True, 'reuse_excerpt': True}]
        fetcher = lambda url: demo_file.read_bytes()
    else:
        fetcher = fetch_feed
    result = run(sources, fetcher=fetcher, demo=args.demo, data_dir=Path(args.dir))
    print(json.dumps(result, ensure_ascii=False))
    return 1 if result['status'] == 'failed' else 0


if __name__ == '__main__':
    sys.exit(main())
