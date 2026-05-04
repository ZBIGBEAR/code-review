"""Security reviewer - security vulnerability checks."""
from .base import BaseReviewer

SECURITY_RULES = """
## 安全规则
- SQL 注入：拼接 SQL 时是否使用参数化查询
- 命令注入：是否使用用户输入拼接系统命令
- XSS：是否对用户输入进行转义
- 敏感信息：是否硬编码密码、API Key、Token、密钥等
- 权限控制：是否有适当的权限检查
- 依赖安全：是否使用已知漏洞的依赖
"""


class SecurityReviewer(BaseReviewer):
    name = "security"

    def get_rules(self) -> str:
        return SECURITY_RULES
