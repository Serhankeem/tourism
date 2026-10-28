"""Six-field link curation. No excerpt, generated prose, image or internal evidence."""
if __package__:
    from .relevance import matches, SUBJECTS
else:
    from relevance import matches, SUBJECTS

PUBLIC_FIELDS = ('title', 'source', 'published_at', 'url', 'category', 'keywords')
TERMS = tuple(dict.fromkeys(term for terms in SUBJECTS.values() for term in terms)) + (
    '방한관광객', '대한항공', '아시아나항공', '제주항공', '진에어', '티웨이', '이스타항공',
    '하나투어', '모두투어', '야놀자', '여기어때', '아고다', '에어비앤비', 'OTA', 'GDS',
    '세이버', '호텔', '크루즈', '인바운드', '취항', '증편', '감편', '발권', '인수', '매출',
    '영업이익', '관광재단', '관광공사', '관광청', 'Korean Air', 'Booking', 'Expedia', 'Trip.com')


def public_record(record):
    """Allowlist, never copy arbitrary source fields (including old desc/insight)."""
    return {**{key: record[key] for key in PUBLIC_FIELDS if key != 'keywords'},
            'keywords': sorted(set(matches(record['title'], TERMS)), key=lambda s: (-len(s), s))[:8]}
