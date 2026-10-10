"""Same-capital, same-period declared cash plans; no annualization or selection."""
from datetime import date
from decimal import Decimal
from research import Calendar, ledger, money, text


def compare_plans(data):
    """Bounded explicit candidates; retain every failure and cost assumption."""
    from itertools import combinations
    from audit import METHOD_VERSION, digest, encoded
    allowed = {'start', 'end', 'calendar', 'initial_cash', 'input_kind', 'currency',
               'plans', 'candidate_issues', 'reference_rates'}
    if set(data) - allowed:
        raise ValueError('Unsupported multi-plan fields')
    plans = list(data['plans'])
    if not 2 <= len(plans) <= 32:
        raise ValueError('Supply 2 to 32 explicit plans first')
    issues = data.get('candidate_issues', [])
    if not isinstance(issues, list) or len(issues) > 5:
        raise ValueError('Finite search accepts at most five explicitly declared issues')
    ids = [text(p['id'], 'plan id') for p in plans + issues]
    if len(set(ids)) != len(ids):
        raise ValueError('Plan and candidate issue ids must be unique')
    for issue in issues:
        if set(issue) != {'id', 'basis', 'events'}:
            raise ValueError('Candidate issue requires id, basis and explicit events')
        text(issue['basis'], 'candidate basis')
    for n in range(len(issues)+1) if issues else []:
        for subset in combinations(issues, n):
            plans.append({'id': 'subset:' + ','.join(i['id'] for i in subset),
                          'basis': 'Finite supplied-event subset, no new dates or allocation assumptions',
                          'events': [e for i in subset for e in i['events']]})
    if len({p['id'] for p in plans}) != len(plans):
        raise ValueError('Generated subset id collides with a supplied plan')
    references = data.get('reference_rates', [])
    if not isinstance(references, list) or len(references) > 8:
        raise ValueError('At most eight reference sensitivities')
    required = {'id','annual_rate','observed_at','source','instrument','tenor',
                'first_settlement','maturity_settlement','fee_basis','applicability','basis'}
    for ref in references:
        if set(ref) != required or ref['basis'] not in ('assumption','public_reference'):
            raise ValueError('Reference needs complete rate/time/term/settlement/fee/applicability metadata')
        for key in required - {'annual_rate'}:
            text(ref[key], key)
        money(ref['annual_rate'], 'reference annual rate')
        date.fromisoformat(ref['observed_at'][:10])
        first = date.fromisoformat(ref['first_settlement'])
        if date.fromisoformat(ref['maturity_settlement']) <= first:
            raise ValueError('Reference maturity must follow first settlement')
        if ref['basis'] == 'public_reference':
            from urllib.parse import urlsplit
            url = urlsplit(ref['source'])
            if url.scheme != 'https' or not url.hostname or url.username or url.password:
                raise ValueError('Public rate reference requires a public HTTPS source')
    if len({r['id'] for r in references}) != len(references):
        raise ValueError('Reference ids must be unique')
    common = {k:v for k,v in data.items() if k not in ('plans','candidate_issues','reference_rates')}
    summaries = []
    for plan in plans:
        out = compare_cash(dict(common, plans=[plan, {'id':'baseline:'+plan['id'],
                           'basis':'Zero-event baseline for independent replay', 'events':[]}]))
        item = out['plans'][0]
        item['origin'] = 'finite_subset' if plan['id'].startswith('subset:') else 'explicit'
        item['reference_sensitivity'] = []
        for ref in references:
            cost = (Decimal(item['locked_capital_days']) * money(ref['annual_rate'], 'rate') / 365
                    if item['locked_capital_days'] is not None else None)
            item['reference_sensitivity'].append({'reference_id':ref['id'],
                'gross_locked_capital_cost':str(cost) if cost is not None else None,
                'adjusted_profit':None,
                'limit':'Gross sensitivity only; not actual alternative income, no automatic fee deduction or cash-profit adjustment'})
        summaries.append(item)
    return {'schema_version':'multi-plan.v1','method_version':'declared-plan-comparison.1',
            'engine_version':METHOD_VERSION,'input_sha256':digest(encoded(data)),
            'input_kind':data['input_kind'],'start':data['start'],'end':data['end'],
            'initial_cash':str(money(data['initial_cash'],'capital')),'plans':summaries,
            'reference_rates':references,'candidate_count':len(summaries),
            'warnings':['Only supplied events and finite subsets; no guaranteed optimal subscription or expected return.',
                        'Same-day cash ordering and retained allocation principal use the existing ledger.',
                        'Unknown extra allocation and account availability are not filled in.',
                        'Reference costs are separate sensitivities; never deducted from explicit cash comparison.']}


def compare_cash(data):
    if set(data) - {'start', 'end', 'calendar', 'initial_cash', 'input_kind', 'plans', 'currency'}:
        raise ValueError('Unsupported comparison fields; use explicit cash events, not precomputed returns')
    if data.get('currency', 'CNY') != 'CNY':
        raise ValueError('Only common CNY cash plans are supported')
    start = date.fromisoformat(data['start'])
    end = date.fromisoformat(data['end'])
    if end <= start:
        raise ValueError('Comparison end must follow start')
    calendar = Calendar(data['calendar'])
    if not calendar.start <= start < end <= calendar.end:
        raise ValueError('Calendar does not cover entire comparison period')
    capital = money(data['initial_cash'], 'initial cash')
    if capital <= 0:
        raise ValueError('Comparison requires positive initial cash')
    kind = data['input_kind']
    if kind not in ('teaching', 'scenario', 'historical_replay'):
        raise ValueError('input_kind 须为 teaching / scenario / historical_replay 之一；混合公开数据与假设用 scenario，不能填 mixed')
    plans = data['plans']
    if not isinstance(plans, list) or len(plans) != 2:
        raise ValueError('Exactly two explicit cash plans required')
    summaries = []
    identities = set()
    for plan in plans:
        identity = text(plan['id'], 'plan id')
        if identity in identities:
            raise ValueError('Plan ids must be unique')
        identities.add(identity)
        text(plan['basis'], 'plan basis')
        # Capital, currency, calendar and horizon come from one shared contract.
        if set(plan) - {'id', 'basis', 'events'}:
            raise ValueError('Plan may not override shared capital/calendar/period or inject precomputed returns')
        events = plan['events']
        if not isinstance(events, list):
            raise ValueError('Plan events must be a list')
        for event in events:
            day = date.fromisoformat(event['date'])
            if not start <= day <= end:
                raise ValueError('All plan events must be within the common period')
        result = ledger(dict(initial_cash=str(capital), calendar=data['calendar'], events=events))
        complete = (result['executable'] and
                    Decimal(result['outstanding_ipo_principal_exact']) == 0 and
                    Decimal(result['outstanding_repo_principal_exact']) == 0)
        last = start
        locked = Decimal(0)
        capital_days = Decimal(0)
        for row in result['events']:
            day = date.fromisoformat(row['date'])
            capital_days += locked * (day - last).days
            locked = Decimal(row['ipo_principal_exact']) + Decimal(row['repo_principal_exact'])
            last = day
        # Partial replay is not silently continued through the end.
        if result['executable']:
            capital_days += locked * (end-last).days
        closing = Decimal(result['final_available_cash_exact'])
        profit = closing-capital if complete else None
        summaries.append(dict(id=identity, basis=plan['basis'],
            status='settled_declared_events' if complete else 'cash_conflict' if not result['executable'] else 'unsettled_principal',
            initial_cash=str(capital), last_replayed_cash=str(closing),
            closing_cash=str(closing) if result['executable'] else None,
            realized_cash_profit=str(profit) if profit is not None else None,
            account_period_cash_return=str(profit/capital) if profit is not None else None,
            locked_capital_days=str(capital_days) if result['executable'] else None,
            paid_separate_fees=str(sum((money(e['amount'], 'fee') for e in events if e['kind']=='fee'), Decimal(0))) if result['executable'] else None,
            ledger=result))
    eligible = all(p['status'] == 'settled_declared_events' for p in summaries)
    difference = Decimal(summaries[0]['realized_cash_profit'])-Decimal(summaries[1]['realized_cash_profit']) if eligible else None
    return dict(schema_version='0.2', mode='same_period_declared_cash_comparison', input_kind=kind,
                start=start.isoformat(), end=end.isoformat(), calendar_days=(end-start).days,
                currency='CNY', initial_cash=str(capital), plans=summaries,
                comparison_status='comparable_declared_cash' if eligible else 'incomplete_not_ranked',
                first_minus_second_cash_profit=str(difference) if difference is not None else None,
                warnings=['Cash-only comparison of explicitly supplied events; no account or completeness certification.',
                          'No opportunity-cost deduction, no annualization, no compounding and no automatic plan choice.',
                          'Fees embedded in sale net proceeds or net repo interest must not be entered twice.',
                          'Idle cash income and pending interest are absent unless explicit events are supplied.',
                          'Unsettled principal has no market valuation here; unresolved plans are not ranked.'])
