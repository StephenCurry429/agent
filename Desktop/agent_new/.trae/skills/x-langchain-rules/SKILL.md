---
name: "x-langchain-rules"
description: "Project rules for x-langchain: (1) never disrupt UI layout or directory structure, (2) always git commit after coding. Invoke automatically at session start AND before any code changes."
---

# X-LangChain 项目规则

## 规则 1：禁止破坏 UI 布局和目录结构

在修改任何代码时，必须遵守以下约束：

- **不新增文件**：除非确有必要，否则不创建新文件。优先编辑已有文件。
- **不删除文件**：除非明确被要求，否则不删除任何现有文件。
- **不改动布局**：前端 HTML/CSS 的 UI 布局结构保持原样，只修改必要的最小代码行。
- **不改动目录**：项目的目录结构（src/、backend/、frontend/、data/ 等）保持原样。
- **最小化改动**：每次编辑只改必要的行，不做大范围重构或格式化。

## 规则 2：编码完成后提交代码

在每次完成编码修改后，必须执行以下操作：

1. 使用 `git diff` 确认本次改动内容
2. 使用 `git add <文件>` 暂存相关文件
3. 使用 `git commit -m "描述信息"` 提交代码
4. 提交信息需简洁描述本次改动的目的（中文或英文均可）

## 触发条件

- 在任何代码修改开始前，提醒自己遵守规则 1
- 在任何代码修改完成后，自动执行规则 2
