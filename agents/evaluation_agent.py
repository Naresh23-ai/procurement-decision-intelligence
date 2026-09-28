import json
import os
import re
from config import LLM_PROVIDER, OPENAI_MODEL, OPENAI_API_KEY, MAX_PDF_CHARS
from prompts.evaluation_prompt import build_evaluation_prompt


def _mock_score(text: str, criterion_name: str) -> tuple[float, str, str]:
    t = text.lower()
    patterns = {
        'Technical Capability': ['architecture','api','integration','scalab','microservice','kubernetes','cloud'],
        'Implementation Plan': ['timeline','milestone','week','project manager','risk','implementation','delivery'],
        'Commercial Value': ['price','cost','total','commercial','discount','assumption','inr','₹'],
        'Security & Compliance': ['security','iso 27001','soc 2','encryption','privacy','audit','compliance'],
        'Support & Experience': ['support','sla','reference','experience','24x7','project','customer'],
    }
    keys = patterns.get(criterion_name, [criterion_name.lower()])
    hits = sum(1 for k in keys if k in t)
    score = min(10.0, 3.0 + hits * 1.0)
    if any(x in t for x in ['not provided','not specified','not available','tbd']) and hits < 3:
        score = max(1.0, score - 2.0)
    evidence = ', '.join([k for k in keys if k in t][:4]) or 'Limited explicit evidence found.'
    return score, f'Mock evaluator found {hits} relevant evidence signals for {criterion_name}.', evidence


def _mock_evaluate(supplier_name: str, supplier_text: str, criteria: list[dict]):
    out = {'supplier_name': supplier_name, 'criteria': [], 'risks': [], 'overall_summary': 'Deterministic mock evaluation for offline/demo use.'}
    for c in criteria:
        score, justification, evidence = _mock_score(supplier_text, c['name'])
        score = min(score, float(c['max_score']))
        out['criteria'].append({
            'criterion_id': c['criterion_id'], 'criterion_name': c['name'], 'score': score,
            'max_score': c['max_score'], 'justification': justification, 'evidence': evidence,
        })
    return out


def evaluate_supplier(supplier_name: str, requirement_text: str, supplier_text: str, criteria: list[dict]):
    supplier_text = supplier_text[:MAX_PDF_CHARS]
    requirement_text = requirement_text[:MAX_PDF_CHARS]
    if LLM_PROVIDER == 'mock':
        return _mock_evaluate(supplier_name, supplier_text, criteria)

    if LLM_PROVIDER == 'openai':
        from openai import OpenAI
        client = OpenAI(api_key=os.environ.get('OPENAI_API_KEY'))
        prompt = build_evaluation_prompt(supplier_name, requirement_text, supplier_text, criteria)
        response = client.responses.create(model=OPENAI_MODEL, input=prompt)
        return response.output_text

    raise ValueError(f'Unsupported LLM_PROVIDER={LLM_PROVIDER}. Use mock or openai.')
