"""LLM client for code review."""
import anthropic
from dotenv import load_dotenv
import os

load_dotenv(override=True)

SYSTEM = """你是一个专业的代码审查专家。你的任务是对代码变更进行全面审查。

## 你的工作方式
1. 首先了解项目结构和修改的文件
2. 仔细阅读修改的代码，理解改动意图
3. 探索可能受影响的未修改代码（改动可能影响其他模块）
4. 从多个维度审查代码
5. 给出结构化的审查结果

## 审查维度
1. **安全 (Security)** - 最重要
   - SQL 注入、命令注入、XSS 等注入漏洞
   - 硬编码密码、API Key、Token 等敏感信息
   - 权限控制问题

2. **正确性 (Correctness)**
   - 逻辑错误、空指针、边界条件
   - 并发问题、线程安全
   - 错误处理

3. **性能 (Performance)**
   - N+1 查询、循环中的数据库操作
   - 内存泄漏、资源未关闭
   - 低效算法

4. **代码风格 (Style)**
   - 命名规范、代码整洁
   - 重复代码、过深嵌套

5. **测试 (Testing)**
   - 测试覆盖是否充分
   - 边界条件是否覆盖

6. **影响分析 (Impact)**
   - 这个改动是否会影响其他未修改的模块
   - 是否有 breaking change

## 重要原则
- 不要只盯着 diff，要看完整的上下文
- 使用 read_file 工具阅读相关文件
- 使用 bash 工具执行 git 命令查看更多信息
- 不要误报，不要漏报
- 如果不确定，用 "?" 标注

## 输出要求
当你完成审查后，必须调用 browse_codebase 工具并输入 "done" 来结束审查，返回结构化的审查结果。

审查结果格式：
{
  "score": 0-100,
  "rating": "⭐-⭐⭐⭐⭐⭐",
  "summary": "简短总结",
  "issues": [
    {
      "severity": "critical|warning|suggestion",
      "category": "security|correctness|performance|style|testing|impact",
      "file": "文件路径",
      "line": 行号,
      "title": "问题简述",
      "description": "详细说明",
      "suggestion": "修复建议"
    }
  ]
}

评分标准（满分100）：
- Critical: -15分/条
- Warning: -5分/条
- Suggestion: -1分/条
"""

TOOLS = [
    {
        "name": "bash",
        "description": "执行 shell 命令。看 git diff、git log、git show 等 git 相关命令，以及任何需要的 shell 命令。",
        "input_schema": {
            "type": "object",
            "properties": {
                "command": {"type": "string", "description": "要执行的命令"},
            },
            "required": ["command"],
        },
    },
    {
        "name": "read_file",
        "description": "读取文件内容。用于查看完整的文件代码，了解上下文。",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "文件路径（相对于项目根目录）"},
                "limit": {"type": "integer", "description": "最多读取的行数（可选）"},
            },
            "required": ["path"],
        },
    },
    {
        "name": "browse_codebase",
        "description": "完成审查时调用此工具返回审查结果。输入 'done' 表示审查完成。",
        "input_schema": {
            "type": "object",
            "properties": {
                "result": {"type": "string", "description": "审查结果，必须是 JSON 格式字符串"},
            },
            "required": ["result"],
        },
    },
]

_client = None
MODEL = os.getenv("CLAUDE_MODEL", "MiniMax-M2.7")


def get_client():
    global _client
    if _client is None:
        _client = anthropic.Anthropic(
            api_key=os.getenv("ANTHROPIC_API_KEY"),
            base_url=os.getenv("ANTHROPIC_BASE_URL"),
        )
    return _client


def chat(messages: list, **kwargs):
    client = get_client()
    max_tokens = kwargs.get("max_tokens", 8192)
    system = kwargs.get("system", SYSTEM)
    tools = kwargs.get("tools", TOOLS)

    response = client.messages.create(
        model=MODEL,
        system=system,
        messages=messages,
        tools=tools,
        max_tokens=max_tokens,
    )
    return response
