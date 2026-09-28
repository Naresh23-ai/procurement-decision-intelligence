# Architecture

The platform is intentionally split into two decision domains:

1. **Probabilistic evidence interpretation**
   - PDF extraction
   - Supplier evidence analysis
   - Criterion score / justification / evidence JSON

2. **Deterministic procurement controls**
   - JSON validation and score-range enforcement
   - Weighted absolute score
   - Peer benchmarks, gaps and relative percentages
   - Peer Performance Index (PPI)
   - Stable tie-break and sequential ranking
   - SQLite persistence and audit export

This boundary prevents the model from directly deciding the final arithmetic or award rank.
