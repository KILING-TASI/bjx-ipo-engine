"""Versioned calculation contract for callers; delegates unchanged legacy implementations."""
from audit import MAX_BYTES, METHOD_VERSION, digest, encoded, loads
from engine import evaluate
from research import ledger

API_VERSION='1.0'
OPERATIONS={'scenario.v1':evaluate,'cash_ledger.v1':ledger}


def calculate(request):
    try:
        if not isinstance(request,dict) or set(request)!={'api_version','operation','input'}:
            raise ValueError('Request requires exactly api_version, operation and input')
        if request['api_version']!=API_VERSION or request['operation'] not in OPERATIONS:
            raise ValueError('Unsupported API version or operation')
        if not isinstance(request['input'],dict):raise ValueError('Calculation input must be an object')
        checksum=digest(encoded(request['input']))
        result=OPERATIONS[request['operation']](request['input'])
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
