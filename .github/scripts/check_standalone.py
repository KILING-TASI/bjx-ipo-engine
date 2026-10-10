"""One-repository archive + non-editable wheel acceptance in a fresh virtualenv."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import venv
import zipfile

ROOT = Path(__file__).resolve().parents[2]

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--out-dir', required=True)
    args = parser.parse_args()
    out = Path(args.out_dir).resolve()
    out.mkdir(exist_ok=False, parents=True)
    env = {k: v for k,v in os.environ.items() if not (k.upper().startswith(('PYTHON','RESEARCH_WORKBENCH','CODEX','BJX')) or k.upper() in ('HOME','USERPROFILE','APPDATA','LOCALAPPDATA','XDG_CACHE_HOME'))}
    home = out/'empty-home'; home.mkdir()
    for key in ('HOME','USERPROFILE','APPDATA','LOCALAPPDATA','XDG_CACHE_HOME'):
        env[key] = str(home)
    env.update(PYTHONUTF8='1', PYTHONIOENCODING='utf-8', PIP_NO_CACHE_DIR='1', PIP_CONFIG_FILE=os.devnull)
    records=[]
    def run(argv, cwd, expected=0, stdin=None):
        p=subprocess.run([str(a) for a in argv],cwd=cwd,env=env,input=stdin,text=True,encoding='utf-8',capture_output=True)
        records.append(dict(command=[str(a) for a in argv],cwd=str(cwd),exit=p.returncode,stdout=p.stdout,stderr=p.stderr))
        if (expected==0 and p.returncode!=0) or (expected!=0 and p.returncode==0):
            raise AssertionError(records[-1])
        return p.stdout
    archive=out/'source.zip'
    run(['git','archive','--format=zip','--output',archive,'HEAD'],ROOT)
    source=out/'source';source.mkdir()
    with zipfile.ZipFile(archive) as z:
        for name in z.namelist():
            if name.startswith(('.git/','local-data/')) or name.endswith(('.pdf','.env')):
                raise AssertionError('Unexpected private/raw asset '+name)
        z.extractall(source)
    venv.EnvBuilder(with_pip=True).create(out/'venv')
    py=out/'venv'/('Scripts/python.exe' if os.name=='nt' else 'bin/python')
    run([py,'-I','-m','pip','install','setuptools>=77'],out)
    wheels=out/'wheels'
    run([py,'-I','-m','pip','wheel','--no-deps','--no-build-isolation',source,'--wheel-dir',wheels],out)
    wheel=next(wheels.glob('*.whl'))
    run([py,'-I','-m','pip','install','--no-deps',wheel],out)
    origins=json.loads(run([py,'-I','-c',"import sys,json,engine,api,audit,research,public_sample; print(json.dumps({'sys_path':sys.path,'origins':{m.__name__:m.__file__ for m in [engine,api,audit,research,public_sample]},'version':audit.METHOD_VERSION}))"],out))
    assert all(Path(v).resolve().is_relative_to(out/'venv') for v in origins['origins'].values())
    assert not any('research-workbench' in p or
                   (p and Path(p).resolve().is_relative_to(ROOT) and
                    not Path(p).resolve().is_relative_to(out))
                   for p in origins['sys_path'])
    scenario=json.loads((source/'examples/scenarios.json').read_bytes())
    request=json.dumps({'api_version':'1.0','operation':'scenario.v1','input':scenario})
    response=json.loads(run([py,'-I','-m','api'],out,stdin=request))
    assert response['result'] is not None and response['api_version']=='1.0'
    (out/'installed-api-result.json').write_text(json.dumps(response,ensure_ascii=False,indent=2),encoding='utf-8')
    run([py,'-S','demo.py','--out-dir',out/'report'],source)
    demo_origins=json.loads(run([py,'-S','-c',"import json,sys,demo,engine,audit;print(json.dumps({'sys_path':sys.path,'origins':{m.__name__:m.__file__ for m in [demo,engine,audit]}}))"],source))
    assert all(Path(v).resolve().is_relative_to(source) for v in demo_origins['origins'].values())
    run([py,'-S','demo.py','--out-dir',out/'report'],source,expected=1)
    run([py,'-I','-c','import pypdf'],out,expected=1)
    # Exercise the actual optional-PDF entry with a harmless local placeholder.
    spec=json.loads((source/'examples/public-sample.json').read_bytes())
    placeholder=source/'missing-optional.pdf';placeholder.write_bytes(b'%PDF-placeholder-not-an-original')
    spec['source_files']={key:str(placeholder) for key in ('offer','result','listing')}
    optional=source/'optional-input.json';optional.write_text(json.dumps(spec),encoding='utf-8')
    failure=run([py,'-S','bjx.py','public-sample',optional,'--out-dir',out/'optional-failure'],source,expected=1)
    blocked=json.loads((out/'optional-failure/result.json').read_bytes())
    assert 'pypdf' in json.dumps(blocked) and 'blocked' in failure
    manifest=json.loads((out/'report/preview-manifest.json').read_bytes())
    for name,digest in manifest['files'].items():
        assert hashlib.sha256((out/'report'/name).read_bytes()).hexdigest()==digest
    result=json.loads((out/'report/result.json').read_bytes())
    assert result['public_reference']['gross_interest_cent']=='11.44'
    assert result['public_reference']['net_reference_interest']=='10.44'
    assert manifest['real_issuance_count']==1 and manifest['visual_review']=='not_performed_at_generation'
    run([py,'-S','.github/scripts/check_docs.py'],source)
    with zipfile.ZipFile(wheel) as z:
        assert any(n.endswith('/LICENSE') for n in z.namelist())
        assert any(n.endswith('research-workbench-MIT.txt') for n in z.namelist())
        assert any(n.endswith('THIRD_PARTY_NOTICES.md') for n in z.namelist())
    receipt={'scope':'isolated directories/processes on existing host, not a fresh OS','status':'archive-demo-and-installed-wheel-api-passed','source_commit':run(['git','rev-parse','HEAD'],ROOT).strip(),'archive_sha256':hashlib.sha256(archive.read_bytes()).hexdigest(),'wheel_sha256':hashlib.sha256(wheel.read_bytes()).hexdigest(),'origins':origins,'demo_origins':demo_origins,'installed_dependencies':run([py,'-I','-m','pip','list','--format=json'],out),'commands':records,'limits':['Wheel is calculation modules only; README demo requires the standalone source archive, not another repository','No live acquisition, optional PDF success, Skill discovery or visual acceptance','Released versions not tested in this batch; prior archive CI is separate evidence']}
    (out/'acceptance.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2),encoding='utf-8')
    print('Standalone source demo and non-editable wheel API passed; boundaries recorded')

if __name__=='__main__':main()
