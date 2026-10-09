"""Explicit joint scenarios for Beijing Stock Exchange IPO research (CNY)."""
import argparse
import json
import math
from audit import load
from datetime import date
from decimal import Decimal, ROUND_FLOOR


def number(value, name, minimum=0):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{name}: expected numeric value")
    if not math.isfinite(value) or value < minimum:
        raise ValueError(f"{name}: invalid value")
    return value


def proceeds_metrics(shares, price, gain, frozen_amount, start, refund, sale, annual_rate, fees):
    retained = shares * price
    proceeds = retained * (1 + gain)
    sell_cost = (max(proceeds * fees['commission_rate'], fees['minimum_commission']) +
                 proceeds * (fees['stamp_rate'] + fees['transfer_rate'])) if shares else 0
    capital_days = frozen_amount * (refund - start).days + retained * (sale - refund).days
    cash_cost = capital_days * annual_rate / 365
    gross = retained * gain
    breakeven = None
    if shares:
        proportional = fees['stamp_rate'] + fees['transfer_rate']
        # Solve each commission branch, rather than adding minimum commission twice.
        required_proceeds = (retained + cash_cost) / (1 - proportional - fees['commission_rate'])
        if required_proceeds * fees['commission_rate'] < fees['minimum_commission']:
            required_proceeds = (retained + cash_cost + fees['minimum_commission']) / (1 - proportional)
        breakeven = required_proceeds / retained - 1
    return dict(gross_profit=gross, sell_cost=sell_cost, cash_cost=cash_cost,
                capital_days=capital_days, net_profit=gross-sell_cost-cash_cost,
                cash_profit_before_opportunity_cost=gross-sell_cost,
                breakeven_listing_return=breakeven)


def evaluate(data):
    capital = number(data['capital'], 'capital', 0.01)
    price = number(data['issue_price'], 'issue_price', 0.01)
    budget = number(data['budget'], 'budget')
    maximum = number(data['max_subscription_shares'], 'max_subscription_shares')
    if maximum != int(maximum) or maximum % 100:
        raise ValueError('max_subscription_shares must be a multiple of 100')
    if budget > capital:
        raise ValueError('budget exceeds capital')
    subscribed = min(int((Decimal(str(budget)) / (Decimal(str(price)) * 100)).to_integral_value(rounding=ROUND_FLOOR)) * 100, int(maximum))
    amount = subscribed * price
    start = date.fromisoformat(data['subscription_date'])
    refund = date.fromisoformat(data['refund_available_date'])
    sale = date.fromisoformat(data['sale_cash_available_date'])
    if not start < refund <= sale:
        raise ValueError('require subscription < refund <= sale cash date')
    rate = number(data['annual_cash_cost_rate'], 'annual_cash_cost_rate')
    fees = data['fees']
    for key in ('commission_rate', 'minimum_commission', 'stamp_rate', 'transfer_rate'):
        number(fees[key], key)
    if fees['commission_rate'] + fees['stamp_rate'] + fees['transfer_rate'] >= 1:
        raise ValueError('Combined proportional sell fee must be below 100%')
    scenarios = data['scenarios']
    if not scenarios or len(scenarios) > 100:
        raise ValueError('require 1..100 scenarios')
    weighted = any('probability' in s for s in scenarios)
    if weighted:
        if not all('probability' in s for s in scenarios) or not data.get('probability_basis'):
            raise ValueError('weights require every probability and probability_basis')
        if not math.isclose(sum(number(s['probability'], 'probability') for s in scenarios), 1, abs_tol=1e-9):
            raise ValueError('probabilities must sum to 1')
    rows = []
    ids = set()
    for s in scenarios:
        if not isinstance(s['id'], str) or not s['id'] or s['id'] in ids:
            raise ValueError('scenario ids must be nonempty and unique')
        ids.add(s['id'])
        allocation_rate = number(s['allocation_rate'], 'allocation_rate')
        if allocation_rate > 1:
            raise ValueError('allocation_rate exceeds 1')
        gain = number(s['listing_return'], 'listing_return', -1)
        if not s.get('basis'):
            raise ValueError('each scenario requires basis')
        continuous_hands = Decimal(subscribed) * Decimal(str(allocation_rate)) / 100
        hands = int(continuous_hands.to_integral_value(rounding=ROUND_FLOOR))
        shares = hands * 100
        metrics = proceeds_metrics(shares, price, gain, amount, start, refund, sale, rate, fees)
        residual = None
        if continuous_hands > hands and shares + 100 <= subscribed:
            residual = dict(assumed_total_shares=shares+100,
                            **proceeds_metrics(shares+100, price, gain, amount, start, refund, sale, rate, fees))
        rows.append(dict(id=s['id'], probability=s.get('probability'), allocation_rate=allocation_rate,
                         listing_return=gain, proportional_hands=hands,
                         proportional_shares=shares, **metrics,
                         residual_extra_100_share_sensitivity=residual,
                         account_period_return=metrics['net_profit']/capital, basis=s['basis']))
    result = dict(schema_version='0.1', subscribed_shares=subscribed, frozen_amount=amount,
                  assumptions=dict(capital=capital, requested_budget=budget, issue_price=price,
                                   annual_cash_cost_rate=rate, fees=fees,
                                   subscription_date=start.isoformat(), refund_available_date=refund.isoformat(),
                                   sale_cash_available_date=sale.isoformat()),
                  scenarios=rows, warnings=['Proportional whole lots only; residual allocation is unknown.',
                  'Extra-100-share sensitivity is conditional, not a probability, bound or guaranteed allocation.',
                  'Scenario inputs and probabilities are assumptions, not calibrated forecasts.',
                  'Cash costs use explicit dates and a simple annual rate; repo alternatives require a separate ledger.'])
    if weighted:
        mean_h = sum(r['probability'] * r['proportional_hands'] for r in rows)
        mean_n = sum(r['probability'] * r['net_profit'] for r in rows)
        result['weighted'] = dict(expected_proportional_hands=mean_h,
            sd_proportional_hands=math.sqrt(sum(r['probability']*(r['proportional_hands']-mean_h)**2 for r in rows)),
            probability_zero_proportional_hands=sum(r['probability'] for r in rows if not r['proportional_hands']),
            expected_net_profit=mean_n,
            sd_net_profit=math.sqrt(sum(r['probability']*(r['net_profit']-mean_n)**2 for r in rows)),
            probability_net_loss=sum(r['probability'] for r in rows if r['net_profit'] < 0),
            probability_basis=data['probability_basis'])
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('input')
    parser.add_argument('--output')
    args = parser.parse_args()
    result = evaluate(load(args.input))
    content = json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False)
    if args.output:
        with open(args.output, 'x', encoding='utf-8') as f:
            f.write(content + '\n')
    else:
        print(content)


if __name__ == '__main__':
    main()
