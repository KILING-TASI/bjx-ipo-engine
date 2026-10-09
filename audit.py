"""Portable source capture, strict input and content-bound research packages."""
import hashlib
import html
import json
import math
import os
import re
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener

METHOD_VERSION = '0.2.0-alpha.6'
MAX_BYTES = 10 * 1024 * 1024
ALLOWED_HOSTS = {'www.bse.cn', 'bse.cn', 'www.sse.com.cn', 'sse.com.cn',
                 'www.szse.cn', 'szse.cn', 'www.cninfo.com.cn', 'static.cninfo.com.cn'}


def digest(blob):
    return hashlib.sha256(blob).hexdigest()


def unique_pairs(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError('Duplicate JSON key: ' + key)
        result[key] = value
    return result


def invalid_constant(value):
    raise ValueError('Nonfinite JSON constant: ' + value)


def finite_float(value):
    parsed = float(value)
    if not math.isfinite(parsed):
        raise ValueError('Nonfinite JSON number')
    return parsed


def loads(content):
    return json.loads(content, object_pairs_hook=unique_pairs,
                      parse_constant=invalid_constant, parse_float=finite_float)


def load(path):
    return loads(Path(path).read_text(encoding='utf-8-sig'))


def encoded(value):
    return (json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + '\n').encode('utf-8')


def safe_url(url):
    if not isinstance(url, str) or re.search(r'[\s\x00-\x1f\x7f]', url):
        raise ValueError('Malformed source URL')
    parsed = urlsplit(url)
    if (parsed.scheme != 'https' or parsed.hostname not in ALLOWED_HOSTS or
            parsed.username is not None or parsed.password is not None or
            parsed.port not in (None, 443) or parsed.fragment):
        raise ValueError('Source must be an allowed public exchange/CNINFO HTTPS URL')
    return url


class SafeRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        safe_url(newurl)
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def capture(spec):
    """No automatic parsing or fact certification; raw bytes retained separately."""
    url = safe_url(spec['url'])
    expected = spec.get('expected_sha256')
    if expected is not None and not re.fullmatch('[0-9a-f]{64}', expected):
        raise ValueError('Expected SHA256 must be lowercase hexadecimal')
    request = Request(url, headers={'User-Agent': 'bjx-ipo-engine/0.2 research-source-capture',
                                    'Accept-Encoding': 'identity'})
    with build_opener(SafeRedirect()).open(request, timeout=20) as response:
        final_url = safe_url(response.geturl())
        content_length = response.headers.get('Content-Length')
        if content_length and int(content_length) > MAX_BYTES:
            raise ValueError('Source exceeds 10 MiB')
        blob = response.read(MAX_BYTES + 1)
        mime = response.headers.get('Content-Type', '')
    if not blob or len(blob) > MAX_BYTES:
        raise ValueError('Empty or oversized source')
    actual = digest(blob)
    if expected is not None and actual != expected:
        raise ValueError('Source hash changed; expected content was not obtained')
    looks_pdf = blob.startswith(b'%PDF-')
    if urlsplit(final_url).path.lower().endswith('.pdf') and not looks_pdf:
        raise ValueError('PDF URL returned non-PDF bytes')
    if not looks_pdf and 'html' not in mime.lower() and 'text/plain' not in mime.lower():
        raise ValueError('Only PDF, HTML and plain-text sources supported')
    name = 'source.pdf' if looks_pdf else 'source.html' if 'html' in mime.lower() else 'source.txt'
    return dict(status='captured_not_verified', source_url=url, final_url=final_url,
                retrieved_at=datetime.now(timezone.utc).isoformat(), sha256=actual,
                size=len(blob), content_type=mime, artifact=name,
                parse_status='not_performed', source_verification='not_performed'), {name: blob}


def report(mode, result, status):
    heading = {'scenarios': '北交所获配与收益情景', 'ledger': '多只资金现金账',
               'facts': '发行事实候选与缺口', 'versions': '公告版本线索',
               'capture': '公告来源保存', 'compare-pdf': '公告原文版本差异',
               'compare-cash': '同本金同期间现金方案对照', 'calendar': '北交所官方排期日历',
               'freeze': '事前假设本地快照', 'archive': '公开发行结果档案', 'review': '事前与事后分离复盘'}.get(mode, mode)
    lines = ['# ' + heading, '', '状态：' + status, '']
    if status == 'blocked':
        lines += ['本次未完成。原因：' + result['message'], '',
                  '下一步：' + result['next_step']]
    elif mode == 'scenarios':
        a = result['assumptions']
        lines += [f"账户本金：{a['capital']:,.2f}元；实际冻结：{result['frozen_amount']:,.2f}元；发行价假设：{a['issue_price']:.2f}元。",
                  f"资金成本年率假设：{a['annual_cash_cost_rate']:.2%}；申购/退款可用/卖出现金可用日期：{a['subscription_date']} / {a['refund_available_date']} / {a['sale_cash_available_date']}。"]
        lines += ['以下是声明参数下的比例整手测算，余股获配未知。', '',
                  '| 情景 | 比例手数 | 毛收益 | 卖出费用 | 资金成本 | 净收益 |',
                  '|---|---:|---:|---:|---:|---:|']
        for r in result['scenarios']:
            label = str(r['id']).replace('|', '\\|').replace('\n', ' ')
            lines.append(f"| {label} | {r['proportional_hands']} | {r['gross_profit']:.2f} | {r['sell_cost']:.2f} | {r['cash_cost']:.2f} | {r['net_profit']:.2f} |")
        lines += ['', '## 盈亏平衡与余股敏感性', '',
                  '盈亏平衡涨幅是固定获配股数、日期及费用假设下覆盖成本所需的卖出涨幅，不是价格预测。',
                  '额外100股是假设余股排序获配后的重新计算，不给获配概率，也不是收益或损失界。', '',
                  '| 情景 | 配售率假设 | 卖出涨幅假设 | 盈亏平衡涨幅 | 假设额外100股后净收益 |',
                  '|---|---:|---:|---:|---:|']
        for r in result['scenarios']:
            label = str(r['id']).replace('|', '\\|').replace('\n', ' ')
            breakeven = '无比例整手，无法计算' if r['breakeven_listing_return'] is None else f"{r['breakeven_listing_return']:.2%}"
            extra = r['residual_extra_100_share_sensitivity']
            net = '不适用' if extra is None else f"{extra['net_profit']:.2f}"
            lines.append(f"| {label} | {r['allocation_rate']:.5%} | {r['listing_return']:.2%} | {breakeven} | {net} |")
        if 'weighted' in result:
            w = result['weighted']
            lines += ['', f"声明权重下期望净收益：{w['expected_net_profit']:.2f}元；比例零整手概率：{w['probability_zero_proportional_hands']:.2%}。",
                      f"净收益标准差：{w['sd_net_profit']:.2f}元；净亏损概率：{w['probability_net_loss']:.2%}。",
                      f"期望比例手数：{w['expected_proportional_hands']:.3f}；手数标准差：{w['sd_proportional_hands']:.3f}。",
                      '权重依据：' + w['probability_basis']]
    elif mode == 'ledger':
        lines += ['计划现金是否足够：' + ('足够（仅声明事件）' if result['executable'] else '不足，已停止回放'),
                  f"最后已回放可用现金：{result['final_available_cash']:.2f}元。",
                  '冲突时该余额不是计划期末余额；不得据此假定融资。']
    elif mode == 'compare-cash':
        lines += [f"共同期间：{result['start']}至{result['end']}；期初本金：{result['initial_cash']}元。",
                  '以下仅对照声明的现金事件，未扣机会成本；不是全年或复利年化。', '',
                  '| 方案 | 状态 | 期末现金 | 已结清现金盈亏 | 本金占用资金日 |',
                  '|---|---|---:|---:|---:|']
        for plan in result['plans']:
            label = plan['id'].replace('|', '\\|').replace('\n', ' ')
            values = [plan['closing_cash'], plan['realized_cash_profit'], plan['locked_capital_days']]
            lines.append('| '+label+' | '+plan['status']+' | '+' | '.join('未完成' if v is None else v for v in values)+' |')
        if result['first_minus_second_cash_profit'] is None:
            lines += ['', '存在撞资或未回收本金，当前不比较盈亏优劣。']
        else:
            lines += ['', '第一方案减第二方案的声明现金盈亏差：'+result['first_minus_second_cash_profit']+'元。']
        lines += ['', '闲置现金利息及尚未到账利息只在显式录入时计入；结果不认证事件完整性。']
    elif mode == 'freeze':
        lines += ['记录类别：'+result['record_kind'], '本地保存时间：'+result['frozen_at'],
                  '现在补录过去假设只能是历史重建；本地摘要与时钟不提供外部可信时间证明。']
    elif mode == 'archive':
        lines += ['公开发行候选独立保存，未核值与冲突不自动选定；余股获配未知。']
        for name, field in result['fields'].items():
            lines.append('- '+name+'：'+field['status'])
        lines += ['公告退款日不等于券商资金可用日。']
    elif mode == 'review':
        lines += ['事前记录类别：'+result['frozen_record_kind'],
                  '只比较声明值，不输出真实预测准确率；事后档案不覆盖事前快照。']
        for item in result['comparisons']:
            lines.append('- '+item['field']+'：'+str(item['signed_error_frozen_minus_actual'])+'（事前减事后，单位'+item['unit']+'，来源状态'+item['source_status']+'）')
        lines += ['余股未知；附加现金回放是另行明确输入的计划，不认证实际账户收益。']
    elif mode == 'calendar':
        lines += [f"排期覆盖：{result['coverage_start']}至{result['coverage_end']}。",
                  f"按官方假期和周一至周五规则推导的计划交易日数：{result['scheduled_trading_date_count']}。",
                  '这是计划日历，不认证临时停市、真实市场开市或账户到账。',
                  '政府调休工作周末仍按交易所周末休市处理；不据此推断T+2退款。']
    elif mode == 'facts':
        lines += ['事实候选保留全部来源，不自动选择冲突值。', '']
        for name, field in result['fields'].items():
            lines.append(f"- {name}：{field['status']}，{len(field['candidates'])}项候选。")
    elif mode == 'versions':
        lines += ['发现需比较正文的公告组数：' + str(len(result['groups'])),
                  '标题更正线索不证明事实已被替代，未发现线索也不证明不存在更正。']
    elif mode == 'capture':
        lines += ['已保存来源字节及SHA256；未解析或核验正文。',
                  '来源：' + result['source_url'], 'SHA256：' + result['sha256']]
    elif mode == 'compare-pdf':
        lines += [f"提取文本差异块：{len(result['changes'])}。",
                  '语义及页图核验尚未完成；不自动覆盖发行事实。']
    lines += ['', '## 适用范围', '',
              '输入为事实声明或情景假设，计算及文件摘要不认证资料真实性。',
              '获取、解析、计算、原文核验和视觉检查分别记录；不构成投资建议。',
              '详情、参数及来源见同目录input.json、result.json与manifest.json。']
    markdown = '\n'.join(lines) + '\n'
    page = render_html(markdown, heading)
    return markdown.encode('utf-8'), page.encode('utf-8')


def render_html(markdown, heading):
    """Render only generated headings/paragraphs/tables; escape every source cell."""
    blocks = []
    table_open = False
    for line in markdown.splitlines():
        if line.startswith('|'):
            cells = [cell.replace('\\|', '|').strip() for cell in re.split(r'(?<!\\)\|', line)[1:-1]]
            if cells and all(re.fullmatch(r':?-+:?', c) for c in cells):
                continue
            if not table_open:
                blocks.append('<div class="table-wrap"><table>')
                tag = 'th'
                table_open = True
            else:
                tag = 'td'
            blocks.append('<tr>' + ''.join(f'<{tag}>'+html.escape(c)+f'</{tag}>' for c in cells) + '</tr>')
            continue
        if table_open:
            blocks.append('</table></div>')
            table_open = False
        if line.startswith('## '):
            blocks.append('<h2>'+html.escape(line[3:])+'</h2>')
        elif line.startswith('# '):
            blocks.append('<h1>'+html.escape(line[2:])+'</h1>')
        elif line.strip():
            blocks.append('<p>'+html.escape(line)+'</p>')
    if table_open:
        blocks.append('</table></div>')
    style = 'body{max-width:1050px;margin:32px auto;padding:0 20px;font-family:system-ui;line-height:1.7;color:#172536;background:#fafbfc}h1{font-size:26px}h2{margin-top:32px;font-size:20px}.table-wrap{overflow-x:auto}table{border-collapse:collapse;width:100%;background:white}th,td{padding:10px 12px;border:1px solid #dbe2eb;text-align:left}th{background:#eef3f8}p{overflow-wrap:anywhere}'
    return '<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width"><title>'+html.escape(heading)+'</title><style>'+style+'</style><body>'+''.join(blocks)+'</body></html>'


def bind_fact_sources(spec, result):
    """Bind candidate claims to exact saved PDF bytes, without certifying values."""
    artifacts = {}
    records = {}
    sources = spec.get('source_files', [])
    if not isinstance(sources, list) or len(sources) > 5:
        raise ValueError('source_files requires 0..5 explicitly supplied PDFs')
    for index, source in enumerate(sources):
        identity = source['id']
        if not isinstance(identity, str) or not identity or identity in records:
            raise ValueError('Source ids must be unique nonempty text')
        path = Path(source['path'])
        if path.stat().st_size > MAX_BYTES:
            raise ValueError('Source PDF exceeds 10 MiB')
        blob = path.read_bytes()
        if len(blob) > MAX_BYTES or not blob.startswith(b'%PDF-'):
            raise ValueError('Source must be a PDF up to 10 MiB')
        actual = digest(blob)
        if actual != source['sha256']:
            raise ValueError('Original content hash mismatch: ' + identity)
        url = source['url']
        parsed = urlsplit(url)
        if parsed.scheme != 'https' or not parsed.hostname or parsed.username or parsed.password:
            raise ValueError('Source provenance must be HTTPS without credentials')
        name = f'original-{index:03d}.pdf'
        artifacts[name] = blob
        records[identity] = dict(artifact=name, sha256=actual, url=url,
                                 status='bytes_bound_not_verified')
    for field in result['fields'].values():
        for candidate in field['candidates']:
            identity = candidate.get('source_id')
            if identity is None:
                if candidate.get('document_sha256') is not None:
                    raise ValueError('Document hash requires source_id')
                continue
            record = records.get(identity)
            if (record is None or candidate.get('document_sha256') != record['sha256']
                    or candidate['source'] != record['url']):
                raise ValueError('Candidate source binding missing or inconsistent')
    result = dict(result, source_bindings=records)
    return result, artifacts


def publish(destination, mode, spec, result, status='completed_with_limits', artifacts=None):
    destination = Path(destination)
    if destination.exists():
        raise FileExistsError('Output directory already exists')
    destination.parent.mkdir(parents=True, exist_ok=True)
    files = {'input.json': encoded(spec), 'result.json': encoded(result)}
    markdown, page = report(mode, result, status)
    files.update({'report.md': markdown, 'report.html': page})
    for name, content in (artifacts or {}).items():
        if name not in ('source.pdf', 'source.html', 'source.txt', 'before.pdf', 'after.pdf') and not re.fullmatch(r'original-\d{3}\.pdf', name):
            raise ValueError('Invalid artifact name')
        files[name] = content
    manifest = dict(schema_version='0.2', method_version=METHOD_VERSION, mode=mode, status=status,
                    created_at=datetime.now(timezone.utc).isoformat(),
                    stages=dict(acquisition='completed' if artifacts else 'not_performed',
                                parsing='completed_extracted_text' if mode == 'compare-pdf' and status != 'blocked' else 'not_performed',
                                calculation='completed' if mode in ('scenarios', 'ledger', 'compare-cash', 'calendar') and status != 'blocked' else 'not_performed',
                                source_verification='not_performed', visual_review='not_performed'),
                    files={name: dict(sha256=digest(blob), size=len(blob)) for name, blob in files.items()})
    files['manifest.json'] = encoded(manifest)
    # Unique staging, then publish new directory; never replace an existing report.
    with tempfile.TemporaryDirectory(prefix='.bjx-', dir=destination.parent) as temp:
        stage = Path(temp) / 'bundle'
        stage.mkdir()
        for name, blob in files.items():
            with (stage / name).open('xb') as handle:
                handle.write(blob)
                handle.flush()
                os.fsync(handle.fileno())
        if destination.exists():
            raise FileExistsError('Output appeared during execution')
        stage.rename(destination)
    return manifest


def verify(directory):
    root = Path(directory)
    if root.is_symlink():
        raise ValueError('Bundle directory cannot be a symlink')
    manifest_path = root / 'manifest.json'
    if manifest_path.is_symlink():
        raise ValueError('Manifest cannot be a symlink')
    manifest = load(manifest_path)
    files = manifest['files']
    if not {'input.json', 'result.json', 'report.md', 'report.html'} <= set(files):
        raise ValueError('Required bundle artifacts missing')
    for name, entry in files.items():
        if not re.fullmatch(r'[A-Za-z0-9_-]+\.(json|md|html|pdf|txt)', name):
            raise ValueError('Unsafe manifest path')
        path = root / name
        if path.is_symlink() or not path.is_file():
            raise ValueError('Missing or linked artifact: ' + name)
        blob = path.read_bytes()
        if digest(blob) != entry['sha256'] or len(blob) != entry['size']:
            raise ValueError('Content differs from manifest: ' + name)
    if {p.name for p in root.iterdir()} != set(files) | {'manifest.json'}:
        raise ValueError('Unregistered bundle content')
    return dict(status='content_matches_manifest', method_version=manifest['method_version'],
                limitation='Manifest is mutable, not a signature or independent timestamp; matching does not certify facts or calculations.')
