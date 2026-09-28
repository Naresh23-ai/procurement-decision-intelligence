-- See database/db.py::init_db. This file documents the minimum persistent design.
CREATE TABLE evaluation_criteria (criterion_id INTEGER PRIMARY KEY, name TEXT, description TEXT, weight REAL, max_score REAL, is_active INTEGER);
CREATE TABLE rfp_runs (rfp_run_id TEXT PRIMARY KEY, created_at TEXT, status TEXT);
CREATE TABLE supplier_results (result_id INTEGER PRIMARY KEY AUTOINCREMENT, rfp_run_id TEXT, supplier_name TEXT, submission_date TEXT, experience_rating REAL, industry TEXT, area TEXT, absolute_score REAL, ppi REAL, area_ppi REAL, industry_ppi REAL, final_rank INTEGER, result_json TEXT);
