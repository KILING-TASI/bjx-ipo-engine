"""Short offline demo: real public field record, hypothetical cash and teaching risk."""
import argparse
from datetime import datetime, timezone, timedelta
import html
from pathlib import Path
import tempfile
from audit import METHOD_VERSION, digest, encoded, load
from engine import evaluate
from public_sample import replay_sample
from sample_validation import validate_sample

ROOT=Path(__file__).resolve().parent


def demo(destination):
    if Path.cwd().resolve()!=ROOT.resolve():raise ValueError('Run the offline demo from the repository directory')
    destination=Path(destination)
    if destination.exists():raise FileExistsError('Demo requires a new output directory')
    destination.parent.mkdir(parents=True,exist_ok=True)
    sample_input=load(ROOT/'examples/public-sample.json')
    public,_=replay_sample(sample_input)
    scenarios_input=load(ROOT/'examples/scenarios.json');scenarios=evaluate(scenarios_input)
    # Matrix input uses caller-independent absolute paths, generated only in staging.
    with tempfile.TemporaryDirectory(prefix='.bjx-demo-',dir=destination.parent) as temp:
        stage=Path(temp)/'result';stage.mkdir()
        matrix_input=Path(temp)/'sample-input.json';matrix_input.write_bytes(encoded(sample_input))
        matrix=validate_sample({'sample_input':str(matrix_input)})
        inputs={'public_sample':sample_input,'teaching_scenarios':scenarios_input,'matrix_cases':{'budgets':['3000000.00','4500000.00','10000000.00'],'basis':'same public issuance with hypothetical budgets; teaching second issuance'}}
        results={'public_sample':public,'teaching_scenarios':scenarios,'matrix':matrix}
        (stage/'input.json').write_bytes(encoded(inputs));(stage/'result.json').write_bytes(encoded(results))
        stamp=datetime.now(timezone(timedelta(hours=8))).date().isoformat()
        table=[]
        for c in matrix['cases']:
            table.append(f"<tr><td>{float(c['hypothetical_budget'])/10000:.0f} 万元（假设）</td><td>{c['proportional_shares']} 股</td><td>未知</td></tr>")
        costs=public['opportunity_cost_assumption']
        scenario_rows=[]
        labels=['低配售 / 破发假设','中配售假设','高配售假设']
        for label,r in zip(labels,scenarios['scenarios']):
            scenario_rows.append(f"<tr><td>{label}</td><td>{r['proportional_shares']} 股</td><td>{r['net_profit']:,.2f} 元</td></tr>")
        sources=' '.join('<a href="'+html.escape(d['url'],quote=True)+'">'+html.escape(ident)+' 官方原文</a>' for ident,d in public['documents'].items())
        page='''<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width"><title>北交所研究引擎 · 案例对比</title><style>
        *{box-sizing:border-box}body{margin:0;background:#f3f6fa;color:#1b3047;font:16px/1.65 system-ui,"Microsoft YaHei",sans-serif}.wrap{max-width:1120px;margin:auto;padding:32px 28px}header{background:#132a43;color:white;border-radius:18px;padding:28px 32px}h1{font-size:30px;margin:8px 0}h2{font-size:21px;margin:0 0 12px}.eyebrow{color:#aec4db;font-size:14px}.grid{display:grid;grid-template-columns:1fr 1fr;gap:20px;margin-top:20px}.card{background:white;border:1px solid #dae3ed;border-radius:14px;padding:24px}.wide{grid-column:1/-1}.tag{display:inline-block;font-size:13px;padding:3px 9px;background:#e7eff7;border-radius:6px;margin-bottom:10px}.teaching{background:#fff0dc}.metrics{display:grid;grid-template-columns:repeat(3,1fr);gap:10px;margin:18px 0}.metric{background:#f4f7fb;border-radius:8px;padding:12px}.metric b{display:block;font-size:22px}table{width:100%;border-collapse:collapse;font-size:14px}th,td{text-align:left;padding:10px 9px;border-bottom:1px solid #e1e7ef}th{background:#f4f7fb}.note{color:#53677d;font-size:14px;margin:14px 0 0}.warning{background:#fff7ea;border-left:4px solid #d89a35;padding:14px 18px;margin-top:16px}a{color:#246099}footer{font-size:13px;color:#60738a;margin-top:20px}@media(max-width:750px){.grid{grid-template-columns:1fr}.wrap{padding:16px}.metrics{grid-template-columns:1fr}header{padding:20px}table{font-size:12px}}
        </style></head><body><div class="wrap"><header><div class="eyebrow">离线结果预览 · 生成日期 '''+stamp+' · 引擎 '+METHOD_VERSION+'''</div><h1>这笔预算能覆盖几手？现金什么时候仍被占用？</h1><div>一只公开发行的证据，与明确的教学边界一起看。历史重建不是事前预测。</div></header><main class="grid"><section class="card wide"><span class="tag">公开真实发行字段 + 假设预算</span><h2>悦龙科技（920188） · 2026-03-16 申购</h2><div>发行 / 结果 / 上市提示三份官方公告，核对八项选定字段。当前离线页复用保存记录，不表示本次重新取源。</div><div class="metrics"><div class="metric">发行价（公告）<b>14.04 元</b></div><div class="metric">申购上限（公告）<b>989,600 股</b></div><div class="metric">网上获配比例（事后）<b>0.0312799900%</b></div></div><table><tr><th>同一发行的不同预算</th><th>比例部分</th><th>真实个人获配 / 余股</th></tr>'''+''.join(table)+'''</table><p class="note">真实发行数仍为 1，三种预算不是三只真实样本。来源：'''+sources+'''</p></section><section class="card"><span class="tag">公共参数下的现金假设</span><h2>1000 万元预算：获配本金继续占用</h2><div class="metric">取整后的冻结额<b>'''+f"{float(public['frozen_amount']):,.2f}"+''' 元</b></div><p>比例获配 200 股，留存本金 2,808 元。假设资金成本年率 2%，观察到 2026-03-30，机会成本约 '''+f"{float(costs['opportunity_cost']):,.2f}"+''' 元。</p><div class="warning">公告退款日：2026-03-18<br>资金可用日：另行假设同日，未认证券商到账<br>上市日：2026-03-30，不自动当卖出 / 回款日</div><p class="note">未模拟卖出，实际收益未知；真实账户未验收。</p></section><section class="card"><span class="tag teaching">纯教学联合情景</span><h2>获配为零，也会有资金成本</h2><table><tr><th>教学情形</th><th>比例部分</th><th>声明净收益</th></tr>'''+''.join(scenario_rows)+'''</table><p class="note">本金 1000 万元、申购预算 800 万元、发行价 18 元及涨幅 / 权重均为人为假设，不对应悦龙或其他真实新股。净收益已扣声明费用和机会成本。</p><div class="warning">余股没有概率或保证；破发时额外获配可能增加损失。</div></section><section class="card wide"><span class="tag teaching">教学第二发行 · 同日资金冲突</span><h2>有退款公告，不代表能先用退款申购下一只</h2><p>悦龙资金重建与另一只教学发行同日投入 600 万元：缺到账顺序证据时先投入后释放，现金缺口为 '''+f"{matrix['teaching_multi_issue_conflict']['conflicts'][0]['shortage']:,.2f}"+''' 元，计划停止回放。</p><p class="note">第二只发行及到账顺序是教学输入，不是已核实际事件。尚缺真实个人零股、余股差异和多发行实际到账证据；不硬凑发行数量。</p></section></main><footer>本页可公开数据仅含字段摘要与教学参数，无账户资料或原文全文。输入 / 结果：input.json、result.json；生成清单：preview-manifest.json。仅供研究，不构成申购指令或收益承诺。</footer></div></body></html>'''
        (stage/'index.html').write_text(page,encoding='utf-8',newline='\n')
        manifest={'engine_version':METHOD_VERSION,'generated_on':stamp,'real_issuance_count':1,'source_review_date':'2026-10-09','visual_review':'not_performed_at_generation','files':{name:digest((stage/name).read_bytes()) for name in ('index.html','input.json','result.json')}}
        (stage/'preview-manifest.json').write_bytes(encoded(manifest))
        stage.rename(destination)
    return destination


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out-dir',required=True);a=p.parse_args()
    result=demo(a.out_dir)
    print('Offline preview created: '+str(result/'index.html')+'; explicit inputs and limits included, no account verification.')


if __name__=='__main__':main()
