from scripts.release_check import check


def test_mock_or_missing_evidence_cannot_freeze_baseline():
    assert not check({'mode':'mock','passed':True})['baseline_frozen']
    assert 'human_voice_three_rounds' in check({})['missing_evidence']
