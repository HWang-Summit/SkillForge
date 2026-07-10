---
name: zotero-web-api
description: Write Zotero cloud library data through the official Zotero Web API. Use when adding paper metadata, abstracts, tags, or collections to Zotero without opening Zotero Desktop; resolving or creating Zotero collection paths; batch importing DOI/title metadata into a Zotero collection; or verifying Zotero Web API read/write access from Codex or Claude Code.
---

# Zotero Web API

Use this skill to write Zotero library data through `https://api.zotero.org`. It is designed for both Codex and Claude Code: all operations use a stdlib-only Python CLI and do not depend on Zotero Desktop, local Zotero APIs, MCP servers, or plugins.

Core helper:

```bash
bash skills/zotero-web-api/scripts/run_zotero_web.sh <command>
```

The launcher loads `${SKILLFORGE_ENV_FILE:-$HOME/.skillforge/env}` before running the stdlib-only Python helper. Store `ZOTERO_API_KEY` there or export it in the current environment. Use `ZOTERO_PYTHON` only when a specific Python executable is required.

## Safety Rules

- Never print, log, save, or commit the API key.
- Do not edit `zotero.sqlite` or Zotero storage files.
- Do not require Zotero Desktop to be open.
- Treat all Zotero writes as explicit write actions. Use dry-run first unless the user has clearly asked to add, import, create, or write.
- All helper write commands are dry-run by default and require `--yes` for live writes.
- Do not upload PDFs or attachments with this skill. This version handles metadata, abstracts, tags, and collections only.

## Quick Starts

Check key and write access:

```bash
bash skills/zotero-web-api/scripts/run_zotero_web.sh status --json
```

List collection paths:

```bash
bash skills/zotero-web-api/scripts/run_zotero_web.sh collections --json
```

Resolve an existing collection:

```bash
bash skills/zotero-web-api/scripts/run_zotero_web.sh resolve-collection --path "Papers/To Read" --json
```

Create a collection path if missing:

```bash
bash skills/zotero-web-api/scripts/run_zotero_web.sh ensure-collection --path "Papers/To Read" --yes --json
```

Dry-run import a paper:

```bash
bash skills/zotero-web-api/scripts/run_zotero_web.sh upsert-item \
  --metadata paper.json \
  --collection "Papers/To Read" \
  --create-collection \
  --json
```

Live import after reviewing the dry-run:

```bash
bash skills/zotero-web-api/scripts/run_zotero_web.sh upsert-item \
  --metadata paper.json \
  --collection "Papers/To Read" \
  --create-collection \
  --yes \
  --json
```

Batch import:

```bash
bash skills/zotero-web-api/scripts/run_zotero_web.sh import-batch \
  --metadata papers.json \
  --default-collection "Papers/To Read" \
  --create-collection \
  --yes \
  --json
```

## Workflow

1. Run `status --json` first. Confirm the key has `write: true` for the target library.
2. Determine the target collection:
   - Single item: use `--collection` or the metadata field `collection`.
   - Batch: prefer each record's `collection`; otherwise use `--default-collection`.
   - If no collection is given, stop and ask unless the user explicitly wants root-library insertion.
3. Resolve or create the collection:
   - Use `resolve-collection` when writing to an existing collection.
   - Use `ensure-collection --yes` only when the user allows creating missing collections.
4. Check duplicates with DOI first, then normalized title.
5. Dry-run the write and report: target library, collection paths, records to create, existing records to update with the target collection, skipped records, and errors.
6. If the user already explicitly asked to add/import/write, run the command with `--yes`; otherwise wait for confirmation after dry-run.
7. Report Zotero item keys, titles, DOI values, collection paths, and created/updated/skipped status.

## Metadata Contract

Single-item metadata is a JSON object:

```json
{
  "itemType": "conferencePaper",
  "title": "Closer to Biological Mechanism: Drug-Drug Interaction Prediction from the Perspective of Pharmacophore",
  "creators": [
    {"creatorType": "author", "firstName": "Mingliang", "lastName": "Dou"}
  ],
  "abstractNote": "...",
  "date": "2026",
  "DOI": "10.1609/aaai.v40i25.39229",
  "url": "https://doi.org/10.1609/aaai.v40i25.39229",
  "proceedingsTitle": "Proceedings of the AAAI Conference on Artificial Intelligence",
  "tags": ["DDI prediction", "pharmacophore"],
  "collection": "Optional/Per-record Collection Path"
}
```

Batch metadata is a JSON array of these objects. The helper converts string tags into Zotero tag objects and injects `collections` from the resolved collection path. If `itemType` is missing, the helper defaults to `journalArticle`; provide a specific type when it is known.

## Commands

```bash
bash skills/zotero-web-api/scripts/run_zotero_web.sh status --json
bash skills/zotero-web-api/scripts/run_zotero_web.sh collections --json
bash skills/zotero-web-api/scripts/run_zotero_web.sh resolve-collection --path "<collection/path>" --json
bash skills/zotero-web-api/scripts/run_zotero_web.sh ensure-collection --path "<collection/path>" --yes --json
bash skills/zotero-web-api/scripts/run_zotero_web.sh delete-collection --path "<temporary/test/path>" --yes --json
bash skills/zotero-web-api/scripts/run_zotero_web.sh find --doi "<doi>" --json
bash skills/zotero-web-api/scripts/run_zotero_web.sh find --title "<title>" --json
bash skills/zotero-web-api/scripts/run_zotero_web.sh upsert-item --metadata paper.json --collection "<collection/path>" --yes --json
bash skills/zotero-web-api/scripts/run_zotero_web.sh import-batch --metadata papers.json --default-collection "<collection/path>" --create-collection --yes --json
```

## Library Selection

By default the helper writes to the API key user's personal library. For group libraries, pass:

```bash
--library group:<groupID>
```

Personal libraries can be explicit:

```bash
--library user:<userID>
```

## References

Read `references/web-api-routes.md` when endpoint details, write semantics, or error handling need to be checked.
