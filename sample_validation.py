"""One public issuance with hypothetical budget cases; no multiplication of real sample counts."""
from decimal import Decimal
from audit import load
from public_sample import replay_sample
from research import ledger
from trading_calendar import build_calendar


def validate_sample(spec):
    base=load(spec['sample_input'])
    cases=[]
    for budget in ('3000000.00','4500000.00','10000000.00'):
        parameters=dict(base,budget=budget)
        result,_=replay_sample(parameters)
        retained=Decimal(result['proportional_shares'])*Decimal(str(result['reviewed_fields']['issue_price']['value']))
        extra=None
        quoted=Decimal(result['quoted_allocation_fraction'])
        continuous=Decimal(result['subscribed_shares'])*quoted
        if continuous>result['proportional_shares'] and result['proportional_shares']+100<=result['subscribed_shares']:
            extra=dict(assumed_total_shares=result['proportional_shares']+100,
                       retained_principal=str(retained+Decimal('100')*Decimal(str(result['reviewed_fields']['issue_price']['value']))),
                       actual_difference='unknown_not_observed',probability=None)
        cases.append(dict(hypothetical_budget=budget,proportional_shares=result['proportional_shares'],
                          actual_individual_shares='unknown',conditional_extra_100=extra))
    full,_=replay_sample(base)
    ev={'basis':'assumption','source':'Teaching second issuance and refund availability, not an account record'}
    first=full['reviewed_fields']['subscription_date']['value'];refund=full['reviewed_fields']['announced_refund_date']['value']
    frozen=Decimal(full['frozen_amount']);retained=Decimal(full['proportional_shares'])*Decimal(str(full['reviewed_fields']['issue_price']['value']))
    conflict=ledger(dict(initial_cash=base['capital'],calendar=build_calendar(load(base['calendar_schedule'])),events=[
        dict(id='A-freeze',instrument='920188-reconstruction',date=first,kind='freeze',amount=str(frozen),evidence=ev),
        dict(id='A-refund',instrument='920188-reconstruction',date=refund,kind='refund',amount=str(frozen-retained),evidence=ev),
        dict(id='B-freeze',instrument='TEACHING-B',date=refund,kind='freeze',amount='6000000',evidence=ev)]))
    return dict(mode='bounded_public_sample_validation',real_issuance_count=1,hypothetical_budget_case_count=len(cases),
                security=full['security'],cases=cases,teaching_multi_issue_conflict=conflict,
                actual_scope='One saved reviewed public issuance; offline source bytes not newly checked',
                remaining_gaps=['Real individual zero-allocation and residual differences not observed.',
                                'Second issuance and same-day refund availability are teaching assumptions.',
                                'Historical reconstruction, not pre-subscription prediction validation.',
                                'Real-account acceptance remains paused; no yearly coverage or new model.'])
