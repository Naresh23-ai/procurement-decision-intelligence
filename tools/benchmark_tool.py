from collections import defaultdict


def _apply_benchmark(group: list[dict], key_prefix: str = ''):
    if not group:
        return
    criterion_ids = [c['criterion_id'] for c in group[0]['criteria']]
    benchmarks = {}
    for cid in criterion_ids:
        benchmarks[cid] = max(
            next(x['score'] for x in r['criteria'] if x['criterion_id'] == cid)
            for r in group
        )
    for r in group:
        weighted_rel = 0.0
        weight_total = 0.0
        for c in r['criteria']:
            benchmark = benchmarks[c['criterion_id']]
            relative = (c['score'] / benchmark * 100.0) if benchmark > 0 else 100.0
            if not key_prefix:
                c['benchmark_score'] = round(benchmark, 4)
                c['gap'] = round(c['score'] - benchmark, 4)
                c['relative_percentage'] = round(relative, 4)
            weighted_rel += relative * c['weight']
            weight_total += c['weight']
        value = weighted_rel / weight_total if weight_total else 0.0
        r[f'{key_prefix}ppi' if key_prefix else 'ppi'] = round(value, 4)


def calculate_peer_metrics(results: list[dict]) -> list[dict]:
    _apply_benchmark(results)

    areas = defaultdict(list)
    industries = defaultdict(list)
    for r in results:
        areas[r.get('area', 'Unknown')].append(r)
        industries[r.get('industry', 'Unknown')].append(r)

    for group in areas.values():
        _apply_benchmark(group, 'area_')
    for group in industries.values():
        _apply_benchmark(group, 'industry_')
    return results
