# SkillForge

SkillForge 是王昊的个人 agent 技能库，用来集中维护可复用的 Codex 和 Claude Code skills。仓库作为长期编辑源，cc-switch 可以从 GitHub 拉取技能，并把它们安装到本地 agent 的技能根目录。

## 当前技能套件

- `galaxypedia-suite`：Galaxypedia 风格 wiki 工作流路由技能，覆盖 wiki 摄入、查询、健康检查、Defuddle 网页文章预处理、Zotero 文献摄入、Obsidian JSON Canvas 和项目维护规则。

`galaxypedia-suite` 不打包 MinerU。PDF、Office、图片或远程文档解析继续使用已经安装在 Codex 和 Claude Code 根目录的 MinerU 技能。

## 目录结构

```text
skills/          # cc-switch、Codex、Claude 可安装的技能
suites/          # 技能套件级 manifest
scripts/         # 验证和导出辅助脚本
dist/            # 生成的兼容导出目录，不手动编辑
```

## 更新模型

本仓库是唯一维护源。cc-switch 从 GitHub 拉取本仓库后，将技能保存到 `~/.cc-switch/skills`，再通过 symlink 暴露给 `~/.codex/skills` 和 `~/.claude/skills`。

## 新增技能

新增技能时，在 `skills/<skill-name>/` 下创建独立目录。除非明确是在升级某个既有 suite，否则不要修改已有 suite；这样后续添加技能只会增加能力，不会改变已经安装技能的行为边界。
