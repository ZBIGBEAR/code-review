"""LLM client for code review."""
import anthropic
import os
from dotenv import load_dotenv

load_dotenv()

MODEL = os.getenv("CLAUDE_MODEL", "claude-sonnet-4-7-20250514")


def get_client() -> anthropic.Anthropic:
    return anthropic.Anthropic(
        api_key=os.getenv("ANTHROPIC_API_KEY"),
        base_url=os.getenv("ANTHROPIC_BASE_URL"),
    )


def chat(messages: list, system: str = "", max_tokens: int = 8192) -> str:
    """Call LLM and return text response."""
    client = get_client()
    response = client.messages.create(
        model=MODEL,
        system=system,
        messages=messages,
        max_tokens=max_tokens,
    )
    return response.content[0].text


REVIEW_SYSTEM_PROMPT = """你是一个专业的代码审查专家，负责审查代码变更。

## 你的任务
审查用户提供的代码变更（git diff），从以下几个维度进行检查：

1. **代码风格 (Style)**
   - 命名规范、不一致的格式化、代码整洁度
   - 无用导入、死代码、过深嵌套

2. **安全 (Security)** - 最关键
   - SQL 注入、命令注入、XSS 等注入漏洞
   - 硬编码密码、API Key、Token 等敏感信息
   - 权限控制问题、认证授权漏洞

3. **性能 (Performance)**
   - N+1 查询问题
   - 同步阻塞、内存泄漏
   - 低效算法

4. **测试 (Testing)**
   - 测试覆盖是否充分
   - 边界条件是否覆盖
   - Mock 使用是否正确

5. **文档 (Docs)**
   - 关键函数是否有注释
   - README 是否需要更新

## 输出格式
请严格按照以下 JSON 格式输出，不要包含任何其他内容：

{
  "issues": [
    {
      "severity": "critical|warning|suggestion",
      "category": "security|style|performance|testing|docs",
      "file": "文件路径",
      "line": 行号或行号范围,
      "title": "问题简述",
      "description": "详细说明",
      "suggestion": "修复建议"
    }
  ]
}

## 评分规则
根据问题严重程度计算综合评分（满分100）：
- Critical 问题：每条 -15 分
- Warning 问题：每条 -5 分
- Suggestion：-1 分
- 最低 0 分

## 注意事项
- 只报告真实存在的问题
- 如果没有问题，在 issues 中返回空数组
- 如果不确定，用 "?" 标注
- 不要误报，不要漏报
"""


def review_code(diff_content: str, language: str = "python") -> str:
    """Review code diff using LLM."""
    messages = [
        {"role": "user", "content": f"请审查以下 {language} 代码变更：\n\n{diff_content}"}
    ]
    return chat(messages, system=REVIEW_SYSTEM_PROMPT)
