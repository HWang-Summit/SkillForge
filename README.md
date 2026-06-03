# SkillForge

SkillForge 是个人 agent 技能库的长期维护源，用来集中维护可复用的 Codex 和 Claude Code skills。仓库内容通过 cc-switch 从 GitHub 拉取，再安装或同步到本机 agent 的技能根目录。

## 当前技能

- `galaxypedia-*`：从 Galaxypedia 原 skills 深度迁移而来的 Obsidian wiki 工作流，覆盖摄入、查询、lint、Defuddle、Zotero、MinerU raw 导入、JSON Canvas 和项目维护规则。
- `galaxypedia-suite`：旧调用兼容入口，只负责路由到独立 `galaxypedia-*` 技能。
- `skillforge-sync-installed-skills`：把 cc-switch 已安装但本仓库尚未维护的技能纳入 SkillForge。
- 其他技能：从已安装技能目录归档进本仓库的通用或第三方技能，例如 `init-project`、`mineru-pdf-parse`、`nature-figure`、`nature-reviewer`。

## 目录结构

```text
skills/          # cc-switch、Codex、Claude Code 可安装的技能
suites/          # 技能套件级 manifest 和兼容信息
scripts/         # 验证、导出和同步辅助脚本
config/          # 示例配置；local 配置不提交
dist/            # 生成的兼容导出目录，不手动编辑
```

## 双平台要求

本仓库维护的技能必须同时满足 Codex 和 Claude Code 可触发、可读取、可执行完整功能：

- 每个技能目录必须有标准 `SKILL.md`。
- frontmatter 至少包含 `name` 和 `description`，且 `name` 必须与目录名一致。
- 技能正文不能写死个人机器绝对路径。
- 可执行命令优先使用仓库相对路径、技能内相对路径、`$HOME`、环境变量或本机 local config。
- 自维护技能应提供 `agents/openai.yaml`，用于 Codex UI；Claude Code 通过标准 `SKILL.md` 触发。

## 路径配置

开源仓库不提交个人绝对路径。需要让脚本知道本机目录时，按优先级使用：

1. CLI 参数，例如 `--cc-switch-skills-dir <path>`
2. 环境变量，例如 `CC_SWITCH_SKILLS_DIR`
3. `config/skillforge.local.json`
4. 默认推断，例如 `$HOME/.cc-switch/skills`

创建本机配置：

```bash
cp config/skillforge.example.json config/skillforge.local.json
```

`config/skillforge.local.json` 已被 `.gitignore` 忽略。

## 常用维护命令

校验技能：

```bash
bash scripts/validate-skills.sh
```

查看已安装技能与仓库差异：

```bash
bash scripts/sync-installed-skills.sh
```

纳入缺失的已安装技能并更新 inventory：

```bash
bash scripts/sync-installed-skills.sh --apply --inventory
```

导出 cc-switch 兼容目录：

```bash
bash scripts/export-cc-switch.sh
```

## 更新模型

- Galaxypedia 技能以本机配置的 Galaxypedia 原 skills 源目录为事实源，迁移后在 SkillForge 中使用 `galaxypedia-*` 命名空间维护。
- cc-switch 已安装技能目录是外部技能发现源。新增安装的外部技能通过 `skillforge-sync-installed-skills` 或 `scripts/sync-installed-skills.sh` 纳入本仓库。
- SkillForge 自维护技能不能被已安装目录反向覆盖，尤其是 `galaxypedia-*`、`galaxypedia-suite` 和 `skillforge-sync-installed-skills`。
- `dist/` 是生成产物，不手动编辑，不提交。
