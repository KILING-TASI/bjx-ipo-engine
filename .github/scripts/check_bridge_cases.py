"""Frozen native-contract cases; optional external bridge on identical stdin bytes."""
import argparse
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from audit import MAX_BYTES, digest, encoded, load, loads, publish


def check(bridge_command=None):
    fixture = load(ROOT/'examples/bridge-cases.json')
    records = []
    if bridge_command is not None and (not isinstance(bridge_command, list) or not bridge_command or
                                       not all(isinstance(arg, str) and arg for arg in bridge_command)):
        raise ValueError('External bridge command must be a nonempty JSON string array; no shell')
    for case in fixture['cases']:
        payload = encoded(case['request'])
        if digest(payload) != case['request_sha256']:
            raise ValueError('Frozen request hash differs: '+case['id'])
        expected = case['expected_response']
        outcomes = {}
        commands = [('native', [sys.executable, '-S', str(ROOT/'api.py')])]
        if bridge_command:
            commands.append(('workbench_bridge', bridge_command))
        for label, command in commands:
            run = subprocess.run(command, input=payload, capture_output=True, timeout=20, cwd=ROOT)
            if len(run.stdout) > MAX_BYTES:
                raise ValueError('Bridge output exceeds limit')
            response = loads(run.stdout.decode('utf-8-sig'))
            envelope = response.get('engine_response', response)
            if envelope != expected:
                raise ValueError(label+' full response differs: '+case['id'])
            if label == 'native' and run.returncode != (2 if expected['status']=='failed' else 0):
                raise ValueError('Native failure exit differs: '+case['id'])
            outcomes[label] = {'exit_code':run.returncode,'response':response,
                               'stdout_sha256':digest(run.stdout),'stderr':run.stderr.decode('utf-8', errors='replace')}
        records.append({'id':case['id'],'request':case['request'],'request_sha256':case['request_sha256'],
                        'status':expected['status'],'full_response_equal':True,'runs':outcomes})
    return fixture, {'schema_version':'bridge-check.v1','cases':records,'case_count':len(records),
                     'scope':'same native request and full envelope; no legacy annual/mapping equivalence',
                     'workbench_checked':bool(bridge_command),'real_sample_count':0}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--bridge-command-json', help='Explicit optional JSON argv; expects stdin JSON and engine_response envelope')
    parser.add_argument('--out-dir')
    args=parser.parse_args()
    if args.out_dir and Path(args.out_dir).exists():
        parser.error('Output directory exists; preserve frozen results')
    command=json.loads(args.bridge_command_json) if args.bridge_command_json else None
    try:
        fixture,result=check(command)
    except (ValueError, KeyError, TypeError, UnicodeError, OSError, subprocess.SubprocessError) as exc:
        if args.out_dir:
            publish(Path(args.out_dir),'bridge-check',{'bridge_command':command},
                    {'status':'blocked','message':str(exc),'next_step':'Inspect the external bridge protocol; retain failure and retry in a new directory.',
                     'error':{'kind':type(exc).__name__,'message':str(exc)},
                     'workbench_checked':False,'scope':'No mismatched or failed run certified as equivalent'},status='blocked')
        print(json.dumps({'status':'blocked','error':str(exc)}))
        return 2
    if args.out_dir:
        publish(Path(args.out_dir),'bridge-check',{'fixture':fixture,'bridge_command':command},result)
    print(json.dumps({'case_count':result['case_count'],'workbench_checked':result['workbench_checked'],'status':'matched_frozen_native_contract'}))
    return 0


if __name__=='__main__':
    sys.exit(main())
