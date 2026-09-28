import uuid
from agents.evaluation_agent import evaluate_supplier
from tools.pdf_tool import extract_pdf_text
from tools.validation_tool import validate_and_normalize
from tools.scoring_tool import calculate_absolute_score
from tools.benchmark_tool import calculate_peer_metrics
from tools.ranking_tool import rank_suppliers
from database.db import get_active_criteria, create_run, complete_run, persist_results


def run_evaluation(requirement_pdf, supplier_inputs: list[dict]) -> tuple[str, list[dict]]:
    criteria = get_active_criteria()
    total_weight = round(sum(float(c['weight']) for c in criteria), 6)
    if total_weight != 100.0:
        raise ValueError(f'Active criteria weights must total 100%; current total={total_weight}.')

    requirement_text = extract_pdf_text(requirement_pdf) if requirement_pdf else ''
    run_id = f'RFP-{uuid.uuid4().hex[:10].upper()}'
    create_run(run_id)

    results = []
    for supplier in supplier_inputs:
        text = extract_pdf_text(supplier['pdf'])
        raw = evaluate_supplier(supplier['supplier_name'], requirement_text, text, criteria)
        normalized = validate_and_normalize(raw, supplier['supplier_name'], criteria)
        normalized.update({
            'submission_date': str(supplier['submission_date']),
            'experience_rating': float(supplier['experience_rating']),
            'industry': supplier.get('industry', 'General'),
            'area': supplier.get('area', 'India'),
            'pdf_name': supplier.get('pdf_name', ''),
        })
        results.append(calculate_absolute_score(normalized, criteria))

    results = calculate_peer_metrics(results)
    results = rank_suppliers(results)
    persist_results(run_id, results)
    complete_run(run_id)
    return run_id, results
