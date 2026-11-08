import pytest

from packages.domain.models import Case, DomainError
from packages.storage.sqlite import Store


@pytest.mark.parametrize('count,retry,channel,followup',[(1,False,'written',False),
                          (2,False,'phone',True),(2,True,'written',False)])
def test_no_answer_transaction_idempotency(tmp_path,count,retry,channel,followup):
    store=Store(tmp_path/'case.sqlite')
    store.seed([Case(case_id='one',company='合成公司',brand='合成',scene_id='one',
                     reason='缺材料',required_actions=['补材料'],reviewed=True,submission_count=count)])
    s=store.create('one','start',{})
    body={'request_id':'missed','expected_version':0,'retry_attempt':retry}
    result=store.no_answer(s.session_id,body)
    assert result.outcome.contact_status=='no_answer'
    assert result.outcome.identity_status=='unknown'
    assert result.outcome.recommended_channel==channel
    assert bool(result.outcome.followup_id)==followup
    assert store.no_answer(s.session_id,body)==result
    assert store.cases()[0].version==2
    with pytest.raises(DomainError):
        store.no_answer(s.session_id,{**body,'retry_attempt':not retry})
