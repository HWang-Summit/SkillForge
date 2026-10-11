# Source-area navigation

Keep the provenance layer parallel to Domain → Topic knowledge navigation:
source type → storage namespace / legacy class → raw Markdown → summary.
It is a derived catalog, never the source of truth for provenance or ingestion.

## Selection and naming

- Top entry points: `papers`, `articles`, `books`, `notes`. Empty Articles/Books
  show no sources, not invented ingest records. Do not create asset entry points.
- Use actual frozen semantic Bundle namespace and project namespace registry;
  existing semantic raw subdirectories remain readable. Never infer namespace
  from scientific Topic or current Zotero collection.
- Legacy `raw/papers/pdf-<hash>/` is grouped under `legacy-paper-bundles`;
  older root/collection paths under `legacy-paper-sources`. Do not create a
  source-area page per hash folder or silently migrate legacy material.
- Only raw source Markdown files are catalogued; exclude every hidden/workflow
  directory, `_inbox`, MinerU asset directories, symlinks and attachments.
  A link to `paper.mineru.md` within a legacy hash folder is valid.

## Fields and links

- `type: meta`, `meta_kind: source-area`; `source_layer` is the source type.
  A namespace leaf has `source_namespace`; general entry pages may omit it.
- Pair raw Markdown and summary in each record using the summary's `sources`
  and existing source-index/manifest evidence. Preserve historical duplicate
  sources pointing to one reused summary; do not deduplicate or replace raw.
- Show Bridge state and wiki coverage separately. `content_mismatch`, pending,
  parsed or linked files may be listed, but do not imply successful wiki ingest.
  Unmapped raw files say "No indexed summary". Report inconsistent old records.
- No scientific claims; `sources: []` remains empty because this is navigation.
  Update index and append log for page changes; do not mutate provenance facts.

## Maintenance and views

- After each successful user-selected ingest, update that source's record in
  the existing source area, including raw link, summary link, and recorded state.
  Refresh parent links/counts where present. Create a new namespace leaf only
  when a real new stable namespace appears.
  Skip unchanged ingest unless explicitly asked; no background watching or
  whole-library scan/write is implied.
- Main Graph excludes `wiki/source-areas`; source areas use teal `#0F766E` for
  local provenance views. Global raw inclusion and attachment nodes stay off.
- `source-provenance.canvas` is a small representative view; update only on
  explicit request. Validate node IDs, edges, file existence and mappings.
