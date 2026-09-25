"""竣工验收判定：验收材料是否齐套、验收项目是否合格，全系统只有这一份实现。

前端页面与后端接口展示的都是 `judge_acceptance` 的返回结果，
任何一方不得再各自实现一套口径，避免同一份验收单得出不同结论。

判定口径（只读取验收单已有字段，不改动任何历史数据与既有结论）：

- 材料齐套：验收单号、关联施工、验收项目、验收标准、验收人员、验收日期
  六项材料全部登记（非空白）为「齐套」；否则为「不齐套」，缺项列入「材料缺项」。
- 项目合格：验收单状态为「已通过」判定「合格」，「需返工」判定「不合格」，
  其余状态（待验收、验收中）判定「待定」。
- 判定结论：材料不齐套或项目不合格 → 「不通过」；
  材料齐套且项目合格 → 「通过」；其余 → 「待定」。
"""
from __future__ import annotations

from typing import Any, Mapping

# 验收材料清单：六项全部登记才算齐套
MATERIAL_FIELDS = ["验收单号", "关联施工", "验收项目", "验收标准", "验收人员", "验收日期"]

QUALIFIED_STATUS = "已通过"
UNQUALIFIED_STATUS = "需返工"


def judge_acceptance(entry: Mapping[str, Any]) -> dict[str, Any]:
    """对单条验收单给出材料齐套、项目合格与综合判定结论。"""
    missing = [field for field in MATERIAL_FIELDS if not str(entry.get(field) or "").strip()]
    materials_ready = not missing

    status = str(entry.get("status") or "")
    if status == QUALIFIED_STATUS:
        items_qualified = "合格"
    elif status == UNQUALIFIED_STATUS:
        items_qualified = "不合格"
    else:
        items_qualified = "待定"

    if not materials_ready or items_qualified == "不合格":
        conclusion = "不通过"
    elif items_qualified == "合格":
        conclusion = "通过"
    else:
        conclusion = "待定"

    return {
        "材料齐套": "齐套" if materials_ready else "不齐套",
        "项目合格": items_qualified,
        "判定结论": conclusion,
        "材料缺项": missing,
    }
