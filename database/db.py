import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from config import DB_PATH


def connect(db_path=DB_PATH):
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db(db_path=DB_PATH):
    conn = connect(db_path)
    conn.executescript('''
    CREATE TABLE IF NOT EXISTS evaluation_criteria (
        criterion_id INTEGER PRIMARY KEY,
        name TEXT NOT NULL,
        description TEXT NOT NULL,
        weight REAL NOT NULL,
        max_score REAL NOT NULL DEFAULT 10,
        is_active INTEGER NOT NULL DEFAULT 1
    );
    CREATE TABLE IF NOT EXISTS rfp_runs (
        rfp_run_id TEXT PRIMARY KEY,
        created_at TEXT NOT NULL,
        status TEXT NOT NULL
    );
    CREATE TABLE IF NOT EXISTS supplier_results (
        result_id INTEGER PRIMARY KEY AUTOINCREMENT,
        rfp_run_id TEXT NOT NULL,
        supplier_name TEXT NOT NULL,
        submission_date TEXT NOT NULL,
        experience_rating REAL NOT NULL,
        industry TEXT,
        area TEXT,
        absolute_score REAL NOT NULL,
        ppi REAL NOT NULL,
        area_ppi REAL,
        industry_ppi REAL,
        final_rank INTEGER NOT NULL,
        result_json TEXT NOT NULL,
        FOREIGN KEY(rfp_run_id) REFERENCES rfp_runs(rfp_run_id)
    );
    CREATE TABLE IF NOT EXISTS criterion_results (
        result_id INTEGER PRIMARY KEY AUTOINCREMENT,
        rfp_run_id TEXT NOT NULL,
        supplier_name TEXT NOT NULL,
        criterion_id INTEGER NOT NULL,
        criterion_name TEXT NOT NULL,
        score REAL NOT NULL,
        benchmark_score REAL NOT NULL,
        gap REAL NOT NULL,
        relative_percentage REAL NOT NULL,
        weight REAL NOT NULL,
        weighted_score REAL NOT NULL,
        justification TEXT,
        evidence TEXT,
        FOREIGN KEY(rfp_run_id) REFERENCES rfp_runs(rfp_run_id)
    );
    ''')
    conn.commit()
    conn.close()


def seed_criteria(db_path=DB_PATH):
    init_db(db_path)
    rows = [
        (1, 'Technical Capability', 'Architecture, integrations, scalability, technical fit', 30, 10, 1),
        (2, 'Implementation Plan', 'Timeline, milestones, staffing, delivery risks and mitigation', 20, 10, 1),
        (3, 'Commercial Value', 'Pricing clarity, total cost, assumptions and value', 20, 10, 1),
        (4, 'Security & Compliance', 'Controls, certifications, privacy, auditability and risk', 20, 10, 1),
        (5, 'Support & Experience', 'Support model, similar projects, references and experience', 10, 10, 1),
    ]
    conn = connect(db_path)
    conn.executemany('''
      INSERT INTO evaluation_criteria(criterion_id,name,description,weight,max_score,is_active)
      VALUES(?,?,?,?,?,?)
      ON CONFLICT(criterion_id) DO UPDATE SET
        name=excluded.name, description=excluded.description, weight=excluded.weight,
        max_score=excluded.max_score, is_active=excluded.is_active
    ''', rows)
    conn.commit(); conn.close()


def get_active_criteria(db_path=DB_PATH):
    conn = connect(db_path)
    rows = [dict(r) for r in conn.execute('SELECT * FROM evaluation_criteria WHERE is_active=1 ORDER BY criterion_id')]
    conn.close()
    return rows


def create_run(run_id, db_path=DB_PATH):
    conn = connect(db_path)
    conn.execute('INSERT INTO rfp_runs(rfp_run_id, created_at, status) VALUES(?,?,?)',
                 (run_id, datetime.now(timezone.utc).isoformat(), 'RUNNING'))
    conn.commit(); conn.close()


def complete_run(run_id, db_path=DB_PATH):
    conn = connect(db_path)
    conn.execute('UPDATE rfp_runs SET status=? WHERE rfp_run_id=?', ('COMPLETED', run_id))
    conn.commit(); conn.close()


def persist_results(run_id, results, db_path=DB_PATH):
    conn = connect(db_path)
    for r in results:
        conn.execute('''INSERT INTO supplier_results(
            rfp_run_id,supplier_name,submission_date,experience_rating,industry,area,
            absolute_score,ppi,area_ppi,industry_ppi,final_rank,result_json)
            VALUES(?,?,?,?,?,?,?,?,?,?,?,?)''', (
            run_id, r['supplier_name'], r['submission_date'], r['experience_rating'],
            r.get('industry'), r.get('area'), r['absolute_score'], r['ppi'],
            r.get('area_ppi'), r.get('industry_ppi'), r['final_rank'], json.dumps(r, ensure_ascii=False)
        ))
        for c in r['criteria']:
            conn.execute('''INSERT INTO criterion_results(
              rfp_run_id,supplier_name,criterion_id,criterion_name,score,benchmark_score,gap,
              relative_percentage,weight,weighted_score,justification,evidence)
              VALUES(?,?,?,?,?,?,?,?,?,?,?,?)''', (
                run_id, r['supplier_name'], c['criterion_id'], c['criterion_name'], c['score'],
                c['benchmark_score'], c['gap'], c['relative_percentage'], c['weight'],
                c['weighted_score'], c.get('justification',''), c.get('evidence','')
            ))
    conn.commit(); conn.close()


def get_all_criteria(db_path=DB_PATH):
    """Return active and inactive criteria for the Criteria Studio."""
    init_db(db_path)
    conn = connect(db_path)
    rows = [dict(r) for r in conn.execute(
        'SELECT * FROM evaluation_criteria ORDER BY criterion_id'
    )]
    conn.close()
    return rows


def ensure_seeded_criteria(db_path=DB_PATH):
    """Seed default classroom criteria only when the table is empty."""
    init_db(db_path)
    conn = connect(db_path)
    count = conn.execute('SELECT COUNT(*) AS n FROM evaluation_criteria').fetchone()['n']
    conn.close()
    if count == 0:
        seed_criteria(db_path)


def update_criterion(criterion_id, weight, max_score, is_active, db_path=DB_PATH):
    """Update configurable business rules without changing prompt code."""
    conn = connect(db_path)
    conn.execute(
        """UPDATE evaluation_criteria
           SET weight=?, max_score=?, is_active=?
           WHERE criterion_id=?""",
        (float(weight), float(max_score), 1 if is_active else 0, int(criterion_id))
    )
    conn.commit()
    conn.close()


def recent_runs(limit=20, db_path=DB_PATH):
    """Return recent persisted RFP runs."""
    init_db(db_path)
    conn = connect(db_path)
    rows = [dict(r) for r in conn.execute(
        """SELECT r.rfp_run_id, r.created_at, r.status,
                  COUNT(s.result_id) AS supplier_count,
                  MAX(CASE WHEN s.final_rank=1 THEN s.supplier_name END) AS winner
           FROM rfp_runs r
           LEFT JOIN supplier_results s ON s.rfp_run_id=r.rfp_run_id
           GROUP BY r.rfp_run_id, r.created_at, r.status
           ORDER BY r.created_at DESC
           LIMIT ?""", (int(limit),)
    )]
    conn.close()
    return rows
