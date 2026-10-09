"""Replay reviewed public issuance fields; optional exact-source rechecking, no accounts."""
from datetime import date
from decimal import Decimal, ROUND_FLOOR
from io import BytesIO
from pathlib import Path
import re
from audit import MAX_BYTES, digest, load
from research import Calendar, ledger, money
from trading_calendar import build_calendar


def replay_sample(spec):
    sample=load(spec['sample'])
    if sample['record_kind']!='historical_public_sample':
        raise ValueError('Historical public sample required')
    required={'issue_price','max_subscription_shares','online_issue_shares','effective_subscription_shares','online_allocation_rate','subscription_date','announced_refund_date','listing_date'}
    if set(sample['fields'])!=required:
        raise ValueError('Selected public field set is incomplete')
    fields=sample['fields'];documents=sample['documents']
    for field in fields.values():
        if field['source_id'] not in documents or field['review_status']!='selected_page_image_and_text_reviewed':
            raise ValueError('Selected field lacks recorded source review')
    for name,field in fields.items():
        if name.endswith('_date'):
            d=date.fromisoformat(field['value']);expected=f'{d.year}年{d.month}月{d.day}日';unit='date'
        elif name.endswith('_shares'):
            value=money(field['value'],name)
            if value!=int(value):raise ValueError('Public share counts must be integers')
            expected=format(int(value),',');unit='shares'
        elif name=='online_allocation_rate':
            expected=format(money(field['value'],name)*100,'.10f')+'%';unit='fraction'
        else:
            expected=str(field['value']);unit='CNY/share'
        if field['unit']!=unit or expected!=field['text_anchor']:
            raise ValueError('Stored public value/unit differs from its reviewed anchor')
    artifacts={}
    verification='saved_review_record_not_rechecked'
    if 'source_files' in spec:
        if set(spec['source_files'])!=set(documents):
            raise ValueError('All original sample source files must be supplied')
        from pypdf import PdfReader
        from pypdf.errors import PyPdfError
        for index,(ident,document) in enumerate(documents.items()):
            path=Path(spec['source_files'][ident])
            if path.stat().st_size>MAX_BYTES:raise ValueError('Source exceeds 10 MiB')
            blob=path.read_bytes()
            if digest(blob)!=document['sha256']:raise ValueError('Public sample source hash changed')
            try:reader=PdfReader(BytesIO(blob));texts=[re.sub(r'\s+','',p.extract_text() or '') for p in reader.pages]
            except PyPdfError as exc:raise ValueError('Original PDF could not be parsed') from exc
            opening=''.join(texts[:5])
            if sample['issuer_name'] not in opening or sample['security'] not in opening:
                raise ValueError('Original issuer/code does not match sample')
            for field in fields.values():
                if field['source_id']==ident:
                    if not 1<=field['page']<=len(texts) or field['text_anchor'] not in texts[field['page']-1]:
                        raise ValueError('Selected field anchor differs from saved source review')
            artifacts[f'original-{index:03d}.pdf']=blob
        verification='exact_hash_and_selected_text_match'
    price=money(fields['issue_price']['value'],'price')
    maximum=money(fields['max_subscription_shares']['value'],'max shares')
    q=money(fields['online_issue_shares']['value'],'online issue shares')
    effective=money(fields['effective_subscription_shares']['value'],'effective subscriptions')
    quoted=money(fields['online_allocation_rate']['value'],'allocation fraction')
    if price<=0 or effective<=0 or q<=0 or q>effective or maximum!=int(maximum) or maximum%100 or not 0<quoted<=1:
        raise ValueError('Public issuance values inconsistent')
    recomputed=q/effective
    # Announcement quotes percentage to 10 decimal places: fraction tolerance 5e-13.
    if abs(recomputed-quoted)>Decimal('0.0000000000005'):
        raise ValueError('Reported rate differs from same-scope public share counts')
    capital=money(spec['capital'],'hypothetical capital');budget=money(spec['budget'],'hypothetical budget')
    if capital<=0 or budget>capital:raise ValueError('Invalid hypothetical budget')
    n=min(int((budget/(price*100)).to_integral_value(rounding=ROUND_FLOOR))*100,int(maximum))
    proportional=int((Decimal(n)*quoted/100).to_integral_value(rounding=ROUND_FLOOR))*100
    frozen=Decimal(n)*price
    refund_assumption=spec.get('refund_available_date_assumption')
    cash=None;cost=None
    if refund_assumption is not None:
        start=date.fromisoformat(fields['subscription_date']['value'])
        refund=date.fromisoformat(refund_assumption)
        announced=date.fromisoformat(fields['announced_refund_date']['value'])
        end=date.fromisoformat(spec['observation_end'])
        if not start<refund<=end or refund<announced:raise ValueError('Explicit refund availability assumption invalid')
        calendar=build_calendar(load(spec['calendar_schedule']))
        for d in (start,refund,end):Calendar(calendar).check(d)
        ev={'basis':'assumption','source':'Hypothetical budget and refund availability, not a real account'}
        events=[]
        if frozen>0:events.append(dict(id='freeze',instrument=sample['security'],date=start.isoformat(),kind='freeze',amount=str(frozen),evidence=ev))
        retained=Decimal(proportional)*price
        if frozen>retained:events.append(dict(id='refund',instrument=sample['security'],date=refund.isoformat(),kind='refund',amount=str(frozen-retained),evidence=ev))
        cash=ledger(dict(initial_cash=str(capital),calendar=calendar,events=events))
        days=frozen*(refund-start).days+retained*(end-refund).days
        annual=money(spec['opportunity_cost_rate_assumption'],'opportunity rate')
        cost=dict(capital_days=str(days),declared_rate=str(annual),opportunity_cost=str(days*annual/365),retained_principal=str(retained),observation_end=end.isoformat(),sale_or_actual_profit='not_computed')
    return dict(mode='historical_public_sample_reconstruction',security=sample['security'],name=sample['name'],
                record_kind='historical_reconstruction_not_prediction',source_verification=verification,
                reviewed_fields=fields,documents=documents,quoted_allocation_fraction=str(quoted),recomputed_allocation_fraction=str(recomputed),
                hypothetical_capital=str(capital),hypothetical_budget=str(budget),subscribed_shares=n,frozen_amount=str(frozen),
                proportional_shares=proportional,individual_actual_allocation='unknown',residual_allocation='unknown',
                cash_reconstruction=cash,opportunity_cost_assumption=cost,
                limitations=sample['limitations']+['Actual published market allocation rate is not a personal account allotment.',
                 'Refund cash date is explicitly assumed, not inferred from T+2 or certified from broker records.',
                 'No sale proceeds, first-day profit or annual return is claimed.']),artifacts
