---
name: init-project
description: 初始化当前项目目录，按调用方创建最小智能体协作文件，并生成中文后续使用说明。
---

# init-project

在当前工作目录创建最小必要的智能体协作入口，并生成中文后续使用文档。该技能不替代 Codex 或 Claude Code 自带的 `/init`；内置 `/init` 适合根据真实代码库生成主记忆文件，本技能适合补齐最小模板和后续扩展指引。

## 初始化模式

根据调用方或用户明确意图选择一种模式：

- **Codex 模式**：当由 Codex 调用，且用户没有明确要求双平台时，只创建 `AGENTS.md` 和 `AGENT_SETUP.md`。
- **Claude Code 模式**：当由 Claude Code 调用，且用户没有明确要求双平台时，只创建 `CLAUDE.md` 和 `AGENT_SETUP.md`。
- **双平台模式**：仅当用户明确要求“同时适用于 Codex 和 Claude Code”“双平台”“两套都要”时，创建 `AGENTS.md`、`CLAUDE.md` 和 `AGENT_SETUP.md`。
- **无法判断调用方**：只创建 `AGENT_SETUP.md`，避免创建不必要的工具专用目录或文件。

默认不要创建 `.codex/`、`.claude/`、`CLAUDE.local.md` 或项目内 skills。后续使用文档会告诉用户需要哪些能力时再创建什么。

## 默认创建结构

### Codex 模式

```text
./
├── AGENTS.md
└── AGENT_SETUP.md
```

### Claude Code 模式

```text
./
├── CLAUDE.md
└── AGENT_SETUP.md
```

### 双平台模式

```text
./
├── AGENTS.md
├── CLAUDE.md
└── AGENT_SETUP.md
```

## 执行规则

1. 读取当前工作目录路径，并只在该目录内初始化项目文件。
2. 按“初始化模式”选择要创建的文件。
3. 创建缺失文件；文件已存在时绝不覆盖。
4. 默认不修改 `.gitignore`，因为默认不会创建本机私有配置。
5. 只有当用户明确要求创建本机私有配置时，才追加对应 `.gitignore` 条目。
6. 完成后报告已创建、已跳过、未创建但可后续按需创建的内容。

## 文件模板

### AGENTS.md

```markdown
# Codex 项目说明

## 项目概览

<!-- 用 1-2 句话说明这个项目做什么。 -->

## 常用命令

- 构建：<!-- e.g. pnpm build -->
- 测试：<!-- e.g. pnpm test -->
- 检查：<!-- e.g. pnpm lint -->

## 代码约定

- <!-- e.g. 使用 pnpm，不使用 npm -->
- <!-- e.g. 日期使用 ISO 8601 -->
- <!-- e.g. 优先使用项目已有 helper，避免随意新增抽象 -->

## 安全与凭证

- 不提交 secrets、tokens、private keys 或本机凭证。
- 不在日志中打印敏感环境变量或可能包含凭证的请求体。
- 本机私有配置不要进入版本控制。

## 不要触碰

- <!-- 文件、目录、生成物或行为边界，例如不要改生产配置。 -->
```

### CLAUDE.md

```markdown
# Claude Code 项目说明

## 项目概览

<!-- 用 1-2 句话说明这个项目做什么。 -->

## 项目规则

- <!-- e.g. 使用 pnpm，不使用 npm -->
- <!-- e.g. 优先做小而可审查的修改 -->
- <!-- e.g. 修改后运行最小相关测试 -->

## 安全与凭证

- 不提交 secrets、tokens、private keys 或本机凭证。
- 本机私有配置放在 `CLAUDE.local.md`，并加入 `.gitignore`。
```

### AGENT_SETUP.md

```markdown
# 智能体后续使用说明

本项目已创建最小智能体协作入口。默认只创建必要文件，避免一次性生成不使用的工具目录。

## 当前文件

- `AGENTS.md`：Codex 的项目级持久说明。仅在 Codex 模式或双平台模式下创建。
- `CLAUDE.md`：Claude Code 的项目级说明。仅在 Claude Code 模式或双平台模式下创建。
- `AGENT_SETUP.md`：中文后续使用说明。

## Codex 后续可按需创建

需要固定 Codex 行为时，可以让 Codex 创建：

- `.codex/config.toml`：项目级 Codex 配置，例如 sandbox、approval、model、reasoning、MCP 或 hooks。
- `.codex/agents/`：项目级 custom agents，用于明确的子代理工作流。
- `AGENTS.md` 的分层版本：在子目录中放更具体的 `AGENTS.md`，用于局部规则覆盖。

不要默认创建 `.codex/skills/`。Codex 可自动触发的 skills 通常放在全局 skills root，例如 `~/.codex/skills/`，项目内 skills 不应假设会自动触发。

## Claude Code 后续可按需创建

需要 Claude Code 扩展能力时，可以让 Claude Code 创建：

- `CLAUDE.local.md`：本机私有偏好或临时规则，必须加入 `.gitignore`。
- `.claude/commands/`：可复用 slash commands。
- `.claude/hooks/`：Claude Code 生命周期 hook，只放可重复、安全的自动化。
- `.claude/agents/`：Claude Code 子代理定义。
- `.claude/rules/`：路径相关规则。
- `.claude/output-styles/`：输出风格定义。

## 建议用法

- 首次使用 Codex 时，可以先运行 Codex 自带 `/init` 生成或改进 `AGENTS.md`。
- 首次使用 Claude Code 时，可以先运行 Claude Code 自带 `/init` 生成或改进 `CLAUDE.md`。
- 本文档用于提醒后续可以扩展什么，不要求现在全部创建。

## 安全提醒

- 不提交密钥、token、私钥或本机凭证。
- 不把临时实验规则写进长期项目说明。
- 创建 hook 或自动化前，确认它可以安全重复执行。
```

## 后续按需模板

### CLAUDE.local.md

```markdown
# Claude Code 本机私有说明

<!-- 本机私有偏好，只在当前机器使用。该文件应被 .gitignore 忽略。 -->
```

### .gitignore 私有配置追加项

```gitignore
# Agent local config
CLAUDE.local.md
.claude/settings.local.json
.codex/local/
```
