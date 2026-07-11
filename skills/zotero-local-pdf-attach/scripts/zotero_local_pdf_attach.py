#!/usr/bin/env python3
"""为本地 Zotero Desktop 生成可恢复的 PDF 托管附件导入任务。"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import sys
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
import zipfile
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


DEFAULT_API = "http://127.0.0.1:23119/api/users/0"
PAGE_SIZE = 100
SUCCESS = {"attached", "skipped_same_hash"}
NS = {"x": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists() or not path.read_text(encoding="utf-8").strip():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def append_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> None:
    rows = list(rows)
    if not rows:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def norm_title(value: Any) -> str:
    return re.sub(r"\W+", "", str(value or "").casefold())


def norm_doi(value: Any) -> str:
    value = str(value or "").strip().lower()
    value = re.sub(r"^https?://(?:dx\.)?doi\.org/", "", value)
    return value.removeprefix("doi:").strip()


def record_id_from_extra(item: dict[str, Any]) -> str:
    extra = str(item.get("data", item).get("extra", ""))
    match = re.search(r"(?:FieldLiteratureSurvey\s+)?record_id:\s*([^\s;]+)", extra, flags=re.I)
    return match.group(1) if match else ""


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def xlsx_rows(path: Path) -> list[dict[str, str]]:
    with zipfile.ZipFile(path) as archive:
        shared: list[str] = []
        if "xl/sharedStrings.xml" in archive.namelist():
            root = ET.fromstring(archive.read("xl/sharedStrings.xml"))
            shared = ["".join(node.itertext()) for node in root.findall("x:si", NS)]
        sheets = [name for name in archive.namelist() if re.fullmatch(r"xl/worksheets/sheet\d+\.xml", name)]
        if not sheets:
            raise ValueError("XLSX 中未找到工作表")
        root = ET.fromstring(archive.read(sorted(sheets)[0]))
        rows: list[list[str]] = []
        for row in root.findall(".//x:sheetData/x:row", NS):
            values: dict[int, str] = {}
            for cell in row.findall("x:c", NS):
                ref = cell.get("r", "A1")
                letters = re.match(r"[A-Z]+", ref).group(0)
                column = 0
                for char in letters:
                    column = column * 26 + ord(char) - 64
                raw = cell.findtext("x:v", default="", namespaces=NS)
                if cell.get("t") == "s" and raw:
                    raw = shared[int(raw)]
                elif cell.get("t") == "inlineStr":
                    raw = "".join(cell.itertext())
                values[column] = raw
            if values:
                rows.append([values.get(i, "") for i in range(1, max(values) + 1)])
    if not rows:
        return []
    headers = [value.strip() for value in rows[0]]
    return [dict(zip(headers, values)) for values in rows[1:] if any(values)]


def tracking_rows(path: Path) -> list[dict[str, Any]]:
    suffix = path.suffix.lower()
    if suffix == ".json":
        source = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(source, dict):
            rows = []
            for key, value in source.items():
                row = dict(value) if isinstance(value, dict) else {"value": value}
                row.setdefault("record_id", key)
                rows.append(row)
            return rows
        if isinstance(source, list):
            return [dict(row) for row in source if isinstance(row, dict)]
        raise ValueError("JSON 跟踪表必须是对象或数组")
    if suffix == ".csv":
        with path.open(encoding="utf-8-sig", newline="") as handle:
            return [dict(row) for row in csv.DictReader(handle)]
    if suffix == ".xlsx":
        return xlsx_rows(path)
    raise ValueError("仅支持 JSON、CSV、XLSX 跟踪表")


def get_value(row: dict[str, Any], *names: str) -> str:
    lookup = {str(key).strip().casefold(): value for key, value in row.items()}
    for name in names:
        value = lookup.get(name.casefold())
        if value is not None and str(value).strip():
            return str(value).strip()
    return ""


def api_get(base: str, path: str) -> tuple[dict[str, str], Any]:
    request = urllib.request.Request(base.rstrip("/") + path, headers={"Zotero-API-Version": "3"})
    with urllib.request.urlopen(request, timeout=45) as response:
        body = response.read().decode("utf-8", errors="replace")
        try:
            value: Any = json.loads(body)
        except json.JSONDecodeError:
            value = body
        return dict(response.headers.items()), value


def paged_get(base: str, path: str) -> list[dict[str, Any]]:
    separator = "&" if "?" in path else "?"
    headers, rows = api_get(base, f"{path}{separator}limit={PAGE_SIZE}&start=0")
    if not isinstance(rows, list):
        raise RuntimeError(f"本地 Zotero 返回非列表：{path}")
    total = int(headers.get("Total-Results", len(rows)))
    for start in range(PAGE_SIZE, total, PAGE_SIZE):
        _, page = api_get(base, f"{path}{separator}limit={PAGE_SIZE}&start={start}")
        rows.extend(page)
    return rows


def latest_results(path: Path) -> dict[str, dict[str, Any]]:
    latest: dict[str, dict[str, Any]] = {}
    for row in read_jsonl(path):
        if row.get("record_id"):
            latest[str(row["record_id"])] = row
    return latest


def command_prepare(args: argparse.Namespace) -> int:
    tracking = tracking_rows(Path(args.tracking))
    pdf_root = Path(args.pdf_root).expanduser().resolve()
    out = Path(args.out).expanduser().resolve()
    manifest_path = out / "pdf_manifest.jsonl"
    manual_path = out / "manual_review.jsonl"
    if manifest_path.exists() and not args.force:
        raise RuntimeError(f"清单已存在：{manifest_path}；如确认重新生成，请传入 --force")

    parents = paged_get(args.local_api, "/items/top")
    attachments = paged_get(args.local_api, "/items?itemType=attachment")
    by_key = {str(item.get("key", "")): item for item in parents}
    by_record: dict[str, list[dict[str, Any]]] = defaultdict(list)
    by_doi: dict[str, list[dict[str, Any]]] = defaultdict(list)
    by_title: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for item in parents:
        data = item.get("data", item)
        if record_id_from_extra(item):
            by_record[record_id_from_extra(item)].append(item)
        if norm_doi(data.get("DOI")):
            by_doi[norm_doi(data.get("DOI"))].append(item)
        if norm_title(data.get("title")):
            by_title[norm_title(data.get("title"))].append(item)
    attachment_counts = Counter(str(item.get("data", item).get("parentItem", "")) for item in attachments)

    manifest: list[dict[str, Any]] = []
    manual: list[dict[str, Any]] = []
    for raw in tracking:
        status = get_value(raw, "pdf_status")
        if status and status.casefold() != "downloaded":
            continue
        if args.limit is not None and len(manifest) >= args.limit:
            break
        record_id = get_value(raw, "record_id", "id")
        title = get_value(raw, "title", "标题")
        doi = norm_doi(get_value(raw, "doi"))
        pdf_value = get_value(raw, "pdf_path", "path", "pdf")
        pdf_path = Path(pdf_value).expanduser() if pdf_value else Path()
        if not pdf_path.is_absolute():
            pdf_path = pdf_root / pdf_path
        result: dict[str, Any] = {
            "record_id": record_id,
            "title": title,
            "doi": doi,
            "source_pdf": str(pdf_path.resolve()),
            "source_size_bytes": pdf_path.stat().st_size if pdf_path.is_file() else 0,
            "source_sha256": sha256(pdf_path) if pdf_path.is_file() else "",
            "prepared_at": now(),
            "status": "",
        }
        requested_key = get_value(raw, "zotero_item_key", "zotero_key")
        candidates: list[dict[str, Any]] = []
        method = ""
        if not record_id or not title:
            result.update(status="manual_review", reason="record_id_or_title_missing")
        elif not pdf_path.is_file():
            result.update(status="manual_review", reason="tracked_pdf_file_missing")
        else:
            if requested_key:
                method, candidates = "zotero_item_key", [by_key[requested_key]] if requested_key in by_key else []
            elif by_record.get(record_id):
                method, candidates = "record_id", by_record[record_id]
            elif doi and by_doi.get(doi):
                method, candidates = "doi", by_doi[doi]
            else:
                method, candidates = "title", by_title.get(norm_title(title), [])
            if len(candidates) == 1:
                parent_key = str(candidates[0].get("key", ""))
                result.update(status="pending_attach", match_method=method, parent_item_key=parent_key,
                              existing_attachment_count=attachment_counts[parent_key])
            else:
                result.update(status="manual_review", reason="parent_not_found" if not candidates else "parent_not_unique",
                              match_method=method, candidate_parent_keys=[str(item.get("key", "")) for item in candidates])
        manifest.append(result)
        if result["status"] == "manual_review":
            manual.append(result)
    out.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text("".join(json.dumps(row, ensure_ascii=False) + "\n" for row in manifest), encoding="utf-8")
    manual_path.write_text("".join(json.dumps(row, ensure_ascii=False) + "\n" for row in manual), encoding="utf-8")
    summary = {"tracking_rows": len(tracking), "selected_rows": len(manifest), "manifest_rows": len(manifest), "manual_review": len(manual),
               "pending_attach": sum(row["status"] == "pending_attach" for row in manifest), "out": str(out)}
    write_json(out / "prepare_summary.json", summary)
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


def command_plan(args: argparse.Namespace) -> int:
    manifest = read_jsonl(Path(args.manifest))
    latest = latest_results(Path(args.results))
    max_files, max_bytes = args.max_files, args.max_mib * 1024 * 1024
    candidates = []
    for row in manifest:
        prior = latest.get(str(row.get("record_id", "")))
        if row.get("status") == "pending_attach" and not (prior and prior.get("status") in SUCCESS):
            candidates.append(row)
    batches: list[dict[str, Any]] = []
    current: list[dict[str, Any]] = []
    current_bytes = 0
    for row in candidates:
        size = int(row.get("source_size_bytes", 0))
        if current and (len(current) >= max_files or current_bytes + size > max_bytes):
            batches.append({"batch_id": f"batch-{len(batches) + 1:04d}", "records": current, "file_count": len(current), "size_bytes": current_bytes})
            current, current_bytes = [], 0
        current.append(row)
        current_bytes += size
    if current:
        batches.append({"batch_id": f"batch-{len(batches) + 1:04d}", "records": current, "file_count": len(current), "size_bytes": current_bytes})
    out = Path(args.out).expanduser().resolve()
    payload = {"created_at": now(), "max_files": max_files, "max_mib": args.max_mib, "cooldown_seconds": args.cooldown_seconds,
               "candidate_count": len(candidates), "batches": batches}
    write_json(out / "batches.json", payload)
    print(json.dumps({key: payload[key] for key in ("candidate_count", "max_files", "max_mib", "cooldown_seconds")} | {"batch_count": len(batches)}, ensure_ascii=False, indent=2))
    return 0


def console_script(records: list[dict[str, Any]], results_path: Path, batch_id: str) -> str:
    rows = json.dumps(records, ensure_ascii=False, indent=2)
    results = json.dumps(str(results_path.resolve()), ensure_ascii=False)
    bid = json.dumps(batch_id, ensure_ascii=False)
    return f'''// 由 zotero-local-pdf-attach 生成。仅导入 {batch_id}；请勿在不确认清单的情况下运行。
(async () => {{
const batchID = {bid};
const resultPath = {results};
const rows = {rows};

const resultFile = Zotero.File.pathToFile(resultPath);
const libraryID = Zotero.Libraries.userLibraryID;
let previous = [];
try {{
  previous = (await Zotero.File.getContentsAsync(resultFile)).trim().split('\\n').filter(Boolean).map(JSON.parse);
}}
catch (_) {{}}
const priorByRecord = new Map(previous.map(row => [row.record_id, row]));
const outcomes = [];
for (const row of rows) {{
  const prior = priorByRecord.get(row.record_id);
  if (prior && ['attached', 'skipped_same_hash'].includes(prior.status)) {{
    if (prior.parent_item_key === row.parent_item_key && prior.source_sha256 === row.source_sha256) {{
      outcomes.push({{ ...prior, status: 'skipped_same_hash', reason: 'checkpoint_success', batch_id: batchID, checked_at: new Date().toISOString() }});
    }}
    else {{
      outcomes.push({{ ...prior, status: 'review_checkpoint_mismatch', reason: 'checkpoint_parent_or_hash_mismatch', batch_id: batchID, checked_at: new Date().toISOString() }});
    }}
    continue;
  }}
  const result = {{ record_id: row.record_id, parent_item_key: row.parent_item_key, source_pdf: row.source_pdf,
    source_sha256: row.source_sha256, batch_id: batchID, imported_at: new Date().toISOString() }};
  try {{
    const parent = Zotero.Items.getByLibraryAndKey(libraryID, row.parent_item_key);
    if (!parent) throw new Error('parent_item_not_found');
    const source = Zotero.File.pathToFile(row.source_pdf);
    if (!source.exists()) throw new Error('source_pdf_not_found');
    const sourceMD5 = await Zotero.File.md5Async(source);
    let sameFileAttachment = null;
    let existingPDFCount = 0;
    for (const childID of parent.getAttachments()) {{
      const child = Zotero.Items.get(childID);
      if (!child || child.attachmentContentType !== 'application/pdf') continue;
      existingPDFCount += 1;
      const childPath = await child.getFilePathAsync();
      if (!childPath) continue;
      const childFile = Zotero.File.pathToFile(childPath);
      if (childFile.exists() && (await Zotero.File.md5Async(childFile)) === sourceMD5) {{
        sameFileAttachment = child;
        break;
      }}
    }}
    if (sameFileAttachment) {{
      result.status = 'skipped_same_hash';
      result.reason = 'existing_parent_pdf_same_content';
      result.attachment_key = sameFileAttachment.key;
      result.link_mode = sameFileAttachment.attachmentLinkMode;
      outcomes.push(result);
      continue;
    }}
    if (existingPDFCount > 0) {{
      result.status = 'review_existing_different_pdf';
      result.reason = 'existing_parent_pdf_different_content';
      result.existing_pdf_count = existingPDFCount;
      outcomes.push(result);
      continue;
    }}
    const attachment = await Zotero.Attachments.importFromFile({{ file: source, parentItemID: parent.id }});
    result.status = 'attached';
    result.attachment_key = attachment.key;
    result.link_mode = attachment.attachmentLinkMode;
    if (result.link_mode !== 0) throw new Error(`unexpected_link_mode:${{result.link_mode}}`);
  }}
  catch (error) {{
    result.status = 'error';
    result.error = String(error);
  }}
  outcomes.push(result);
}}
const lines = previous.concat(outcomes).map(row => JSON.stringify(row)).join('\\n') + '\\n';
await Zotero.File.putContentsAsync(resultFile, lines);
return {{ batch_id: batchID, processed: outcomes.length,
  attached: outcomes.filter(row => row.status === 'attached').length,
  skipped: outcomes.filter(row => row.status === 'skipped_same_hash').length,
  errors: outcomes.filter(row => row.status === 'error').length, results: resultPath }};
}})();
'''


def console_audit_script(records: list[dict[str, Any]], audit_path: Path, batch_id: str) -> str:
    rows = json.dumps(records, ensure_ascii=False, indent=2)
    audit = json.dumps(str(audit_path.resolve()), ensure_ascii=False)
    bid = json.dumps(batch_id, ensure_ascii=False)
    return f'''// 由 zotero-local-pdf-attach 生成。仅核验 {batch_id}；不导入或删除附件。
(async () => {{
const batchID = {bid};
const auditPath = {audit};
const rows = {rows};
const auditFile = Zotero.File.pathToFile(auditPath);
const libraryID = Zotero.Libraries.userLibraryID;

function sha256File(file) {{
  const crypto = Components.classes['@mozilla.org/security/hash;1']
    .createInstance(Components.interfaces.nsICryptoHash);
  crypto.init(crypto.SHA256);
  const stream = Components.classes['@mozilla.org/network/file-input-stream;1']
    .createInstance(Components.interfaces.nsIFileInputStream);
  stream.init(file, 0x01, 0o400, 0);
  try {{
    crypto.updateFromStream(stream, file.fileSize);
  }} finally {{
    stream.close();
  }}
  return Array.from(crypto.finish(false), char => char.charCodeAt(0).toString(16).padStart(2, '0')).join('');
}}

let previous = [];
try {{
  previous = (await Zotero.File.getContentsAsync(auditFile)).trim().split('\\n').filter(Boolean).map(JSON.parse);
}} catch (_) {{}}
const outcomes = [];
for (const row of rows) {{
  const result = {{ ...row, audit_batch_id: batchID, audited_at: new Date().toISOString(), status: '' }};
  try {{
    const attachment = Zotero.Items.getByLibraryAndKey(libraryID, row.attachment_key);
    if (!attachment) throw new Error('attachment_not_found');
    result.observed_parent_item_key = attachment.parentKey;
    result.observed_link_mode = attachment.attachmentLinkMode;
    const filePath = await attachment.getFilePathAsync();
    if (!filePath) throw new Error('stored_file_path_not_available');
    const file = Zotero.File.pathToFile(filePath);
    if (!file.exists()) throw new Error('stored_file_missing');
    result.stored_file_exists = true;
    result.observed_sha256 = sha256File(file);
    result.sha256_matches_source = result.observed_sha256 === row.source_sha256;
    result.status = result.observed_parent_item_key === row.parent_item_key
      && result.observed_link_mode === 0 && result.sha256_matches_source ? 'verified' : 'mismatch';
    if (result.status === 'mismatch') {{
      result.reason = result.observed_parent_item_key !== row.parent_item_key ? 'parent_item_mismatch'
        : result.observed_link_mode !== 0 ? 'not_imported_file' : 'stored_file_sha256_mismatch';
    }}
  }} catch (error) {{
    result.status = 'audit_error';
    result.reason = String(error);
  }}
  outcomes.push(result);
}}
await Zotero.File.putContentsAsync(auditFile, previous.concat(outcomes).map(row => JSON.stringify(row)).join('\\n') + '\\n');
return {{ batch_id: batchID, processed: outcomes.length,
  verified: outcomes.filter(row => row.status === 'verified').length,
  mismatches: outcomes.filter(row => row.status === 'mismatch').length,
  errors: outcomes.filter(row => row.status === 'audit_error').length, audit: auditPath }};
}})();
'''


def command_render(args: argparse.Namespace) -> int:
    batches = json.loads(Path(args.batches).read_text(encoding="utf-8"))
    batch = next((value for value in batches.get("batches", []) if value.get("batch_id") == args.batch_id), None)
    if not batch:
        raise RuntimeError(f"未找到批次：{args.batch_id}")
    out = Path(args.out).expanduser().resolve()
    out.mkdir(parents=True, exist_ok=True)
    script_path = out / f"console_{args.batch_id}.js"
    script_path.write_text(console_script(batch["records"], Path(args.results), args.batch_id), encoding="utf-8")
    print(json.dumps({"batch_id": args.batch_id, "file_count": batch["file_count"], "size_bytes": batch["size_bytes"], "script": str(script_path)}, ensure_ascii=False, indent=2))
    return 0


def command_render_audit(args: argparse.Namespace) -> int:
    manifest = {str(row.get("record_id")): row for row in read_jsonl(Path(args.manifest))}
    latest = latest_results(Path(args.results))
    audited = latest_results(Path(args.audit))
    candidates: list[dict[str, Any]] = []
    for record_id, source in manifest.items():
        result = latest.get(record_id, {})
        prior_audit = audited.get(record_id, {})
        if result.get("status") not in SUCCESS or not result.get("attachment_key"):
            continue
        if prior_audit.get("status") == "verified":
            continue
        candidates.append({"record_id": record_id, "parent_item_key": result.get("parent_item_key"),
                           "attachment_key": result.get("attachment_key"), "source_sha256": source.get("source_sha256", result.get("source_sha256", "")),
                           "source_size_bytes": int(source.get("source_size_bytes", 0))})
    batch: list[dict[str, Any]] = []
    batch_bytes = 0
    for row in candidates[args.offset:]:
        size = int(row.get("source_size_bytes", 0))
        if batch and (len(batch) >= args.limit or batch_bytes + size > args.max_mib * 1024 * 1024):
            break
        batch.append(row)
        batch_bytes += size
    if not batch:
        raise RuntimeError("没有待 Console 核验的附件")
    out = Path(args.out).expanduser().resolve()
    out.mkdir(parents=True, exist_ok=True)
    batch_id = f"audit-{args.offset // args.limit + 1:04d}"
    script_path = out / f"console_{batch_id}.js"
    script_path.write_text(console_audit_script(batch, Path(args.audit), batch_id), encoding="utf-8")
    print(json.dumps({"batch_id": batch_id, "file_count": len(batch), "size_bytes": batch_bytes, "remaining_after_batch": len(candidates) - args.offset - len(batch), "script": str(script_path)}, ensure_ascii=False, indent=2))
    return 0


def command_audit(args: argparse.Namespace) -> int:
    manifest = {str(row.get("record_id")): row for row in read_jsonl(Path(args.manifest))}
    latest = latest_results(Path(args.results))
    audit: list[dict[str, Any]] = []
    for index, (record_id, source) in enumerate(manifest.items()):
        if args.limit is not None and index >= args.limit:
            break
        result = latest.get(record_id, {})
        item: dict[str, Any] = {"record_id": record_id, "result_status": result.get("status"), "parent_item_key": result.get("parent_item_key"),
                                "attachment_key": result.get("attachment_key"), "source_sha256": source.get("source_sha256", result.get("source_sha256", "")), "status": ""}
        if source.get("status") != "pending_attach":
            item.update(status="manual_review", reason=source.get("reason", ""))
        elif not result:
            item.update(status="not_imported", reason="no_import_result")
        elif result.get("status") not in SUCCESS:
            item.update(status="not_successful", reason=result.get("error", ""))
        elif not result.get("attachment_key"):
            item.update(status="checkpoint_only", reason="需在 Zotero 中复核已存在附件")
        else:
            try:
                _, attachment = api_get(args.local_api, f"/items/{urllib.parse.quote(str(result['attachment_key']))}")
                data = attachment.get("data", attachment)
                parent_ok = str(data.get("parentItem", "")) == str(result.get("parent_item_key", ""))
                mode_ok = int(data.get("linkMode", -1)) == 0
                item.update(observed_parent_item_key=data.get("parentItem"), observed_link_mode=data.get("linkMode"))
                _, file_url = api_get(args.local_api, f"/items/{urllib.parse.quote(str(result['attachment_key']))}/file/view/url")
                parsed = urllib.parse.urlparse(str(file_url))
                stored_file = Path(urllib.parse.unquote(parsed.path)) if parsed.scheme == "file" else Path()
                exists = stored_file.is_file()
                item.update(stored_file=str(stored_file), stored_file_exists=exists)
                hash_ok = False
                if exists:
                    observed_sha256 = sha256(stored_file)
                    hash_ok = observed_sha256 == item["source_sha256"]
                    item.update(observed_sha256=observed_sha256, sha256_matches_source=hash_ok)
                item["status"] = "verified" if parent_ok and mode_ok and exists and hash_ok else "mismatch"
                if not parent_ok:
                    item["reason"] = "parent_item_mismatch"
                elif not mode_ok:
                    item["reason"] = "not_imported_file"
                elif not exists:
                    item["reason"] = "stored_file_missing"
                elif not hash_ok:
                    item["reason"] = "stored_file_sha256_mismatch"
            except Exception as error:
                item.update(status="local_api_unavailable", reason=str(error))
        audit.append(item)
    out = Path(args.out).expanduser().resolve()
    out.mkdir(parents=True, exist_ok=True)
    path = out / "attachment_audit.jsonl"
    path.write_text("".join(json.dumps(row, ensure_ascii=False) + "\n" for row in audit), encoding="utf-8")
    summary = {"records": len(audit), "status_counts": dict(Counter(row["status"] for row in audit)), "audit": str(path)}
    write_json(out / "audit_summary.json", summary)
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


def command_report(args: argparse.Namespace) -> int:
    audit = read_jsonl(Path(args.audit))
    out = Path(args.out).expanduser().resolve()
    counts = Counter(row.get("status", "unknown") for row in audit)
    summary = {"generated_at": now(), "records": len(audit), "status_counts": dict(counts)}
    lines = ["# Zotero 本地 PDF 附加报告", "", f"- 审计记录：{len(audit)}"]
    labels = {"verified": "已核验", "mismatch": "父条目、存储模式或文件哈希异常", "local_api_unavailable": "本地 API 无法读取附件，需 Console 核验", "audit_error": "Console 核验失败", "not_successful": "导入失败", "not_imported": "尚未导入", "manual_review": "准备阶段待人工复核", "checkpoint_only": "仅检查点跳过，需复核"}
    for key, value in sorted(counts.items()):
        lines.append(f"- {labels.get(key, key)}：{value}")
    out.mkdir(parents=True, exist_ok=True)
    (out / "import_report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    write_json(out / "import_summary.json", summary)
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(description=__doc__)
    commands = root.add_subparsers(dest="command", required=True)
    common_api = argparse.ArgumentParser(add_help=False)
    common_api.add_argument("--local-api", default=DEFAULT_API, help="本地 Zotero API 根地址")
    prepare = commands.add_parser("prepare", parents=[common_api], help="构建清单并匹配 Zotero 父条目")
    prepare.add_argument("--tracking", required=True)
    prepare.add_argument("--pdf-root", required=True)
    prepare.add_argument("--out", required=True)
    prepare.add_argument("--limit", type=int, help="仅准备前 N 条，用于连通性测试；省略时处理全部已下载记录")
    prepare.add_argument("--force", action="store_true")
    prepare.set_defaults(func=command_prepare)
    plan = commands.add_parser("plan", help="将未完成记录拆分为受限批次")
    plan.add_argument("--manifest", required=True)
    plan.add_argument("--results", required=True)
    plan.add_argument("--out", required=True)
    plan.add_argument("--max-files", type=int, default=20)
    plan.add_argument("--max-mib", type=int, default=512)
    plan.add_argument("--cooldown-seconds", type=int, default=45)
    plan.set_defaults(func=command_plan)
    render = commands.add_parser("render-console-script", help="生成单批 Zotero Developer Console 脚本")
    render.add_argument("--manifest", required=True, help="保留以明确任务输入；脚本使用 batches 中冻结的记录")
    render.add_argument("--batches", required=True)
    render.add_argument("--results", required=True)
    render.add_argument("--batch-id", required=True)
    render.add_argument("--out", required=True)
    render.set_defaults(func=command_render)
    render_audit = commands.add_parser("render-audit-console-script", help="生成单批 Zotero Developer Console 核验脚本")
    render_audit.add_argument("--manifest", required=True)
    render_audit.add_argument("--results", required=True)
    render_audit.add_argument("--audit", required=True)
    render_audit.add_argument("--out", required=True)
    render_audit.add_argument("--limit", type=int, default=20, help="每批最多核验的附件数，默认 20")
    render_audit.add_argument("--max-mib", type=int, default=512, help="每批最多核验的源文件总大小，默认 512 MiB")
    render_audit.add_argument("--offset", type=int, default=0, help="待核验队列中的起始偏移，默认 0")
    render_audit.set_defaults(func=command_render_audit)
    audit = commands.add_parser("audit", parents=[common_api], help="全量核验已导入附件的父条目和托管模式")
    audit.add_argument("--manifest", required=True)
    audit.add_argument("--results", required=True)
    audit.add_argument("--out", required=True)
    audit.add_argument("--limit", type=int, help="仅核验前 N 条，用于连通性测试；省略时全量核验")
    audit.set_defaults(func=command_audit)
    report = commands.add_parser("report", help="生成中文汇总报告")
    report.add_argument("--audit", required=True)
    report.add_argument("--out", required=True)
    report.set_defaults(func=command_report)
    return root


def main() -> int:
    args = parser().parse_args()
    try:
        return args.func(args)
    except Exception as error:
        print(f"错误：{error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
