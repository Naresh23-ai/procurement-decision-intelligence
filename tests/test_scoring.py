from tools.scoring_tool import calculate_absolute_score


def test_weighted_score():
    criteria=[{'criterion_id':1,'weight':30,'max_score':10},{'criterion_id':2,'weight':70,'max_score':10}]
    e={'criteria':[{'criterion_id':1,'score':10},{'criterion_id':2,'score':5}]}
    out=calculate_absolute_score(e,criteria)
    assert out['absolute_score']==65.0
