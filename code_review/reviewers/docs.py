"""Docs reviewer - documentation checks."""
from .base import BaseReviewer

DOCS_RULES = """
## 文档规则
- 关键函数：是否有关键函数缺少注释
- README：新增功能是否需要更新 README
- API 文档：公开 API 是否需要更新文档
- 复杂逻辑：复杂算法是否有解释性注释
"""


class DocsReviewer(BaseReviewer):
    name = "docs"

    def get_rules(self) -> str:
        return DOCS_RULES
