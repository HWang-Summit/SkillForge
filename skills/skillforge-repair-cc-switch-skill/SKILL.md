---
name: skillforge-repair-cc-switch-skill
description: 当通过 cc-switch 只安装了 GitHub 技能仓库中的单个 skill，导致运行时缺失 skill 内部文件、同仓库共享目录、_shared、公共 references/assets/templates、manifest 相对引用或其他支持文件时使用。给出上游仓库 URL 和 skill 名称后，对比上游完整 skill 与 cc-switch 已安装 skill，扫描相对依赖，dry-run 报告缺失项，并在用户确认后从上游仓库补齐文件。
---

# SkillForge Repair cc-switch Skill

这个 skill 用于修复 cc-switch 单技能安装后的缺文件问题。典型场景包括：

- 已安装 skill 目录内部缺少上游已有的 `references/`、`assets/`、`static/`、`scripts/`、`templates/` 或 manifest 片段。
- 已安装 skill 的 `manifest.yaml`、`SKILL.md` 或静态片段引用 `../_shared/...`、`../assets/...` 等同仓库相对路径，但 cc-switch 只安装了该 skill 目录。
- 上游完整 skill 中存在相对依赖，但本地已安装 skill 因为文件缺失而无法暴露这些引用。

## 边界

- 默认只做 dry-run，分别报告 `missing_skill_files` 和 `missing_support_files`。
- 只有用户明确要求修复或传入 `--apply` 时才写入 cc-switch 技能目录。
- 只补齐上游 skill 内部缺失文件，以及被相对引用命中的同仓库支持文件；不整仓复制。
- 如目标路径已有内容，默认跳过；只有显式传入更新参数才覆盖。
- 不复制 `.git`、`.env`、缓存、构建产物或可能包含密钥的文件。
- 不修改已安装 skill 的 `SKILL.md`、manifest 或源码。
- 本 skill 自身不需要 API token，不读取 `$HOME/.skillforge/env`；脚本中的 secret/path 关键词只用于安全扫描待复制文件。

## 命令

在 SkillForge 仓库根目录运行 dry-run：

```bash
python skills/skillforge-repair-cc-switch-skill/scripts/repair_cc_switch_skill.py \
  --repo-url https://github.com/Yuan1z0825/nature-skills \
  --skill-name nature-writing
```

如果上游仓库已经 clone 到本地，可避免网络访问：

```bash
python skills/skillforge-repair-cc-switch-skill/scripts/repair_cc_switch_skill.py \
  --repo-path /path/to/nature-skills \
  --skill-name nature-writing
```

确认报告后执行修复：

```bash
python skills/skillforge-repair-cc-switch-skill/scripts/repair_cc_switch_skill.py \
  --repo-url https://github.com/Yuan1z0825/nature-skills \
  --skill-name nature-writing \
  --apply
```

如需指定 cc-switch 技能目录：

```bash
python skills/skillforge-repair-cc-switch-skill/scripts/repair_cc_switch_skill.py \
  --repo-url <github-repo-url> \
  --skill-name <installed-skill-name> \
  --cc-switch-skills-dir "$HOME/.cc-switch/skills" \
  --apply
```

## 路径解析

cc-switch 技能目录按以下优先级解析：

1. CLI 参数：`--cc-switch-skills-dir <path>`
2. 环境变量：`CC_SWITCH_SKILLS_DIR`
3. `config/skillforge.local.json`
4. 默认 `$HOME/.cc-switch/skills`

上游 skill 目录会按常见结构查找：

- `skills/<skill-name>`
- `plugins/*/skills/<skill-name>`

上游来源可用 `--repo-url` 指向 GitHub 仓库，也可用 `--repo-path` 指向本地已 clone 仓库。

## 完成报告

报告上游 commit、已安装 skill 路径、发现的相对引用、缺失支持路径、已复制路径和跳过原因。修复后建议重新触发对应 skill，确认相对引用可以读取。

输出中的两类缺失：

- `missing_skill_files`：目标 skill 目录内部相对上游缺失的文件。
- `missing_support_files`：目标 skill 引用到同仓库其他位置但 cc-switch 安装目录缺失的支持文件。
