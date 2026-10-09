"""Derive scheduled dates from reviewed exchange notices, not actual market attendance."""
from datetime import date, timedelta
import re
from research import text


def build_calendar(spec):
    year = spec['year']
    if isinstance(year, bool) or not isinstance(year, int) or not 1900 <= year <= 2100:
        raise ValueError('Calendar requires a supported integer year')
    if spec['exchange'] != 'BSE' or spec['weekdays'] != [0, 1, 2, 3, 4]:
        raise ValueError('Only declared Monday-Friday BSE scheduled calendars supported')
    sources = spec['sources']
    if not isinstance(sources, list) or not sources:
        raise ValueError('Official source records are required')
    identities = set()
    for source in sources:
        ident = text(source['id'], 'source id')
        if ident in identities:
            raise ValueError('Duplicate calendar source id')
        identities.add(ident)
        if not source['url'].startswith('https://www.bse.cn/'):
            raise ValueError('Calendar source must be a BSE HTTPS URL')
        date.fromisoformat(source['document_date'])
        date.fromisoformat(source['reviewed_on'])
        text(source['locator'], 'calendar locator')
        if not re.fullmatch(r'[a-f0-9]{64}', source['captured_sha256']):
            raise ValueError('Captured source hash required')
    holidays = set()
    for item in spec['holiday_closures']:
        if not item['source_ids'] or not set(item['source_ids']) <= identities:
            raise ValueError('Holiday source binding missing')
        first, last = date.fromisoformat(item['start']), date.fromisoformat(item['end'])
        if first.year != year or last.year != year or last < first:
            raise ValueError('Holiday range must be inside calendar year')
        for offset in range((last-first).days+1):
            day = first+timedelta(days=offset)
            if day in holidays:
                raise ValueError('Overlapping holiday ranges')
            holidays.add(day)
    first, last = date(year, 1, 1), date(year, 12, 31)
    dates = [first+timedelta(days=i) for i in range((last-first).days+1)]
    trading = [day.isoformat() for day in dates if day.weekday() < 5 and day not in holidays]
    for day in spec['explicit_weekend_closures']:
        parsed = date.fromisoformat(day)
        if parsed.year != year or parsed.weekday() < 5:
            raise ValueError('Explicit weekend closure is not a weekend in the calendar year')
    return dict(coverage_start=first.isoformat(), coverage_end=last.isoformat(),
                source=spec['sources'][0]['url'], basis='derived', trading_dates=trading,
                scheduled_trading_date_count=len(trading), exchange='BSE',
                derivation=dict(method='weekday-rule-minus-announced-holiday-ranges', sources=sources,
                                review_scope='Published holiday ranges and weekday rule; no exhaustive exceptional-closure review'),
                warnings=['Scheduled dates, not certification of actual market opening.',
                          'Government make-up workdays do not open weekend trading.',
                          'No refund, settlement, broker availability or repo maturity dates are inferred.',
                          'Historical queries before source publication must use an earlier available schedule.'])
