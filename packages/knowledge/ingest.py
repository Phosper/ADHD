import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path

import openpyxl

from packages.domain.models import KnowledgeEntry, Source


def cell_value(sheet, row, col):
    """Fill only actual merged ranges, never forward-fill arbitrary empty rows."""
    value = sheet.cell(row, col).value
    if value is None:
        for region in sheet.merged_cells.ranges:
            if region.min_row <= row <= region.max_row and region.min_col <= col <= region.max_col:
                return sheet.cell(region.min_row, region.min_col).value
    return value


def read_main(path: Path) -> tuple[list[KnowledgeEntry], dict]:
    checksum = hashlib.sha256(path.read_bytes()).hexdigest()
    book = openpyxl.load_workbook(path, data_only=True)
    try:
        if "场景汇总" not in book.sheetnames or book["场景汇总"].sheet_state != "visible":
            raise ValueError("Required visible sheet 场景汇总 is missing")
        sheet = book["场景汇总"]
        header = next((i for i in range(1, sheet.max_row + 1)
                       if sheet.cell(i, 1).value == "一级菜单" and sheet.cell(i, 3).value == "二级分类"), None)
        if not header:
            raise ValueError("Business column headers not found")
        entries, issues = [], []
        for row in range(header + 1, sheet.max_row + 1):
            reason = sheet.cell(row, 3).value
            if not reason:
                continue
            category = [str(cell_value(sheet, row, c) or "").strip() for c in (1, 2, 3)]
            channel = {"电话": "phone", "京麦驳回": "written"}.get(sheet.cell(row, 4).value, "unknown")
            answer = str(sheet.cell(row, 5).value or "").strip()
            if not answer or not all(category) or channel == "unknown":
                issues.append({"row": row, "reason": "missing_or_invalid_fields"})
            entries.append(KnowledgeEntry(entry_id=f"main-{row}", category=category,
                question=str(reason).strip(), answer=answer, channel=channel,
                source=Source(file=path.name, sheet=sheet.title, row=row, sha256=checksum)))
        return entries, {"source_sha256": checksum, "count": len(entries),
                         "channels": dict(Counter(e.channel for e in entries)),
                         "excluded_sheets": [{"name": s.title, "state": s.sheet_state}
                                             for s in book if s.title != sheet.title],
                         "issues": issues, "review_status": "pending"}
    finally:
        book.close()


def read_faq(path: Path) -> list[KnowledgeEntry]:
    checksum = hashlib.sha256(path.read_bytes()).hexdigest()
    book = openpyxl.load_workbook(path, data_only=True)
    entries = []
    try:
        for title, qcol, acol in [("高频QA", 2, 3), ("特殊场景", 3, 4)]:
            if title not in book.sheetnames or book[title].sheet_state != "visible":
                continue
            sheet = book[title]
            for row in range(2, sheet.max_row + 1):
                question, answer = sheet.cell(row, qcol).value, sheet.cell(row, acol).value
                if not question or not answer or str(question).strip() == "京麦驳回":
                    continue
                entries.append(KnowledgeEntry(entry_id=f"faq-{'general' if qcol == 2 else 'special'}-{row}",
                    category=[title], question=str(question).strip(), answer=str(answer).strip(),
                    source=Source(file=path.name, sheet=title, row=row, sha256=checksum)))
        return entries
    finally:
        book.close()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--main", type=Path, required=True)
    parser.add_argument("--faq", type=Path)
    parser.add_argument("--output", type=Path, default=Path("data/knowledge/import.json"))
    args = parser.parse_args()
    entries, summary = read_main(args.main)
    if args.faq:
        faq = read_faq(args.faq)
        entries += faq
        summary["faq_count"] = len(faq)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps({"entries": [e.model_dump() for e in entries], "summary": summary},
                                     ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False))


if __name__ == "__main__":
    main()
