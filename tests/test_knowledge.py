from pathlib import Path

import openpyxl
import pytest

from packages.domain.contact_policy import contact_policy
from packages.domain.models import Case, KnowledgeEntry, Source
from packages.knowledge.ingest import read_main
from packages.knowledge.retrieve import Retriever


def workbook(path: Path):
    book = openpyxl.Workbook()
    sheet = book.active
    sheet.title = "场景汇总"
    sheet.append(["一级菜单", "一级分类", "二级分类", "关单方式", "话术"])
    sheet.append(["品牌", "授权", "缺盖章", "电话", "请补齐盖章"])
    sheet.append([None, None, "缺日期", "京麦驳回", "请补齐日期"])
    sheet.merge_cells("A2:A3")
    sheet.merge_cells("B2:B3")
    hidden = book.create_sheet("电话场景")
    hidden.sheet_state = "hidden"
    hidden.append(["不应导入"])
    book.save(path)


def test_import_visible_allowlist_and_merged_cells(tmp_path):
    path = tmp_path / "source.xlsx"
    workbook(path)
    entries, summary = read_main(path)
    assert len(entries) == 2
    assert entries[1].category == ["品牌", "授权", "缺日期"]
    assert summary["channels"] == {"phone": 1, "written": 1}
    assert summary["excluded_sheets"] == [{"name": "电话场景", "state": "hidden"}]
    assert all(e.review_status == "pending" for e in entries)
    assert entries[0].source.row == 2 and len(entries[0].source.sha256) == 64


def test_import_missing_visible_main_rejected(tmp_path):
    path = tmp_path / "wrong.xlsx"
    openpyxl.Workbook().save(path)
    with pytest.raises(ValueError):
        read_main(path)


def test_pending_evidence_not_retrieved():
    e = KnowledgeEntry(entry_id="a", category=["授权"], question="授权书怎么补齐",
                       answer="补齐盖章页", source=Source(file="synthetic", sheet="s", row=1, sha256="0"*64))
    assert Retriever([e]).search("授权书") == []
    e.review_status = "approved"
    assert Retriever([e]).search("授权书")[0][0].entry_id == "a"
    assert Retriever([e]).search("授权书", allowed_ids={"other"}) == []


@pytest.mark.parametrize("count,connected,retry,channel,followup", [
    (1, False, False, "written", False), (2, False, False, "phone", True),
    (2, False, True, "written", False), (3, True, False, "written", False),
    (1, True, False, "phone", False),
])
def test_contact_policy(count, connected, retry, channel, followup):
    case = Case(case_id="x", company="合成", brand="合成", scene_id="x", reason="缺材料",
                required_actions=["补齐"], reviewed=True, submission_count=count)
    result = contact_policy(case, connected=connected, retry_attempt=retry)
    assert (result.channel, result.followup) == (channel, followup)


def test_callback_override_and_unreviewed_case():
    case = Case(case_id="x", company="合成", brand="合成", scene_id="x", reason="缺材料",
                required_actions=["补齐"], submission_count=3, callback_requested=True)
    assert contact_policy(case, connected=True).channel == "human"
    case.reviewed = True
    assert contact_policy(case, connected=True).channel == "phone"
