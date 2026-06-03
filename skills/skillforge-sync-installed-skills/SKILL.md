---
name: skillforge-sync-installed-skills
description: 当维护 SkillForge 技能库、同步 cc-switch 已安装技能、把新安装技能纳入当前仓库、检查 skills 目录差异、生成 skill inventory，或更新 Codex/Claude Code 共用技能源时使用。
---

# SkillForge Sync Installed Skills

使用这个 skill，把本机 agent 环境中已经安装的技能纳入 SkillForge 源仓库，并保持 Codex 与 Claude Code 都能触发和使用。

## 边界

- SkillForge 是长期源码仓库；已安装技能目录只是发现源。
- 默认只做 dry-run，报告 SkillForge 与已安装技能目录的差异。
- 只有用户明确要求同步、纳入、更新或传入 `--apply` 时才复制文件。
- 不要从已安装目录反向覆盖 SkillForge 自维护技能：`galaxypedia-*`、`galaxypedia-suite`、`skillforge-sync-installed-skills`。
- 不要把本机绝对路径写入 `SKILL.md`、README 或可提交配置。

## 路径解析

不要把个人机器路径写死进技能文件。运行脚本时按以下顺序解析已安装技能目录：

1. CLI 参数：`--cc-switch-skills-dir <path>`
2. 环境变量：`CC_SWITCH_SKILLS_DIR`
3. 本机私有配置：`config/skillforge.local.json`
4. 默认推断：`$HOME/.cc-switch/skills`

Galaxypedia 原 skills 源目录按同样模式使用 `--galaxypedia-skills-dir`、`GALAXYPEDIA_SKILLS_DIR` 或本机私有配置解析。

## 工作流

1. 在 SkillForge 仓库根目录运行 dry-run：

```bash
bash scripts/sync-installed-skills.sh
```

2. 阅读报告，确认缺失、已存在、hash 不同和默认跳过的技能。
3. 用户确认后同步缺失技能：

```bash
bash scripts/sync-installed-skills.sh --apply --inventory
```

4. 如需更新已归档的外部技能，显式使用：

```bash
bash scripts/sync-installed-skills.sh --apply --update-existing --inventory
```

5. 同步后运行：

```bash
bash scripts/validate-skills.sh
```

## 双平台要求

- 每个纳入 SkillForge 的技能都必须有标准 `SKILL.md`，frontmatter 包含 `name` 和 `description`。
- 技能正文应避免只适配 Codex 或只适配 Claude Code 的路径。需要平台差异时，同时给出两端方案，或使用 `$HOME`、仓库相对路径、环境变量、配置解析。
- 对脚本型技能，优先使用技能内相对路径或项目脚本路径，不假设技能只安装在某个绝对目录。

## 完成报告

报告已同步、跳过、hash 不同但未更新、更新的技能，以及是否生成 `skill-inventory.json`。
