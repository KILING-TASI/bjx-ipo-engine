"""One public fixing reference, explicit settlement and separately declared fees."""
from datetime import date, datetime, timedelta
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path
from audit import MAX_BYTES, digest, encoded, load
from research import Calendar, money, text, repo_interest


def repo_reference(spec):
    allowed = {'quote_record','raw_quote_path','principal','dates','calendar','fee'}
    if set(spec) - allowed:
        raise ValueError('Unsupported reference fields')
    quote = load(spec['quote_record'])
    if quote['schema'] != 'public-repo-fixing.v1' or quote['instrument'] != '204001':
        raise ValueError('Only reviewed 204001 fixing sample supported')
    if quote['quote_kind'] != 'daily_fixing_not_executable_quote':
        raise ValueError('Preserve fixing reference scope')
    if quote['source'] != 'https://bond.sse.com.cn/data/standard/repocurve/onerepo/' or quote['tenor_days'] != 1:
        raise ValueError('Reviewed one-day official source required')
    rate = money(quote['rate_percent'], 'public percent') / 100
    if rate != money(quote['annual_rate_fraction'], 'public fraction'):
        raise ValueError('Percent/fraction mismatch')
    day = date.fromisoformat(quote['trade_date'])
    stamp = datetime.fromisoformat(quote['page_updated_at'])
    if stamp.tzinfo is None or stamp.date() < day:
        raise ValueError('Quote update requires timezone and valid date')
    row = quote['selected_row']
    parts = row.split(',')
    if len(parts) != 5 or parts[0] != day.strftime('%Y%m%d') or money(parts[1], 'row percent') != money(quote['rate_percent'], 'percent'):
        raise ValueError('Selected row differs from quote')
    status = 'saved_review_record_not_rechecked'
    if spec.get('raw_quote_path'):
        path = Path(spec['raw_quote_path'])
        if path.stat().st_size > MAX_BYTES:
            raise ValueError('Raw quote exceeds 10 MiB')
        blob = path.read_bytes()
        if digest(blob) != quote['raw_sha256']:
            raise ValueError('Raw quote hash mismatch')
        body = blob.decode('utf-8')
        if row not in body or stamp.strftime('%Y-%m-%d %H:%M:%S') not in body or 'RATE_1DAY' not in body or '204001' not in body:
            raise ValueError('Selected quote anchors missing')
        status = 'exact_hash_and_selected_numeric_anchors_match'
    principal = money(spec['principal'], 'principal')
    if principal <= 0:
        raise ValueError('Positive principal required')
    dates = spec['dates']
    if set(dates) != {'trade_date','first_settlement_date','maturity_settlement_date',
                      'principal_available_date','interest_available_date','basis','source','availability_basis'}:
        raise ValueError('Explicit settlement and cash availability declarations required')
    for key in ('basis','source','availability_basis'):
        text(dates[key], key)
    if dates['trade_date'] != quote['trade_date']:
        raise ValueError('Do not reuse dated fixing for another trade date')
    calendar = Calendar(spec['calendar'])
    first = calendar.next_day(day)
    due = day + timedelta(days=quote['tenor_days'])
    maturity_day = next((d for d in calendar.days if d >= due), None)
    if maturity_day is None:
        raise ValueError('Calendar does not cover nominal maturity')
    final = calendar.next_day(maturity_day)
    if dates['first_settlement_date'] != first.isoformat() or dates['maturity_settlement_date'] != final.isoformat():
        raise ValueError('Explicit settlement dates disagree with supplied calendar and fixing settlement rule')
    interest_day = date.fromisoformat(dates['interest_available_date'])
    calendar.check(interest_day)
    if interest_day < date.fromisoformat(dates['maturity_settlement_date']):
        raise ValueError('Interest availability cannot precede maturity settlement')
    # Existing calculation validates settlement ordering and declared calendar dates.
    trade = {k:dates[k] for k in ('trade_date','first_settlement_date','maturity_settlement_date','principal_available_date')}
    trade.update(principal=str(principal), annual_rate=str(rate), fee='0',
                 evidence={'basis':'assumption','source':dates['source']})
    checked = repo_interest(trade, calendar)
    gross = principal * rate * checked['interest_days'] / 365
    rounded = gross.quantize(Decimal('.01'), rounding=ROUND_HALF_UP)
    fee = spec['fee']
    text(fee['basis'], 'fee basis'); text(fee['source'], 'fee source')
    fee_amount = None
    if fee['status'] == 'declared':
        if set(fee) != {'status','basis','source','principal_rate','minimum','fixed','paid_date','rounding'}:
            raise ValueError('Complete fee formula and paid date required')
        if fee['rounding'] != 'half_up_cent':
            raise ValueError('Declare half_up_cent fee rounding')
        paid = date.fromisoformat(fee['paid_date']); calendar.check(paid)
        if not day <= paid <= interest_day:
            raise ValueError('Fee paid date must fall within explicit cash period')
        fee_amount = (max(principal * money(fee['principal_rate'], 'fee rate'),
                         money(fee['minimum'], 'minimum')) + money(fee['fixed'], 'fixed')).quantize(Decimal('.01'), rounding=ROUND_HALF_UP)
    elif fee['status'] != 'unknown' or set(fee) != {'status','basis','source'}:
        raise ValueError('Fee must be explicitly declared or unknown')
    events = None
    if fee_amount is not None:
        evidence = {'basis':'assumption','source':'Dated public fixing applied to hypothetical principal; declared availability/fees, no account execution'}
        events = [{'id':'reference-open','instrument':'REFERENCE-204001','date':dates['trade_date'],'kind':'repo_open','amount':str(principal),'evidence':evidence},
                  {'id':'reference-principal','instrument':'REFERENCE-204001','date':dates['principal_available_date'],'kind':'repo_principal','amount':str(principal),'evidence':evidence},
                  {'id':'reference-interest','instrument':'REFERENCE-204001','date':dates['interest_available_date'],'kind':'repo_interest','amount':str(rounded),'evidence':evidence},
                  {'id':'reference-fee','instrument':'REFERENCE-204001','date':fee['paid_date'],'kind':'fee','amount':str(fee_amount),'evidence':evidence}]
        # An explicit zero is retained in the result, but is not a cash movement.
        # Unknown fees never reach this branch. Do not relax the ledger contract.
        events = [event for event in events if Decimal(event['amount']) != 0]
    return {'schema_version':'repo-reference.v1','method_version':'public-fixing-fee-adaptation.2',
            'input_sha256':digest(encoded(spec)), 'quote_record_sha256':digest(encoded(quote)),
            'quote':quote,'source_check':status,'principal':str(principal),'dates':dates,'fee':fee,
            'interest_days':checked['interest_days'],'gross_interest_exact':str(gross),
            'gross_interest_cent':str(rounded),'rounding_basis':'Declared half-up-cent research convention, not certified broker rounding',
            'fee_exact':str(fee_amount) if fee_amount is not None else None,
            'net_reference_interest':str(rounded-fee_amount) if fee_amount is not None else None,
            'status':'declared_reference_scenario' if fee_amount is not None else 'fee_unknown_net_blocked',
            'cash_plan':{'id':'public-fixing-reference','basis':'Historical fixing with hypothetical principal, cash availability and fee assumptions','events':events} if events is not None else None,
            'limits':['Public daily fixing is neither executable quote nor actual account net income.',
                      'Record/hash matching is mutable provenance, not independent certification; supplied calendar completeness is not certified.',
                      'Fees and cash availability remain explicit assumptions; no actual-account acceptance.',
                      'No rolling reinvestment or period-wide constant-rate substitution.',
                      'Gross interest and fee are separate events: do not deduct fee twice.']}
