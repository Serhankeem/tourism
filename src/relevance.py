"""Deterministic, metadata-only relevance rules. No article-body retrieval or AI.

Indirect stories are held until a title-bound editorial approval supplies an
original-source URL and an impact explanation. Keyword presence alone is not an
approval. Evidence contains rule identifiers/terms, never copied RSS paragraphs.
"""
import hashlib
import re
import unicodedata

RULE_VERSION = '0.2'
CATEGORIES = ('관광정책', '인바운드', '여행산업', '항공·숙박', '문화·트렌드', '경제·시장')
LEGACY_CATEGORIES = {'정책': '관광정책', '수요': '인바운드', '산업': '여행산업',
                     '리서치': '경제·시장', '지역': '문화·트렌드', 'MICE': '여행산업'}
# A subject is an industry concept, not the generic word 관광/여행/항공/문화.
SUBJECTS = {
    '관광정책': ('관광정책', '관광산업', '관광진흥', '관광예산', '관광기금', '관광비자', '관광세', '무비자', 'tourism policy', 'tourism strategy'),
    '인바운드': ('외래관광객', '외국인관광객', '방한객', '방한수요', '인바운드', '관광객수', '입국관광객', 'inbound tourism', 'visitor arrivals'),
    '여행산업': ('여행업', '여행사', '관광기업', '관광스타트업', '관광플랫폼', '여행플랫폼', '국제회의', '컨벤션산업', '마이스산업', 'travel agency', 'convention industry'),
    '항공·숙박': ('호텔업', '호텔시장', '관광숙박', '숙박업', '호텔객실', '객실점유율', '객실공급', '숙박요금', '항공노선', '국제선', '항공운임', '항공사', '여객수요', 'airline routes', 'hospitality'),
    '문화·트렌드': ('지역관광', '관광특구', '관광도시', '관광개발', '관광콘텐츠', '관광활성화', '관광재단', '웰니스관광', '웰니스트래블', 'regional tourism'),
    '경제·시장': ('국내여행수요', '관광통계', '관광수입', '관광지출', '관광소비', '관광데이터', '관광연구', '관광산업동향', 'tourism statistics', 'tourism receipts'),
}
ACTIONS = ('발표', '지원', '개최', '운영', '증가', '감소', '확대', '축소', '공급', '취항', '운항', '결항', '예약', '투자', '실적', '매출', '정책', '개편', '수요', '개발', '지원', '증편', '감편', '파산', '신설', '폐지')
SECTORS = {
    '경제·시장': ('환율', '원화약세', '원화강세', '원달러', '금리', '유가', '물가', '소비심리', '경기침체'),
    '문화·트렌드': ('앨범', '도서전', '미술', '콘서트', '공연', '한류', '영화', '스포츠', '축제', '전시'),
    '항공·숙박': ('폭우', '태풍', '지진', '파업', '공항폐쇄'),
    '여행산업': ('철도', '고속철', '교통망', '주52시간', '휴일', '휴가제도'),
}
IMPACTS = {
    '관광수요': ('관광수요', '국내여행수요', '방한수요', '방한객', '외래관광객', '외국인관광객', '해외여행수요', '입국관광객', '관광객수', '해외팬입국'),
    '관광소비': ('관광소비', '관광지출', '관광수입', '여행경비', '숙박예약', '객실예약', '호텔객실', '객실점유율'),
    '관광기업': ('여행사', '호텔업', '숙박업', '항공사', '국제선', '관광기업'),
    '관광정책': ('관광정책', '관광예산', '관광기금', '관광비자'),
}
LINKS = ('영향', '증가', '감소', '확대', '축소', '부담', '견인', '때문', '따라', '급증', '취소', '결항', '감편', '증편')
UNCERTAIN = ('가능성', '예상', '추정', '전망', '수있', '수도있', '확인되지', '근거없')
NEGATIVE = ('무관', '관련없', '영향없', '관계없', '영향을주지않', '영향이없')
PERSONAL = ('연예인여행', '연예여행', '여행예능', '여행블로그', '여행후기', '산책후기', '맛집소개', '가볼만한곳', '영화줄거리')


def compact(text):
    return re.sub(r'\s+', ' ', unicodedata.normalize('NFKC', text).casefold()).strip()


def title_digest(title):
    return hashlib.sha256(unicodedata.normalize('NFKC', title).strip().encode()).hexdigest()


def matches(text, terms):
    found = []
    for term in terms:
        letters = re.sub(r'\s+', '', compact(term))
        pattern = r'\s*'.join(re.escape(char) for char in letters)
        if term in ('여행사', '항공사'):
            # Do not turn 참'여 행사', 여행사진 or 여행사랑 into a company.
            pattern = r'(?<![가-힣A-Za-z])' + pattern + r'(?=\s|[은는이가를의와도에로]|[^가-힣A-Za-z]|$)'
        if re.search(pattern, text):
            found.append(term)
    return found


def assess(title, description=''):
    fields = {'title': compact(title), 'description': compact(description)}
    result = {'rule_version': RULE_VERSION, 'label': 'Irrelevant', 'decision': 'exclude',
              'category': None, 'score': 0, 'rules': [], 'signals': [],
              'impact_targets': [], 'reason': '관광산업에 대한 구체적 대상·영향 근거가 없습니다.'}
    if matches(fields['title'], PERSONAL):
        return {**result, 'rules': ['personal_or_generic_travel'], 'reason': '개인 여행·일반 여가 정보는 산업 뉴스에서 제외합니다.'}
    if matches(fields['title'], ('할인쿠폰', '최저가', '추천숙소', '호텔추천')) and not matches(fields['title'], ('시장', '실적', '매출', '정책', '공급', '수요')):
        return {**result, 'rules': ['consumer_promotion'], 'reason': '일반 예약·할인 정보는 산업 뉴스에서 제외합니다.'}
    # Never combine unrelated sentences into a manufactured causal connection.
    for field, raw in (('title', title), ('description', description)):
        for sentence in re.split(r'[.!?。\n]+', raw):
            text = compact(sentence)
            if matches(text, NEGATIVE):
                continue
            for category, sectors in SECTORS.items():
                sector_hits = matches(text, sectors)
                impacts = {k: matches(text, v) for k, v in IMPACTS.items()}
                targets = [k for k, v in impacts.items() if v]
                if sector_hits and targets:
                    linked = matches(text, LINKS)
                    uncertain = matches(text, UNCERTAIN)
                    return {**result, 'label': 'Indirect', 'decision': 'hold', 'category': category,
                            'score': 6 if linked and not uncertain else 2,
                            'rules': ['cross_sector_impact' if linked else 'cross_sector_unproven'],
                            'signals': [{'field': field, 'terms': sector_hits + [t for v in impacts.values() for t in v] + linked}],
                            'impact_targets': targets,
                            'evidence_status': 'explicit_feed_claim' if linked and not uncertain else 'insufficient',
                            'reason': '다른 산업 변화와 관광산업 영향의 근거를 원문에서 검토한 뒤 승인해야 합니다.'}
    # A generic macro/culture headline cannot become Direct from incidental
    # tourism keywords in a different paragraph.
    cross_headline = any(matches(fields['title'], terms) for terms in SECTORS.values())
    candidates = []
    for category, terms in SUBJECTS.items():
        for field, raw in (('title', title), ('description', description)):
            # Direct support must also be local to a single sentence.
            contexts = [raw] if field == 'title' else re.split(r'[.!?。\n]+', raw)
            for context in contexts:
                text = compact(context)
                hits = matches(text, terms)
                if not hits or matches(text, NEGATIVE):
                    continue
                actions = matches(text, ACTIONS)
                entity_only = all(h in ('여행사', '항공사', '관광재단') for h in hits)
                if field == 'title' and entity_only and not actions:
                    continue
                if field == 'title' or len(hits) >= 2 or (hits and actions):
                    candidates.append((4 * len(hits) + (2 if field == 'title' else 0), category, field, hits))
    if cross_headline:
        candidates = [candidate for candidate in candidates if candidate[2] == 'title']
        if not candidates:
            return {**result, 'rules': ['cross_sentence_unproven'],
                    'reason': '다른 산업 기사에서 관광 키워드만으로 영향 관계를 만들지 않습니다.'}
    if candidates:
        # Keep the historical demand-before-statistics priority on tied headlines.
        order = ('인바운드', '관광정책', '경제·시장', '항공·숙박', '여행산업', '문화·트렌드')
        score, category, field, hits = max(candidates, key=lambda c: (c[0], -order.index(c[1])))
        return {**result, 'label': 'Direct', 'decision': 'publish', 'category': category,
                'score': score, 'rules': ['explicit_industry_subject'],
                'signals': [{'field': field, 'terms': hits}],
                'evidence_status': 'industry_subject_in_feed',
                'reason': 'RSS 제목 또는 설명에서 구체적인 관광산업 대상·사업 신호를 확인했습니다.'}
    return result


def approve(assessment, title, url, approval, at, parse_date):
    """Reject stale, unbound, malformed or unsupported indirect approvals."""
    if assessment.get('label') != 'Indirect' or not isinstance(approval, dict):
        return assessment
    valid = (assessment.get('evidence_status') == 'explicit_feed_claim'
             and approval.get('rule_version') == RULE_VERSION
             and approval.get('title_sha256') == title_digest(title)
             and approval.get('evidence_url') == url
             and isinstance(approval.get('reason'), str)
             and len(approval['reason'].strip()) >= 15)
    reviewed_at = parse_date(approval.get('reviewed_at', ''))
    if not valid or reviewed_at is None or reviewed_at > at:
        return assessment
    return {**assessment, 'decision': 'publish', 'review_status': 'approved',
            'review': {k: approval[k] for k in ('reviewed_at', 'evidence_url', 'reason', 'title_sha256', 'rule_version')}}
