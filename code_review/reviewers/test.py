"""Test reviewer - test coverage checks."""
from .base import BaseReviewer

TEST_RULES = """
## 测试规则
- 测试覆盖：新增代码是否有对应的测试
- 边界条件：空值、0、负数、极大值是否覆盖
- Mock 使用：外部依赖是否正确 Mock
- 断言质量：断言是否有意义，是否过于宽松
"""


class TestReviewer(BaseReviewer):
    name = "test"

    def get_rules(self) -> str:
        return TEST_RULES
