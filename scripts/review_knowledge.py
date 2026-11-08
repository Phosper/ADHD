"""Apply explicit reviewer decisions to a NEW knowledge snapshot, preserving provenance."""
import argparse
import hashlib
import json
import re
from pathlib import Path

from packages.domain.models import KnowledgeEntry, utcnow


def apply_review(source: Path, decisions: Path, output: Path):
    original = source.read_bytes()
    bundle = json.loads(original)
    reviews = json.loads(decisions.read_text(encoding='utf-8'))
    if reviews['source_sha256'] != hashlib.sha256(original).hexdigest():
        raise ValueError('Review was made against a different knowledge snapshot')
    reviewer = reviews['reviewer_alias']
    if not re.fullmatch(r'[A-Za-z0-9_-]{1,50}', reviewer):
        raise ValueError('Use a team reviewer alias, not personal contact information')
    entries = {e['entry_id']: KnowledgeEntry.model_validate(e) for e in bundle['entries']}
    seen = set()
    for decision in reviews['decisions']:
        key = decision['entry_id']
        if key in seen or key not in entries:
            raise ValueError('Duplicate or unknown reviewed entry')
        seen.add(key)
        entry = entries[key]
        if decision['status'] not in ('approved', 'rejected') or not decision.get('reason', '').strip():
            raise ValueError('Each decision requires approved/rejected and a review reason')
        if decision['status'] == 'approved':
            if not entry.answer.strip() or not all(entry.category):
                raise ValueError('Incomplete source cannot be approved')
            if re.search(r'\{[^}]*\}|\[[^]]*(?:名称|电话|工号)[^]]*\]|[Xx]{3,}', entry.answer):
                raise ValueError('Unbound source placeholder; publish a separately reviewed template first')
        entry.review_status = decision['status']
    bundle['entries'] = [e.model_dump() for e in entries.values()]
    bundle['review'] = {'source_sha256':reviews['source_sha256'], 'reviewer_alias':reviewer,
                        'timestamp':utcnow(), 'decisions':reviews['decisions']}
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open('x', encoding='utf-8') as stream:
        json.dump(bundle, stream, ensure_ascii=False, indent=2)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source',type=Path)
    parser.add_argument('decisions',type=Path)
    parser.add_argument('output',type=Path)
    args = parser.parse_args()
    apply_review(args.source,args.decisions,args.output)
    print('New reviewed snapshot saved; original untouched')


if __name__ == '__main__':
    main()
