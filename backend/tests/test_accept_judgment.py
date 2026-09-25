"""竣工验收统一判定的口径回归测试。

判定只在 app/services/accept_judgment.py 里实现一份，前后端共用同一份结果；
口径如需调整，先改这里再改实现，避免两边再次漂移。

运行：cd backend && .venv/bin/python -m unittest discover -s tests -v
"""
from __future__ import annotations

import unittest

from app.services.accept import AcceptService
from app.services.accept_judgment import MATERIAL_FIELDS, judge_acceptance
from app.store import store


def _full_entry(status: str) -> dict[str, object]:
    entry: dict[str, object] = {field: "已登记" for field in MATERIAL_FIELDS}
    entry["status"] = status
    return entry


class JudgeAcceptanceTest(unittest.TestCase):
    def test_materials_ready_when_all_fields_registered(self):
        result = judge_acceptance(_full_entry("验收中"))
        self.assertEqual(result["材料齐套"], "齐套")
        self.assertEqual(result["材料缺项"], [])

    def test_materials_missing_are_listed(self):
        result = judge_acceptance({"验收单号": "ACCE-9001", "status": "待验收"})
        self.assertEqual(result["材料齐套"], "不齐套")
        self.assertEqual(result["材料缺项"], ["关联施工", "验收项目", "验收标准", "验收人员", "验收日期"])
        self.assertEqual(result["判定结论"], "不通过")

    def test_blank_fields_count_as_missing(self):
        entry = _full_entry("待验收")
        entry["验收人员"] = "   "
        result = judge_acceptance(entry)
        self.assertEqual(result["材料齐套"], "不齐套")
        self.assertEqual(result["材料缺项"], ["验收人员"])

    def test_items_qualified_follows_status(self):
        self.assertEqual(judge_acceptance(_full_entry("已通过"))["项目合格"], "合格")
        self.assertEqual(judge_acceptance(_full_entry("需返工"))["项目合格"], "不合格")
        self.assertEqual(judge_acceptance(_full_entry("验收中"))["项目合格"], "待定")
        self.assertEqual(judge_acceptance(_full_entry("待验收"))["项目合格"], "待定")

    def test_conclusion_combines_both_judgments(self):
        self.assertEqual(judge_acceptance(_full_entry("已通过"))["判定结论"], "通过")
        self.assertEqual(judge_acceptance(_full_entry("需返工"))["判定结论"], "不通过")
        self.assertEqual(judge_acceptance(_full_entry("验收中"))["判定结论"], "待定")
        incomplete = {"status": "已通过"}
        self.assertEqual(judge_acceptance(incomplete)["判定结论"], "不通过")


class AcceptServiceJudgmentTest(unittest.TestCase):
    def setUp(self):
        self.service = AcceptService()

    def test_list_and_detail_carry_shared_judgment(self):
        items, total = self.service.list_entries()
        self.assertGreater(total, 0)
        for item in items:
            self.assertIn("验收判定", item)
            self.assertEqual(item["验收判定"], judge_acceptance(item))
        detail = self.service.get_entry(int(items[0]["id"]))
        self.assertIsNotNone(detail)
        self.assertEqual(detail["验收判定"], items[0]["验收判定"])

    def test_history_rows_and_conclusion_stay_untouched(self):
        self.service.list_entries()
        self.service.get_entry(1)
        for row in store.rows("accept"):
            self.assertNotIn("验收判定", row)
            self.assertIn("验收结论", row)

    def test_filters_and_pagination_unchanged(self):
        items, total = self.service.list_entries(keyword="ACCE-0001")
        self.assertEqual(total, 1)
        self.assertEqual(items[0]["验收单号"], "ACCE-0001")
        items, total = self.service.list_entries(status="已通过")
        self.assertGreater(total, 0)
        self.assertTrue(all(item["status"] == "已通过" for item in items))
        items, total = self.service.list_entries(page=2, size=2)
        self.assertEqual(len(items), max(total - 2, 0))


if __name__ == "__main__":
    unittest.main()
