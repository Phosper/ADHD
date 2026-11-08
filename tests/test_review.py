import hashlib
import json

import pytest

from scripts.review_knowledge import apply_review


def test_review_binds_snapshot_and_never_overwrites(tmp_path):
    source = tmp_path/'source.json'
    entry = {'entry_id':'one','category':['合成类别'],'question':'怎么整改','answer':'补齐材料',
             'source':{'file':'synthetic.xlsx','sheet':'场景汇总','row':13,'sha256':'a'*64}}
    source.write_text(json.dumps({'entries':[entry]}),encoding='utf-8')
    decisions = tmp_path/'review.json'
    review = {'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'reviewer_alias':'reviewer-1',
              'decisions':[{'entry_id':'one','status':'approved','reason':'核对合成来源'}]}
    decisions.write_text(json.dumps(review),encoding='utf-8')
    target=tmp_path/'new.json'
    apply_review(source,decisions,target)
    assert json.loads(target.read_text(encoding='utf-8'))['entries'][0]['review_status']=='approved'
    with pytest.raises(FileExistsError):
        apply_review(source,decisions,target)
    review['source_sha256']='b'*64
    decisions.write_text(json.dumps(review),encoding='utf-8')
    with pytest.raises(ValueError,match='different'):
        apply_review(source,decisions,tmp_path/'invalid.json')
