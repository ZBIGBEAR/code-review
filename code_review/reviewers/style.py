"""Style reviewer - code style checks."""
from .base import BaseReviewer

STYLE_RULES = """
## 风格规则
- 命名规范：变量、函数、类命名是否清晰一致
- 格式化：缩进、空格、换行是否一致
- 无用代码：无用导入、未使用变量、死代码
- 嵌套深度：嵌套是否过深（>3层建议拆分）
- 代码重复：是否有明显的重复代码
"""


class StyleReviewer(BaseReviewer):
    name = "style"

    def get_rules(self) -> str:
        return STYLE_RULES
