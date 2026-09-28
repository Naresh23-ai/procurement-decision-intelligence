import json


def build_evaluation_prompt(supplier_name: str, requirement_text: str, supplier_text: str, criteria: list[dict]) -> str:
    criteria_payload = [
        {
            'criterion_id': c['criterion_id'],
            'name': c['name'],
            'description': c['description'],
            'max_score': c['max_score'],
        }
        for c in criteria
    ]
    return f'''
You are the Evaluation Agent in an RFP supplier evaluation workflow.

Evaluate supplier "{supplier_name}" against the active criteria below.
Use ONLY evidence present in the supplier proposal. The procurement requirement is context for fit,
but do not invent supplier capabilities. If evidence is absent, score conservatively and explicitly say
that the information is missing.

ACTIVE CRITERIA:
{json.dumps(criteria_payload, indent=2)}

PROCUREMENT REQUIREMENT:
{requirement_text}

SUPPLIER PROPOSAL:
{supplier_text}

Return JSON ONLY with this exact top-level shape:
{{
  "supplier_name": "{supplier_name}",
  "criteria": [
    {{
      "criterion_id": 1,
      "criterion_name": "Technical Capability",
      "score": 0,
      "max_score": 10,
      "justification": "brief evidence-grounded reasoning",
      "evidence": "short supporting excerpt or precise proposal reference"
    }}
  ],
  "risks": ["risk 1"],
  "overall_summary": "short summary"
}}

Rules:
1. Return exactly one criterion result for every active criterion_id.
2. score must be numeric and between 0 and max_score.
3. Never calculate weighted score, benchmark, PPI, tie-break or final rank.
4. Do not use external knowledge.
5. JSON only; no markdown fences.
'''.strip()
