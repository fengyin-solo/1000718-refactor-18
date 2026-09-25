"""竣工验收判定口径：验收材料是否齐套、验收项目是否合格。

这两套判定在全系统只有这一份实现：

- 后端接口（列表、明细、登记、动作、导出）统一调用这里的函数；
- 前端页面从接口返回的「验收判定」字段读取同一份结果，不在页面里另写规则。

判定只读取验收单已有字段，不改写验收结论、不改动历史验收单数据，
也不影响列表的筛选与分页口径。
"""
from __future__ import annotations

from typing import Any

# 接口返回里挂载判定结果的字段名，前后端都认这一个 key。
CHECK_FIELD = "验收判定"

# 验收材料是否齐套：单号、关联施工、项目、标准、结论、人员、日期七项材料全部填写才算齐套。
MATERIAL_FIELDS = ["验收单号", "关联施工", "验收项目", "验收标准", "验收结论", "验收人员", "验收日期"]

# 验收项目是否合格：验收单确认通过才算合格；需返工或仍在验收流程中的都不算合格。
QUALIFIED_STATUS = "已通过"


def materials_complete(entry: dict[str, Any]) -> bool:
    """验收材料是否齐套：七项验收材料字段全部有值。"""
    return all(str(entry.get(field) or "").strip() for field in MATERIAL_FIELDS)


def items_qualified(entry: dict[str, Any]) -> bool:
    """验收项目是否合格：验收单已流转到「已通过」。"""
    return entry.get("status") == QUALIFIED_STATUS


def acceptance_check(entry: dict[str, Any]) -> dict[str, bool]:
    """一份验收单的两套判定结果，前后端共用这一份。"""
    return {"材料齐套": materials_complete(entry), "项目合格": items_qualified(entry)}
