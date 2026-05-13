#!/usr/bin/env python3
"""
validate_resources.py
配置资源校验工具

功能：
  对比生成配置与参考配置，只校验资源字段（MSprite/MAudio/MAnimation/MParticle），
  不校验坐标、尺寸等动态内容。

  校验规则：
  1. 对于每个组件名（name/component_name），检查生成配置里用到的资源URL
     是否在参考配置里的同名组件中出现过（或在参考配置的全局资源池中）
  2. 特殊组件（节点_37 题目配图 / 拖拽物品音频）由用户动态指定，加入白名单豁免
  3. 输出 PASS / WARN / FAIL 三级结果

用法:
  python3 validate_resources.py <生成配置.json> <参考配置.json> [--whitelist url1,url2,...]

  或作为模块调用:
    from validate_resources import validate
    result = validate(generated_cfg, ref_cfg, whitelist_urls=set())
"""

import json
import sys
import os
from collections import defaultdict

# 需要校验的资源字段
RESOURCE_KEYS = ('MSprite', 'MAudio', 'MAnimation', 'MParticle')

# 组件名归一化（去掉末尾的数字后缀，如 拖拽放置区4_39 → 拖拽放置区4）
import re
def normalize_name(name: str) -> str:
    if not name:
        return ''
    return re.sub(r'_\d+$', '', name.strip())


def extract_resources(obj, component_name=''):
    """
    递归提取配置中所有资源记录
    返回: list of dict {cname, norm_cname, rtype, value}
    """
    results = []
    if isinstance(obj, dict):
        cname = obj.get('name') or obj.get('component_name') or component_name
        cname = cname or ''
        for rk in RESOURCE_KEYS:
            if rk in obj and isinstance(obj[rk], dict):
                val = obj[rk].get('value', '')
                if val and isinstance(val, str) and val.strip():
                    results.append({
                        'cname': cname,
                        'norm_cname': normalize_name(cname),
                        'rtype': rk,
                        'value': val.strip(),
                    })
        for k, v in obj.items():
            results.extend(extract_resources(v, cname))
    elif isinstance(obj, list):
        for item in obj:
            results.extend(extract_resources(item, component_name))
    return results


def build_ref_index(ref_cfg):
    """
    从参考配置建立资源索引：
      - per_component: {(norm_cname, rtype): set(values)}
      - global_pool: {rtype: set(values)}  （所有资源的全局池）
    """
    records = extract_resources(ref_cfg)
    per_component = defaultdict(set)
    global_pool = defaultdict(set)
    for r in records:
        per_component[(r['norm_cname'], r['rtype'])].add(r['value'])
        global_pool[r['rtype']].add(r['value'])
    return per_component, global_pool


def validate(generated_cfg, ref_cfg, whitelist_urls=None):
    """
    校验生成配置 vs 参考配置（资源字段）。

    参数:
      generated_cfg  — 已解析的生成配置 dict
      ref_cfg        — 已解析的参考配置 dict
      whitelist_urls — set，豁免的资源URL（如用户自定义上传的图片、题目音频）

    返回:
      {
        'ok': bool,
        'pass': [...],   # 通过的记录
        'warn': [...],   # 全局池中有但同名组件没有（可能是跨组件复用，警告）
        'fail': [...],   # 参考配置中完全没有此资源（可疑）
        'whitelisted': [...],
      }
    """
    if whitelist_urls is None:
        whitelist_urls = set()

    per_component, global_pool = build_ref_index(ref_cfg)
    gen_records = extract_resources(generated_cfg)

    result = {'ok': True, 'pass': [], 'warn': [], 'fail': [], 'whitelisted': []}

    # 去重（同一 cname+rtype+value 只报一次）
    seen = set()
    for r in gen_records:
        key = (r['norm_cname'], r['rtype'], r['value'])
        if key in seen:
            continue
        seen.add(key)

        val = r['value']
        cname = r['norm_cname']
        rtype = r['rtype']

        if val in whitelist_urls:
            result['whitelisted'].append(r)
            continue

        if val in per_component.get((cname, rtype), set()):
            result['pass'].append(r)
        elif val in global_pool.get(rtype, set()):
            result['warn'].append(r)
        else:
            result['fail'].append(r)
            result['ok'] = False

    return result


def print_report(result, verbose=False):
    total = len(result['pass']) + len(result['warn']) + len(result['fail']) + len(result['whitelisted'])
    print(f"\n{'='*60}")
    print(f"资源校验报告")
    print(f"{'='*60}")
    print(f"总计: {total} 条  |  ✅ PASS: {len(result['pass'])}  |  "
          f"⚠️  WARN: {len(result['warn'])}  |  "
          f"❌ FAIL: {len(result['fail'])}  |  "
          f"🔵 豁免: {len(result['whitelisted'])}")

    if result['fail']:
        print(f"\n❌ FAIL（参考配置中完全没有此资源，请检查）:")
        for r in result['fail']:
            print(f"  [{r['cname']}] {r['rtype']}: {r['value'][:80]}")

    if result['warn']:
        print(f"\n⚠️  WARN（全局池有但同名组件没有，可能是跨组件复用，建议确认）:")
        for r in result['warn']:
            print(f"  [{r['cname']}] {r['rtype']}: {r['value'][:80]}")

    if verbose and result['pass']:
        print(f"\n✅ PASS（与参考一致，略）:")
        for r in result['pass'][:10]:
            print(f"  [{r['cname']}] {r['rtype']}: {r['value'][:60]}")
        if len(result['pass']) > 10:
            print(f"  ...({len(result['pass'])-10} more)")

    print(f"\n{'='*60}")
    print(f"结论: {'✅ 资源校验通过' if result['ok'] else '❌ 存在未知资源，请检查 FAIL 项'}")
    print(f"{'='*60}\n")


def main():
    import argparse
    parser = argparse.ArgumentParser(description='配置资源校验工具')
    parser.add_argument('generated', help='生成的配置 JSON 文件')
    parser.add_argument('reference', help='参考配置 JSON 文件')
    parser.add_argument('--whitelist', help='豁免的URL列表，逗号分隔', default='')
    parser.add_argument('--whitelist-file', help='豁免URL列表文件（每行一个URL）', default='')
    parser.add_argument('--verbose', action='store_true', help='显示PASS的详情')
    args = parser.parse_args()

    with open(args.generated, encoding='utf-8') as f:
        gen = json.load(f)
    with open(args.reference, encoding='utf-8') as f:
        ref = json.load(f)

    whitelist = set()
    if args.whitelist:
        whitelist.update(u.strip() for u in args.whitelist.split(',') if u.strip())
    if args.whitelist_file and os.path.exists(args.whitelist_file):
        with open(args.whitelist_file) as f:
            whitelist.update(line.strip() for line in f if line.strip())

    result = validate(gen, ref, whitelist_urls=whitelist)
    print_report(result, verbose=args.verbose)

    sys.exit(0 if result['ok'] else 1)


if __name__ == '__main__':
    main()
