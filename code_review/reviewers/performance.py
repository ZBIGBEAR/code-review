"""Performance reviewer - performance issue checks."""
from .base import BaseReviewer

PERFORMANCE_RULES = """
## 性能规则
- N+1 查询：循环中是否有数据库查询
- 同步阻塞：异步代码中是否有同步阻塞操作
- 内存泄漏：是否有未关闭的资源、大对象引用
- 算法效率：是否有 O(n^2) 或更差的算法
- 缓存：是否有适当的缓存策略
"""


class PerformanceReviewer(BaseReviewer):
    name = "performance"

    def get_rules(self) -> str:
        return PERFORMANCE_RULES
