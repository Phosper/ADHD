"""Summarize a named cohort, never mix revisions or call schedule time acoustic latency."""
import argparse
import json
import math
import statistics
from pathlib import Path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('reports',type=Path,nargs='+')
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    records=[json.loads(p.read_text(encoding='utf-8')) for p in args.reports]
    hashes={r['session']['manifest']['prompt_sha256'] for r in records}
    if len(hashes)!=1:
        parser.error('Do not pool different prompt revisions')
    timings=[v for r in records for v in r['measurement']['starts']]
    if not timings or any(not math.isfinite(v) or v<0 for v in timings):
        parser.error('Invalid timing evidence')
    ordered=sorted(timings)
    result={'measurement':'synthetic-input end to browser AudioContext schedule',
        'official_acceptance':False,'acoustic_latency':False,'sessions':len(records),'samples':len(timings),
        'p50_ms':statistics.median(timings),'p95_nearest_rank_ms':ordered[math.ceil(len(ordered)*.95)-1],
        'max_ms':max(timings),'prompt_sha256':next(iter(hashes)),
        'successful_writebacks':sum(r['session']['outcome']['merchant_response']=='will_resubmit' for r in records),
        'raw_reports':[str(p) for p in args.reports], 'values_ms':timings,
        'limitations':['Synthetic input, no human microphone/noise acceptance',
                       'Prewarmed deterministic speech; not uncached arbitrary answers',
                       'Official network and measurement method unconfirmed']}
    with args.output.open('x',encoding='utf-8') as stream:
        json.dump(result,stream,ensure_ascii=False,indent=2)
    print(json.dumps(result,ensure_ascii=True,indent=2))


if __name__=='__main__':
    main()
