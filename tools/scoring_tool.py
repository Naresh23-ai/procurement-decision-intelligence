def calculate_absolute_score(evaluation: dict, criteria: list[dict]) -> dict:
    criterion_map = {int(c['criterion_id']): c for c in criteria}
    total = 0.0
    for item in evaluation['criteria']:
        c = criterion_map[item['criterion_id']]
        weight = float(c['weight'])
        max_score = float(c['max_score'])
        weighted = (item['score'] / max_score) * weight if max_score else 0.0
        item['weight'] = weight
        item['weighted_score'] = round(weighted, 4)
        total += weighted
    evaluation['absolute_score'] = round(total, 4)
    return evaluation
