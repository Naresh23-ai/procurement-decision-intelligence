from tools.ranking_tool import rank_suppliers


def test_tie_break_order():
    rows=[
      {'supplier_name':'B','ppi':90,'submission_date':'2026-08-20','experience_rating':9},
      {'supplier_name':'A','ppi':90,'submission_date':'2026-08-19','experience_rating':7},
    ]
    out=rank_suppliers(rows)
    assert out[0]['supplier_name']=='A'
    assert out[0]['final_rank']==1
