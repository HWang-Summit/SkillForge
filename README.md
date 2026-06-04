# SkillForge

SkillForge 是个人 agent 技能库的长期维护源，用来集中维护可复用的 Codex 和 Claude Code skills。仓库内容通过 cc-switch 从 GitHub 拉取，再安装或同步到本机 agent 的技能根目录。

## 当前技能

- `galaxypedia-*`：从 Galaxypedia 原 skills 深度迁移而来的 Obsidian wiki 工作流，覆盖摄入、查询、lint、Defuddle、Zotero、MinerU raw 导入、JSON Canvas 和项目维护规则。
- `galaxypedia-suite`：旧调用兼容入口，只负责路由到独立 `galaxypedia-*` 技能。
- `skillforge-sync-installed-skills`：把 cc-switch 已安装但本仓库尚未维护的技能纳入 SkillForge。
- `nature-*`：源自 `Yuan1z0825/nature-skills` 的科学写作、绘图和评审技能。本仓库维护已安装子集，并保留上游共享支持目录 `skills/_shared/`。
- 其他技能：从已安装技能目录归档进本仓库的通用或第三方技能，例如 `init-project`、`mineru-pdf-parse`、`pdf-render-contact-sheet`。

## 目录结构

```text
skills/          # cc-switch、Codex、Claude Code 可安装的技能
skills/_shared/  # 非独立 skill；nature-skills 上游共享支持文件
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

## 私密环境配置

API token 和本机 Python 偏好不要写入技能文件或提交到 GitHub。需要让技能在 Codex 和 Claude Code 中稳定读取密钥时，使用本机私密 env 文件：

```bash
mkdir -p "$HOME/.skillforge"
test -f "$HOME/.skillforge/env" || cp config/skillforge.env.example "$HOME/.skillforge/env"
```

然后只在 `$HOME/.skillforge/env` 中填写真实值，例如 `MINERU_API_TOKEN`、`MINERU_CONDA_ENV` 或 `MINERU_PYTHON`。脚本型技能应在执行前加载该文件；如需使用其他路径，可设置 `SKILLFORGE_ENV_FILE=/path/to/env`。

当前 shell 或 `launchctl` 中已有的 token 可以保留，但 SkillForge 技能不依赖 GUI 进程是否继承这些环境变量。

### 脚本型技能接入规范

`$HOME/.skillforge/env` 是 SkillForge 的通用私密环境来源，不是 MinerU 专用。需要 API token、密钥或稳定 Python/CLI 环境的技能，都应提供技能内 launcher，例如 `skills/<skill-name>/scripts/run_<tool>.sh`。

launcher 负责在执行真实脚本前加载私密 env，并选择可用运行环境。不要让 `SKILL.md` 指示 agent 直接运行裸 `python`、`python3`、`curl` 或 SDK 命令来访问带密钥的服务；Codex 和 Claude Code 不保证继承同一套 shell 或 GUI 环境。

当前参考实现是 `mineru-pdf-parse/scripts/run_mineru_parse.sh`。后续新增脚本型密钥技能时，应复用同样模式，或在仓库维护脚本中加载 `scripts/load-skillforge-env.sh`。

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
- `nature-figure`、`nature-reviewer`、`nature-writing` 属于上游 `https://github.com/Yuan1z0825/nature-skills`。同步或更新这组技能时，要同时维护 `skills/_shared/`，因为 `nature-writing` 等技能会通过相对路径读取共享规则。
- SkillForge 自维护技能不能被已安装目录反向覆盖，尤其是 `galaxypedia-*`、`galaxypedia-suite` 和 `skillforge-sync-installed-skills`。
- `dist/` 是生成产物，不手动编辑，不提交。
