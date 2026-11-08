"""Fail closed on absent acceptance evidence; never bless Mock as real voice."""
import argparse
import json
from pathlib import Path


def check(evidence: dict):
    required = ['independent_business_review', 'human_voice_three_rounds',
                'acoustic_p50_le_2000ms', 'no_severe_compliance_violation',
                'approved_competition_network', 'official_tool_contract_verified',
                'restore_drill', 'clean_source_checkpoint']
    missing = [key for key in required if evidence.get(key,{}).get('passed') is not True
               or not evidence.get(key,{}).get('artifact')]
    return {'baseline_frozen':not missing,'missing_evidence':missing,
            'note':'Artifact references must be checked by a reviewer; flags alone are not certification'}


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('evidence',type=Path)
    args=parser.parse_args()
    result=check(json.loads(args.evidence.read_text(encoding='utf-8')))
    print(json.dumps(result,ensure_ascii=False,indent=2))
    if not result['baseline_frozen']:
        raise SystemExit(1)


if __name__=='__main__':
    main()
