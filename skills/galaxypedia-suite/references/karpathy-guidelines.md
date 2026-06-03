# karpathy-guidelines 模块

迁移自 Galaxypedia `skills/karpathy-guidelines/SKILL.md`。本文件是 `galaxypedia-suite` 的内部参考模块，不是 SkillForge v0.1.0 中独立安装的根目录技能。

# Karpathy Guidelines

编辑项目 Markdown、脚本或 agent 规则时，使用这些原则。
本文件受 `https://github.com/multica-ai/andrej-karpathy-skills` 启发，是本项目的本地总结，不复制该仓库内容。

## 项目贴合度

当前 Galaxypedia 已高度遵循 Karpathy 的 LLM Wiki 设计：不可变 `raw/`、LLM 维护的 `wiki/`、中央 `SCHEMA.md`、可 grep 的 `index.md`、追加式 `log.md`，以及 ingest/query/lint 三类核心工作流。

还不能称为“完美”，因为真实素材摄入、图片/附件处理、查询结果回存、长期 lint 维护仍需要实践验证。

## 原则

- 先想清楚再编辑。理解现有结构和用户的真实目标。
- 保持简单。优先使用朴素、直接的改动，避免聪明但脆弱的结构。
- 做外科式修改。除非用户明确要求，不做大范围重写。
- 保留有价值的已有内容。不要因为内容粗糙或不完整就删除知识。
- 围绕目标验证。运行能证明结构或行为正确的针对性检查。
- 任务完成就停止。不要添加推测性的抽象或额外系统。

## 脚本放置原则

默认把可执行脚本放在项目根目录 `scripts/`，而不是塞进某个 skill 目录。

适合放 `scripts/`：

- 会读写本项目真实数据，例如 `raw/`、`wiki/`、`raw/.manifest.json`。
- 需要用户手动运行或在 README 中公开说明。
- 多个 skills 都可能调用，例如 `/ingest` 调用 MinerU 预处理。
- 依赖项目环境，例如 Conda 环境 `galaxypedia`、项目根路径、vault 目录结构。

适合放 `skills/<name>/scripts/`：

- 脚本只服务于该 skill，且可随 skill 复制到其他项目。
- 脚本不假设 Galaxypedia 的具体目录结构。
- 主要用于减少 agent 重写重复代码，而不是作为项目级工具。

本项目当前只有 `scripts/mineru_parse.py`，它是项目级导入工具，应继续留在 `scripts/`。

## Markdown 应用

- 保持页面容易 grep、容易扫描。
- 优先写具体链接、来源和日期，少写模糊判断。
- 指令要短到未来 agent 真的会读。
- 两份文档重叠时，明确一个事实源，另一份指向它。

## 参考技能取舍

可以参考 `/Users/wanghao/Documents/claude-obsidian/skills` 的设计，但不要照搬。

- 当前应强化：`wiki-ingest`、`wiki-query`、`wiki-lint`、`wiki` 作为路由入口。
- 暂不引入：`wiki-fold`、`autoresearch`、`canvas`、`obsidian-bases`、`save`。
- 原因：Galaxypedia 目前的核心瓶颈是高质量摄入、查询回存和健康检查，而不是增加更多入口。
- `wiki-fold` 的作用是把较长的 `wiki/log.md` 或近期操作压缩成 meta/fold 页面。当前日志规模还小，等 `wiki/log.md` 明显变长或跨会话上下文难以恢复时再加。
