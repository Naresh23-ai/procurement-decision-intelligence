# Procurement Decision Intelligence

A Streamlit-based agentic procurement decision platform for evidence-grounded RFP evaluation, deterministic scoring, peer benchmarking and auditable supplier ranking.

## Product capabilities

- Executive command center with pipeline and decision state
- Explicit Single Supplier and Multiple Suppliers intake modes
- Multi-supplier RFP batch evaluation
- PDF evidence extraction
- JSON-capable evaluation agent
- Deterministic validation and weighted scoring
- Overall / area / industry peer performance indices
- Executive Decision Board
- Concurrent All Supplier Evaluations workspace with full criterion evidence for every supplier
- Supplier 360 with radar profile and evidence drill-down
- Criterion benchmark heatmap
- Scenario Lab for non-persistent weight simulation
- SQLite-based Criteria Governance
- Risk & Controls workspace
- Audit Explorer with run history and JSON export
- Streamlit Cloud ready configuration

## Decision boundary

**AI interprets unstructured supplier evidence.**

**Python owns validation, scoring, peer benchmarks, PPI, tie-breaks and final rank.**

**SQLite owns configurable policy and audit persistence.**

## Run locally

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python -m streamlit run app.py
```

Open `http://localhost:8501`.

## Streamlit Community Cloud

Push this repository to GitHub and create a Streamlit Community Cloud app with:

- Repository: your GitHub repository
- Branch: `main`
- Main file: `app.py`

The default runtime is deterministic simulation and requires no API key.

For a live model, configure Streamlit Secrets:

```toml
LLM_PROVIDER = "openai"
OPENAI_API_KEY = "..."
OPENAI_MODEL = "your-json-capable-model"
```

Do not commit API keys.

## Default procurement policy

| Criterion | Weight |
|---|---:|
| Technical Capability | 30% |
| Implementation Plan | 20% |
| Commercial Value | 20% |
| Security & Compliance | 20% |
| Support & Experience | 10% |

Final deterministic ordering:

`PPI DESC → submission date ASC → experience DESC → supplier name ASC`


## Copyright and License

Copyright © 2026 Kavali Naresh Kumar. All rights reserved.

This project is provided for academic evaluation and portfolio demonstration. No permission is granted to reproduce, modify, distribute, sublicense, or commercially use the project without prior written permission.

See `LICENSE` for the full notice.
