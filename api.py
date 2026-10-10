"""Versioned calculation contract for callers; delegates unchanged legacy implementations."""
from audit import MAX_BYTES, METHOD_VERSION, digest, encoded, loads
from engine import evaluate
from research import ledger

API_VERSION='1.0'
OPERATIONS={'scenario.v1':evaluate,'cash_ledger.v1':ledger}

# API v1 keeps its frozen machine envelope; direct research/CLI reports use Chinese.
LEGACY_WARNINGS={
    '仅计算比例整手获配；个人余股获配仍未知。':'Proportional whole lots only; residual allocation is unknown.',
    '额外100股仅为条件敏感性情景，不是概率、上下界或保证获配。':'Extra-100-share sensitivity is conditional, not a probability, bound or guaranteed allocation.',
    '情景参数与概率是输入假设，不是经过校准的预测。':'Scenario inputs and probabilities are assumptions, not calibrated forecasts.',
    '现金成本按明确日期与简单年率计算；回购替代方案需另建现金账。':'Cash costs use explicit dates and a simple annual rate; repo alternatives require a separate ledger.',
    '仅处理明确输入的事件；不自动选择申购顺序或执行交易。':'Explicit input events only; no automatic order selection or trading.',
    '同日时序不完整时，按先承诺支出、后释放资金处理。':'Without complete same-day timing, commitments precede releases.',
    '来源记录与日历完整性需另行核对。':'Source records and calendar completeness require independent review.',
}


def calculate(request):
    try:
        if not isinstance(request,dict) or set(request)!={'api_version','operation','input'}:
            raise ValueError('Request requires exactly api_version, operation and input')
        if request['api_version']!=API_VERSION or request['operation'] not in OPERATIONS:
            raise ValueError('Unsupported API version or operation')
        if not isinstance(request['input'],dict):raise ValueError('Calculation input must be an object')
        checksum=digest(encoded(request['input']))
        result=OPERATIONS[request['operation']](request['input'])
        if 'warnings' in result:result['warnings']=[LEGACY_WARNINGS.get(w,w) for w in result['warnings']]
        encoded(result)  # Reject nonfinite computed output without silently substituting zero.
        status='infeasible' if request['operation']=='cash_ledger.v1' and not result['executable'] else 'completed_with_limits'
        return dict(api_version=API_VERSION,engine_version=METHOD_VERSION,operation=request['operation'],status=status,
                    input_sha256=checksum,result=result,error=None,
                    scope='Exact legacy delegation; source verification and account acceptance not performed')
    except (ValueError,KeyError,TypeError,ArithmeticError) as exc:
        return dict(api_version=API_VERSION,engine_version=METHOD_VERSION,status='failed',
                    result=None,input_sha256=None,error=dict(kind=type(exc).__name__,message=str(exc)),
                    scope='No partial result promoted to success')


def main():
    import sys
    try:
        payload=sys.stdin.buffer.read(MAX_BYTES+1)
        if len(payload)>MAX_BYTES:raise ValueError('Request exceeds 10 MiB')
        request=loads(payload.decode('utf-8-sig'))
        response=calculate(request)
    except (ValueError,UnicodeError) as exc:
        response=dict(api_version=API_VERSION,engine_version=METHOD_VERSION,status='failed',result=None,
                      input_sha256=None,error=dict(kind=type(exc).__name__,message=str(exc)))
    sys.stdout.buffer.write(encoded(response))
    return 2 if response['status']=='failed' else 0


if __name__=='__main__':
    import sys
    sys.exit(main())
