"""Evidence registry and explicit event cash ledger; no trading or prediction."""
import argparse
import json
from datetime import date, datetime
from decimal import Decimal
from urllib.parse import urlparse
from audit import load


def text(value, name):
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f'{name}: nonempty text required')
    return value


def money(value, name):
    if isinstance(value, bool) or not isinstance(value, (int, float, str)):
        raise ValueError(f'{name}: number required')
    try:
        number = Decimal(str(value))
    except Exception as exc:
        raise ValueError(f'{name}: invalid number') from exc
    if not number.is_finite() or number < 0:
        raise ValueError(f'{name}: finite nonnegative number required')
    return number


def evidence(record):
    basis = record['basis']
    if basis not in ('original', 'third_party', 'assumption', 'derived'):
        raise ValueError('invalid evidence basis')
    text(record['source'], 'source')
    if basis in ('original', 'third_party'):
        if urlparse(record['source']).scheme != 'https':
            raise ValueError('source must be an HTTPS URL')
        date.fromisoformat(record['document_date'])
        stamp = datetime.fromisoformat(record['retrieved_at'])
        if stamp.utcoffset() is None:
            raise ValueError('retrieved_at requires timezone')
        text(record['locator'], 'locator')
    elif basis == 'derived':
        if not record.get('dependencies'):
            raise ValueError('derived evidence requires dependencies')
    return basis


def facts(data):
    """Keep all conflicting candidates; registration is not verification."""
    text(data['security'], 'security')
    text(data['rule_version'], 'rule_version')
    fields = {}
    for name, candidates in data['fields'].items():
        text(name, 'field name')
        if not isinstance(candidates, list):
            raise ValueError('field candidates must be a list')
        values = []
        for c in candidates:
            if c.get('value') is None:
                raise ValueError('use empty candidates for missing values')
            evidence(c)
            text(c['unit'], 'unit')
            values.append((json.dumps(c['value'], sort_keys=True, allow_nan=False), c['unit']))
        conflict = len(set(values)) > 1
        fields[name] = dict(status='missing' if not values else 'conflict' if conflict else 'recorded_unverified',
                            candidates=candidates, resolved_value=None)
    for required in data.get('required_fields', []):
        fields.setdefault(required, dict(status='missing', candidates=[], resolved_value=None))
    return dict(schema_version='0.2-alpha', security=data['security'], rule_version=data['rule_version'],
                fields=fields, warning='Registration preserves claims; it does not verify source text or applicability.')


class Calendar:
    def __init__(self, data):
        text(data['source'], 'calendar source')
        self.basis = text(data['basis'], 'calendar basis')
        if self.basis not in ('assumption', 'original', 'third_party'):
            raise ValueError('invalid calendar basis')
        self.start = date.fromisoformat(data['coverage_start'])
        self.end = date.fromisoformat(data['coverage_end'])
        if self.end < self.start:
            raise ValueError('invalid calendar coverage')
        self.days = [date.fromisoformat(d) for d in data['trading_dates']]
        if self.days != sorted(set(self.days)) or any(d < self.start or d > self.end for d in self.days):
            raise ValueError('calendar dates must be unique, sorted and within coverage')
        if not self.days:
            raise ValueError('empty trading calendar')

    def check(self, day):
        if not self.start <= day <= self.end:
            raise ValueError('date outside calendar coverage')
        if day not in self.days:
            raise ValueError('event date is not a declared trading date')

    def next_day(self, day):
        self.check(day)
        index = self.days.index(day) + 1
        if index == len(self.days):
            raise ValueError('calendar lacks next trading date')
        return self.days[index]


def repo_interest(trade, calendar):
    principal = money(trade['principal'], 'repo principal')
    rate = money(trade['annual_rate'], 'repo annual rate')
    fee = money(trade['fee'], 'repo fee')
    entered = date.fromisoformat(trade['trade_date'])
    available = date.fromisoformat(trade['principal_available_date'])
    first = date.fromisoformat(trade['first_settlement_date'])
    final = date.fromisoformat(trade['maturity_settlement_date'])
    for d in (entered, available, first, final):
        calendar.check(d)
    if not entered < available or not entered <= first < final:
        raise ValueError('invalid repo settlement ordering')
    if available > final:
        raise ValueError('principal availability cannot follow final settlement')
    evidence(trade['evidence'])
    days = (final - first).days
    interest = principal * rate * days / Decimal(365)
    return dict(interest_days=days, gross_interest=float(interest), fee=float(fee),
                net_interest=float(interest - fee))


def ledger(data):
    """Atomic same-day groups; unknown release timing sorts after commitments."""
    initial = money(data['initial_cash'], 'initial cash')
    if initial <= 0:
        raise ValueError('initial_cash must be positive')
    calendar = Calendar(data['calendar'])
    events = []
    ids = set()
    allowed = {'freeze', 'refund', 'sale', 'repo_open', 'repo_principal', 'repo_interest'}
    for e in data['events']:
        identity = text(e['id'], 'event id')
        if identity in ids:
            raise ValueError('duplicate event id')
        ids.add(identity)
        instrument = text(e['instrument'], 'instrument')
        kind = e['kind']
        if kind not in allowed:
            raise ValueError('invalid event kind')
        amount = money(e['amount'], 'event amount')
        if amount == 0 and kind != 'sale':
            raise ValueError('event amount must be positive except a total-loss sale')
        day = date.fromisoformat(e['date'])
        calendar.check(day)
        evidence(e['evidence'])
        order = e.get('order')
        if order is not None:
            if isinstance(order, bool) or not isinstance(order, int) or order < 0:
                raise ValueError('order must be a nonnegative integer')
            evidence(e['timing_evidence'])
        events.append((day, order, instrument, kind, amount, identity))
    # Explicit order is usable only if every event on that day has timing evidence.
    ordered_days = {d: all(e[1] is not None for e in events if e[0] == d) for d in {e[0] for e in events}}
    keys = {}
    for e in events:
        d, order, _, kind, _, _ = e
        rank = order if ordered_days[d] else (0 if kind in ('freeze', 'repo_open') else 1)
        keys.setdefault((d, rank), []).append(e)
    cash = initial
    frozen = {}
    repos = {}
    rows = []
    conflicts = []
    for (day, rank), group in sorted(keys.items()):
        needed = sum((e[4] for e in group if e[3] in ('freeze', 'repo_open')), Decimal(0))
        if needed > cash:
            conflicts.append(dict(date=day.isoformat(), required=float(needed), available=float(cash),
                                  shortage=float(needed-cash), event_ids=[e[5] for e in group]))
            # Do not pretend that a partially executable user plan was executed.
            break
        for _, _, instrument, kind, amount, identity in sorted(group, key=lambda e: e[5]):
            if kind == 'freeze':
                cash -= amount
                frozen[instrument] = frozen.get(instrument, Decimal(0)) + amount
            elif kind == 'refund':
                if amount > frozen.get(instrument, Decimal(0)):
                    raise ValueError('refund exceeds instrument frozen principal')
                frozen[instrument] -= amount
                cash += amount
            elif kind == 'sale':
                # Sale includes an explicit principal component; profit can be negative.
                raw = next(v for v in data['events'] if v['id'] == identity)
                principal = money(raw['principal_released'], 'sale principal')
                if principal <= 0 or principal > frozen.get(instrument, Decimal(0)):
                    raise ValueError('sale principal exceeds retained principal')
                frozen[instrument] -= principal
                cash += amount
            elif kind == 'repo_open':
                cash -= amount
                repos[instrument] = repos.get(instrument, Decimal(0)) + amount
            elif kind == 'repo_principal':
                if amount > repos.get(instrument, Decimal(0)):
                    raise ValueError('repo return exceeds principal')
                repos[instrument] -= amount
                cash += amount
            else:
                if instrument not in repos:
                    raise ValueError('repo interest requires an opened repo')
                cash += amount
            rows.append(dict(date=day.isoformat(), order=rank, event_id=identity, kind=kind,
                             available_cash=float(cash), ipo_principal=float(sum(frozen.values())),
                             repo_principal=float(sum(repos.values()))))
    return dict(schema_version='0.2-alpha', executable=not conflicts, conflicts=conflicts, events=rows,
                final_available_cash=float(cash), outstanding_ipo_principal=float(sum(frozen.values())),
                outstanding_repo_principal=float(sum(repos.values())),
                calendar_basis=calendar.basis,
                warnings=['Explicit input events only; no automatic order selection or trading.',
                          'Without complete same-day timing, commitments precede releases.',
                          'Source records and calendar completeness require independent review.'])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode', choices=['facts', 'ledger', 'repo'])
    parser.add_argument('input')
    parser.add_argument('--output')
    args = parser.parse_args()
    data = load(args.input)
    if args.mode == 'repo':
        out = repo_interest(data['trade'], Calendar(data['calendar']))
    else:
        out = {'facts': facts, 'ledger': ledger}[args.mode](data)
    content = json.dumps(out, ensure_ascii=False, indent=2, allow_nan=False)
    if args.output:
        with open(args.output, 'x', encoding='utf-8') as f:
            f.write(content + '\n')
    else:
        print(content)


if __name__ == '__main__':
    main()
