"""Same-capital, same-period declared cash plans; no annualization or selection."""
from datetime import date
from decimal import Decimal
from research import Calendar, ledger, money, text


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
        raise ValueError('Declare teaching, scenario or historical_replay input_kind')
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
