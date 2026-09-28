import json
from typing import Any
from models.evaluation import SupplierEvaluation


def _load_json(raw: Any):
    if isinstance(raw, dict):
        return raw, []
    warnings = []
    text = str(raw).strip()
    if text.startswith('```'):
        text = text.replace('```json', '').replace('```', '').strip()
        warnings.append('Removed markdown code fences from LLM output.')
    try:
        return json.loads(text), warnings
    except Exception as exc:
        warnings.append(f'LLM JSON parse failed: {exc}. Using empty result for normalization.')
        return {}, warnings


def validate_and_normalize(raw, supplier_name: str, criteria: list[dict]) -> dict:
    data, warnings = _load_json(raw)
    items = data.get('criteria', []) if isinstance(data, dict) else []
    by_id = {}
    for item in items if isinstance(items, list) else []:
        try:
            cid = int(item.get('criterion_id'))
            by_id[cid] = item
        except Exception:
            warnings.append('Ignored criterion with missing/malformed criterion_id.')

    normalized = []
    for c in criteria:
        cid, max_score = int(c['criterion_id']), float(c['max_score'])
        item = by_id.get(cid)
        if item is None:
            warnings.append(f"Missing criterion {cid} ({c['name']}); defaulted score to 0.")
            item = {}
        try:
            score = float(item.get('score', 0))
        except Exception:
            score = 0.0
            warnings.append(f"Criterion {cid} returned non-numeric score; defaulted to 0.")
        clipped = min(max(score, 0.0), max_score)
        if clipped != score:
            warnings.append(f"Criterion {cid} score {score} clipped to valid range 0-{max_score}.")
        normalized.append({
            'criterion_id': cid,
            'criterion_name': c['name'],
            'score': clipped,
            'max_score': max_score,
            'justification': str(item.get('justification', 'No valid justification returned.')),
            'evidence': str(item.get('evidence', '')),
        })

    result = {
        'supplier_name': supplier_name,
        'criteria': normalized,
        'risks': data.get('risks', []) if isinstance(data, dict) else [],
        'overall_summary': data.get('overall_summary', '') if isinstance(data, dict) else '',
        'warnings': warnings,
    }
    # final schema check
    return SupplierEvaluation.model_validate(result).model_dump()
