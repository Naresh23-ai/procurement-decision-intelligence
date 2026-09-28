from datetime import date


def rank_suppliers(results: list[dict]) -> list[dict]:
    def sort_key(r):
        try:
            d = date.fromisoformat(str(r['submission_date']))
        except Exception:
            d = date.max
        return (-float(r['ppi']), d, -float(r['experience_rating']), str(r['supplier_name']).lower())

    ordered = sorted(results, key=sort_key)
    for i, r in enumerate(ordered, start=1):
        r['final_rank'] = i
        r['tie_break_explanation'] = (
            'Sorted by mandatory order: higher PPI, earlier submission date, '
            'higher historical experience rating, supplier name ascending.'
        )
    return ordered
