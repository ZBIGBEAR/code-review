[English](./README_en.md) | 中文
# Code Review - 智能代码审查系统

基于 LLM 的多维度代码审查工具，支持 Git Hook 和 GitHub Actions 集成。

## 特性

- 🤖 **LLM 智能审查**：使用 Claude 模型进行代码审查
- 🔍 **多维度检查**：安全、风格、性能、测试、文档
- 📊 **评分系统**：每次代码变更获得 0-100 的综合评分
- 🪝 **Git Hook 支持**：提交前自动审查
- 🚀 **GitHub Actions**：CI/CD 自动化集成

## 安装

```bash
pip install -e .
```

或使用 uv：

```bash
uv pip install -e .
```

## 使用方式

### 审查 GitHub PR

```bash
code-review pr https://github.com/user/repo/pull/123
```

### 审查最近的提交

```bash
# 审查上一次提交
code-review commit

# 审查指定提交
code-review commit --commit abc123
```

### 审查本地代码变更

```bash
# 审查与 main 分支的差异
code-review diff --base-branch main

# 审查当前未提交的变更
code-review diff
```

### 审查指定文件

```bash
code-review file path/to/file.py
```

### 输出格式

默认输出为文本格式，支持 JSON 格式输出：

```bash
code-review pr https://github.com/user/repo/pull/123 --format json
```

## Git Hook 集成

### 安装 pre-commit hook

```bash
# 方式一：复制脚本
cp hooks/pre-commit .git/hooks/pre-commit
chmod +x .git/hooks/pre-commit

# 方式二：使用命令
code-review hook install
```

安装后，每次 `git commit` 会自动审查 staged 的代码变更。如果发现 Critical 级别的问题，将阻止提交。

## GitHub Actions 集成

在项目中创建 `.github/workflows/code-review.yml`：

```yaml
name: Code Review

on:
  pull_request:
    types: [opened, synchronize, reopened]

jobs:
  review:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.10'

      - name: Install code-review
        run: pip install code-review

      - name: Run Code Review
        env:
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
        run: |
          code-review pr ${{ github.event.pull_request.html_url }}
```

需要在 GitHub 仓库的 Settings → Secrets 中添加 `ANTHROPIC_API_KEY`。

## 环境变量

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `ANTHROPIC_API_KEY` | Anthropic API 密钥 | 必填 |
| `ANTHROPIC_BASE_URL` | API 地址 | `https://api.anthropic.com` |
| `CLAUDE_MODEL` | 使用的模型 | `claude-sonnet-4-7-20250514` |

## 评分说明

审查结果会给出 0-100 的综合评分：

| 评分 | 等级 | 说明 |
|------|------|------|
| 90-100 | ⭐⭐⭐⭐⭐ | 优秀，建议直接合并 |
| 75-89 | ⭐⭐⭐⭐ | 良好，小问题修复后可合并 |
| 60-74 | ⭐⭐⭐ | 一般，需要较大改进 |
| 40-59 | ⭐⭐ | 较差，建议大幅重构 |
| 0-39 | ⭐ | 不合格，建议重新提交 |

扣分规则：
- Critical 问题：每条 -15 分
- Warning 问题：每条 -5 分
- Suggestion：每条 -1 分

## 审查维度

1. **安全 (Security)**
   - SQL 注入、命令注入、XSS
   - 硬编码密码、API Key、Token
   - 权限控制漏洞

2. **代码风格 (Style)**
   - 命名规范
   - 格式化一致性
   - 无用代码、死代码

3. **性能 (Performance)**
   - N+1 查询问题
   - 同步阻塞
   - 内存泄漏

4. **测试 (Testing)**
   - 测试覆盖
   - 边界条件
   - Mock 使用

5. **文档 (Docs)**
   - 关键函数注释
   - README 更新
   - API 文档

## 配置文件

可在项目根目录创建 `.code-review.yaml` 自定义配置：

```yaml
scoring:
  critical_weight: -15
  warning_weight: -5
  suggestion_weight: -1

categories:
  - security
  - style
  - performance
  - test
  - docs
```

## 示例输出

```
==================================================
📋 Code Review Report
==================================================

📊 综合评分：85/100 ⭐⭐⭐⭐

🔴 Critical: 0
🟡 Warning: 3
🟢 Suggestion: 2

==================================================
🟡 Warning Issues
==================================================

• src/utils/db.py:42 - N+1 查询问题
  说明：循环中执行数据库查询
  建议：使用批量查询或 JOIN

• src/api/users.py:15 - 命名不规范
  说明：变量名不够清晰
  建议：使用更有描述性的命名

==================================================
✅ 良好，小问题修复后可合并
==================================================
```

## 技术栈

- Python 3.10+
- Click (CLI)
- Anthropic SDK (LLM)
- GitPython (Git 操作)
- PyYAML (配置)

## License

MIT

test
test2
