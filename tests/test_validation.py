from tools.validation_tool import validate_and_normalize


def test_missing_and_out_of_range():
    criteria=[
      {'criterion_id':1,'name':'A','max_score':10},
      {'criterion_id':2,'name':'B','max_score':10},
    ]
    raw={'supplier_name':'X','criteria':[{'criterion_id':1,'score':13}]}
    out=validate_and_normalize(raw,'X',criteria)
    assert out['criteria'][0]['score']==10
    assert out['criteria'][1]['score']==0
    assert len(out['warnings'])>=2
