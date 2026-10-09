"""Separate local assumption snapshots from subsequently declared public results."""
from datetime import datetime, timezone
from pathlib import Path
from audit import bind_fact_sources, digest, encoded, load, verify
from engine import evaluate, number
from decimal import Decimal
from research import facts, text
from comparison import compare_cash

FIELDS = {'issue_price', 'max_subscription_shares', 'effective_subscription_shares', 'online_issue_shares',
          'online_allocation_rate', 'subscription_date', 'announced_refund_date', 'listing_date'}


def timestamp(value):
    stamp = datetime.fromisoformat(value)
    if stamp.utcoffset() is None:
        raise ValueError('Timestamp requires explicit timezone')
    return stamp


def freeze(spec):
    text(spec['security'], 'security')
    kind = spec['input_kind']
    if kind not in ('teaching', 'scenario', 'historical_reconstruction'):
        raise ValueError('Only teaching, declared scenario or historical reconstruction supported')
    now = datetime.now(timezone.utc)
    cutoff, subscription = timestamp(spec['information_cutoff']), timestamp(spec['subscription_at'])
    if cutoff > now or cutoff >= subscription:
        raise ValueError('Information cutoff must be no later than now and before subscription')
    sources = spec['information_sources']
    if not isinstance(sources, list) or not sources:
        raise ValueError('Information sources with availability clocks required')
    ids = set()
    for source in sources:
        ident = text(source['id'], 'source id')
        if ident in ids:
            raise ValueError('Duplicate information source id')
        ids.add(ident)
        text(source['basis'], 'information basis')
        if timestamp(source['available_at']) > cutoff:
            raise ValueError('Source unavailable at declared information cutoff')
    assumptions = spec['assumptions']
    result = evaluate(assumptions)
    if assumptions['subscription_date'] != subscription.date().isoformat():
        raise ValueError('Assumption subscription date differs from declared subscription timestamp')
    past = now >= subscription or kind == 'historical_reconstruction'
    return dict(mode='local_assumption_snapshot', security=spec['security'], input_kind=kind,
                frozen_at=now.isoformat(), information_cutoff=cutoff.isoformat(),
                subscription_at=subscription.isoformat(),
                record_kind='historical_reconstruction' if past else 'local_pre_subscription_snapshot',
                assumptions_sha256=digest(encoded(assumptions)), frozen_assumptions=assumptions,
                scenario_result=result, information_sources=sources,
                externally_timestamped=False,
                warnings=['Local clock and hashes are not externally trusted timestamps.',
                          'Declared source clocks do not prove all assumptions were knowable then.',
                          'Historical reconstructions are excluded from genuine prediction evidence.'])


def archive(spec):
    if set(spec['fields']) - FIELDS:
        raise ValueError('Archive covers public issuance fields only, not account data')
    if spec['input_kind'] not in ('teaching', 'public_disclosure'):
        raise ValueError('Real-account acceptance remains paused')
    data = dict(spec, required_fields=sorted(FIELDS))
    result, artifacts = bind_fact_sources(data, facts(data))
    result.update(mode='public_issuance_archive', input_kind=spec['input_kind'],
                  recorded_at=datetime.now(timezone.utc).isoformat(),
                  residual_allocation='unknown',
                  refund_boundary='Announced refund date is not broker cash availability')
    if spec['input_kind'] == 'public_disclosure':
        for field in result['fields'].values():
            for c in field['candidates']:
                if c['basis'] != 'original' or not c.get('source_id'):
                    raise ValueError('Public archive candidates require original source binding')
    return result, artifacts


def review(spec):
    frozen_root, actual_root = Path(spec['frozen_bundle']), Path(spec['actual_bundle'])
    verify(frozen_root)
    verify(actual_root)
    frozen, actual = load(frozen_root/'result.json'), load(actual_root/'result.json')
    if frozen.get('mode') != 'local_assumption_snapshot' or actual.get('mode') != 'public_issuance_archive':
        raise ValueError('Review requires separate successful freeze and public archive bundles')
    if frozen['security'] != actual['security']:
        raise ValueError('Frozen and actual securities differ')
    if digest(encoded(frozen['frozen_assumptions'])) != frozen['assumptions_sha256']:
        raise ValueError('Frozen assumptions digest mismatch')
    expected = spec['comparison_values']
    if set(expected) - {'issue_price', 'online_allocation_rate'}:
        raise ValueError('Only issue price and online allocation rate comparisons supported initially')
    entries = []
    for name, claim in expected.items():
        # The comparison baseline must itself be present in the frozen assumptions.
        value, unit = claim['value'], claim['unit']
        if name == 'issue_price':
            matches = value == frozen['frozen_assumptions']['issue_price'] and unit == 'CNY/share'
        else:
            matches = unit == 'fraction' and any(value == s['allocation_rate'] for s in frozen['frozen_assumptions']['scenarios'])
        if not matches:
            raise ValueError('Comparison value must match frozen assumptions and declared unit')
        field = actual['fields'][name]
        candidates = field['candidates']
        comparable = field['status'] == 'recorded_unverified' and all(c['unit'] == unit for c in candidates)
        actual_value = candidates[0]['value'] if comparable else None
        if comparable and (isinstance(actual_value, bool) or not isinstance(actual_value, (int,float))):
            raise ValueError('Comparable actual value must be numeric')
        entries.append(dict(field=name, frozen_value=value, unit=unit,
                            declared_actual_value=actual_value, source_status=field['status'],
                            signed_error_frozen_minus_actual=value-actual_value if comparable else None))
    cash = None
    opportunity = None
    if 'cash_comparison' in spec:
        if spec.get('cash_basis') not in ('teaching', 'public_proportional_reconstruction'):
            raise ValueError('Only teaching/public proportional cash reconstruction; account acceptance paused')
        cash = compare_cash(spec['cash_comparison'])
        if 'opportunity_cost_rate' in spec:
            rate=number(spec['opportunity_cost_rate'],'opportunity cost rate')
            if rate != frozen['frozen_assumptions']['annual_cash_cost_rate']:
                raise ValueError('Opportunity rate must match frozen assumption')
            opportunity=[]
            for plan in cash['plans']:
                cost=Decimal(plan['locked_capital_days'])*Decimal(str(rate))/365 if plan['locked_capital_days'] is not None else None
                net=Decimal(plan['realized_cash_profit'])-cost if cost is not None and plan['realized_cash_profit'] is not None else None
                opportunity.append(dict(plan=plan['id'],declared_rate=rate,opportunity_cost=str(cost) if cost is not None else None,
                                        cash_profit_less_opportunity_cost=str(net) if net is not None else None))
    elif 'opportunity_cost_rate' in spec:
        raise ValueError('Opportunity-cost sensitivity requires an explicit cash plan')
    return dict(mode='separate_assumption_actual_review', security=frozen['security'],
                frozen_record_kind=frozen['record_kind'], comparisons=entries,
                evidence_scope='declared_values_not_verified_prediction_accuracy',
                frozen_result_sha256=digest((frozen_root/'result.json').read_bytes()),
                actual_result_sha256=digest((actual_root/'result.json').read_bytes()),
                frozen_input_sha256=digest((frozen_root/'input.json').read_bytes()),
                actual_input_sha256=digest((actual_root/'input.json').read_bytes()),
                frozen_at=frozen['frozen_at'], actual_recorded_at=actual['recorded_at'],
                cash_reconstruction=cash, opportunity_cost_sensitivity=opportunity, residual_allocation='unknown',
                warnings=['Actual results never replace frozen assumptions.',
                          'Unverified candidates, conflicts and missing values do not become verified facts.',
                          'Cash comparison is a separate explicit plan, not automatically derived from archive facts.',
                          'Opportunity sensitivity is separate; never subtract it again from the cash-alternative difference.',
                          'No genuine prediction score, yearly backtest, return guarantee or real-account acceptance.'])
