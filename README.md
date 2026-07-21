# SkillForge

SkillForge 是个人 agent 技能库的长期维护源，用来集中维护可复用的 Codex 和 Claude Code skills。仓库内容通过 cc-switch 从 GitHub 拉取，再安装或同步到本机 agent 的技能根目录。

## 当前技能列表

本仓库当前维护 24 个独立 skill。`skills/_shared/` 是 `nature-*` 技能使用的共享支持目录，不作为独立 skill 触发。

### 文献检索与期刊决策

| Skill | 用途 |
| --- | --- |
| `ai-science-literature-survey` | 面向 Bioinformatics、Geospatial & Earth Informatics、Astroinformatics 的 AI for Science 文献严格检索、题录级采集、目标会议/期刊限定、领域分类、去重、校验和中文报告生成。 |

### 学术写作、作图与投稿评估

| Skill | 用途 |
| --- | --- |
| `nature-figure` | 面向 Nature 或高水平期刊的投稿级科学绘图工作流，支持 Python 或 R。 |
| `nature-reviewer` | 以 Nature 风格审稿人视角进行投稿前评估，输出 3 份 reviewer reports 和综合意见。 |
| `nature-writing` | 起草、重构或规划 Nature 风格论文段落和章节，包括摘要、引言、方法、实验、讨论等。 |

### PDF 与文档处理

| Skill | 用途 |
| --- | --- |
| `mineru-pdf-parse` | 使用 MinerU 解析 PDF、本地或远程 PDF 转 Markdown，提取论文、图片、公式或表格。 |
| `pdf-layout-inspection` | 检查 PDF 的版式与页面视觉问题，按需渲染逐页 PNG 和 contact sheet。 |

### Zotero 文献库

| Skill | 用途 |
| --- | --- |
| `zotero-dev-library` | 通过本地开发 API 与 CLI 安全读写正在运行的 Zotero 开发版：条目、collection、metadata、标签、成员关系和既有相对链接附件。 |
| `zotero-galaxypedia-bridge` | 论文 PDF 的 canonical bundle、MinerU、AI 分类提案与 Zotero relative linked attachment 的两阶段 Bridge。 |
| `zotero-galaxypedia-removal-sync` | 仅在明确授权后检查 Zotero 回收站、阻止死链/共享知识页风险，并同步永久清理 Obsidian 文献资产。 |
| `zotero-local-pdf-attach` | **已弃用兼容技能**：仅维护历史 Zotero storage 托管附件；新的论文附件使用 Galaxypedia Bridge 的 relative linked attachment。 |
| `zotero-cloud-library` | **已弃用兼容技能**：当前开发工作流不经 Zotero Web API 写入；官方云端同步由 Zotero Desktop 自己负责。 |

### Galaxypedia 知识库

| Skill | 用途 |
| --- | --- |
| `galaxypedia-defuddle` | 清洗网页文章、博客、文档页 URL，并保存为 Galaxypedia raw/articles Markdown 来源。 |
| `galaxypedia-json-canvas` | 创建和维护 Obsidian JSON Canvas 文件，用于白板、概念图、架构图、工作流图和 topic map。 |
| `galaxypedia-karpathy-guidelines` | 维护 Galaxypedia Markdown、脚本或 agent 指令时遵循的简单、直接、目标驱动改动规则。 |
| `galaxypedia-mineru-import` | 解析非论文 Bridge 管理的 PDF、Office、图片或文件型 URL；`raw/papers` 论文 PDF 不使用此技能。 |
| `galaxypedia-notion-literature-notes` | 将 Galaxypedia/Obsidian 中的论文、summary、concept/entity 页面整理为 Notion 文献阅读笔记。 |
| `galaxypedia-wiki` | Galaxypedia wiki 总入口，路由摄入、查询、检查、MinerU 预处理、模板/frontmatter 规范和知识库维护任务。 |
| `galaxypedia-wiki-ingest` | 统一摄入入口；分流 raw Markdown、非论文 MinerU 来源与论文 Bridge 流程，并维护 summary、entity、concept、index 和 log。 |
| `galaxypedia-wiki-lint` | 检查 Galaxypedia wiki 健康状态，包括未索引页面、死链、孤儿页、缺失交叉引用和一致性问题。 |
| `galaxypedia-wiki-query` | 按 quick、standard、deep 模式查询 Galaxypedia wiki，综合回答并可回存高价值答案。 |
| `galaxypedia-zotero-ingest` | **已弃用兼容技能**：仅用于历史 SQLite metadata/index 的只读核查；新论文流程使用 `galaxypedia-wiki-ingest` 与 Bridge。 |

### SkillForge 维护

| Skill | 用途 |
| --- | --- |
| `init-project` | 初始化当前项目目录，创建最小智能体协作文件，并生成中文后续使用说明。 |
| `skillforge-repair-cc-switch-skill` | 修复 cc-switch 单独安装 GitHub skill 后缺失上游共享目录、相对依赖或支持文件的问题。 |
| `skillforge-sync-installed-skills` | 同步已安装技能、纳入新 skill、检查目录差异并生成 `skill-inventory.json`。 |

## 目录结构

```text
skills/          # cc-switch、Codex、Claude Code 可安装的技能
skills/_shared/  # 非独立 skill；nature-skills 上游共享支持文件
suites/          # 技能套件级 manifest 和兼容信息
scripts/         # 验证、导出和同步辅助脚本
config/          # 示例配置；local 配置不提交
dist/            # 生成的兼容导出目录，不手动编辑
```

## Zotero–Galaxypedia 论文工作流

`galaxypedia-wiki-ingest` 是论文摄入的唯一入口。非论文文件型来源继续使用 `galaxypedia-mineru-import`；位于 `raw/papers` 的 PDF、外部论文 PDF 和 Zotero 附件则使用 Zotero-Galaxypedia Bridge。

每篇论文只有一个稳定 bundle：`raw/papers/pdf-<sha-prefix>/`，其中包含标题命名的 PDF、`paper.mineru.md` 与 `paper.mineru/` 资源。Zotero collection 的移动或改名不会移动 bundle。

1. `stage-pdf`、`stage-legacy-pdf`、`stage-papers-inbox` 或 `stage-zotero-item`：复制前先登记 `pending_copy`、MinerU 前登记 `pending_parse`、成功后才返回 `pending_classification` 与当前 collection tree；不写 Zotero，也不删除来源。手动下载的论文先放入 `raw/papers/_inbox/`，按需调用 `stage-papers-inbox` 递归扫描。`pending_copy`/`pending_parse` 修复后用 `resume-stage <bundle> --apply` 显式恢复，不自动重试。外部 PDF 须在 commit 前以 `verify-metadata` 写入绑定 hash/path 的可信题录，不能把 MinerU 正文或参考文献年份直接写入 Zotero。
2. Codex/Claude 根据标题、摘要、DOI、关键词和 MinerU 正文开头生成可审计的分类提案。批量 `_inbox` stage 时使用每篇一个的 `outputs/classification-proposals/<pdf-sha256>.json`。优先已有二级 collection；低置信度或多个合理候选使用 `needs_review`，不写 collection。对已有 Zotero 条目，Zotero 的 title、DOI、年份和 creators 是 canonical metadata，MinerU metadata 仅用于内容验证、分类和 wiki；title/DOI 矛盾会停在 `content_mismatch`。
3. `commit-bundle` 校验提案后创建/复用 Zotero 条目、追加确认的 collection、建立并读回验证 relative linked attachment。Zotero 来源默认在验证后删除旧 linked PDF，使 `raw/papers/pdf-<hash>/` 成为唯一物理 PDF；历史保留源文件的 bundle 用 `cleanup-source` 显式收敛。新建一级/二级 collection 必须经用户明确确认。
4. 成功后摄入 bundle 的 `paper.mineru.md` 到 wiki；不会重复执行 MinerU。

删除文献时，先在 Zotero 将条目移入回收站；不会实时同步。用户明确触发 `zotero-galaxypedia-removal-sync` 后，skill 先生成回收站快照与 Obsidian 影响计划。只有不存在 summary backlink、共享知识页或 manifest/source-index 风险，才会在 Obsidian 事务和死链校验成功后永久清空整个 Zotero 回收站。普通 ingest、audit、reconcile 不会删除回收站内容。

Zotero Desktop 继续负责 metadata 与 collection 的官方云端同步。relative linked PDF 的文件本身以 `raw/papers` 为事实源，不作为 Zotero 云端附件上传。

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

修复 cc-switch 单技能安装后缺失的上游共享支持文件：

```bash
python skills/skillforge-repair-cc-switch-skill/scripts/repair_cc_switch_skill.py \
  --repo-url <github-repo-url> \
  --skill-name <installed-skill-name>
```

## 更新模型

- SkillForge 中的 `galaxypedia-*`、`zotero-dev-library` 和 `zotero-galaxypedia-bridge` 是当前工作流的唯一规范源。此仓库不自动安装、复制或链接这些 Skill 到其他本机目录。
- cc-switch 已安装技能目录是外部技能发现源。新增安装的外部技能通过 `skillforge-sync-installed-skills` 或 `scripts/sync-installed-skills.sh` 纳入本仓库。
- 如果某个 GitHub 仓库的单个 skill 通过 cc-switch 安装后缺失同仓库共享目录、`_shared`、公共 references/assets/templates 或 manifest 相对引用，使用 `skillforge-repair-cc-switch-skill` 从上游仓库补齐支持文件。
- `nature-figure`、`nature-reviewer`、`nature-writing` 属于上游 `https://github.com/Yuan1z0825/nature-skills`。同步或更新这组技能时，要同时维护 `skills/_shared/`，因为 `nature-writing` 等技能会通过相对路径读取共享规则。
- SkillForge 自维护技能不能被已安装目录反向覆盖，尤其是 `galaxypedia-*` 和 `skillforge-sync-installed-skills`。
- `dist/` 是生成产物，不手动编辑，不提交。
