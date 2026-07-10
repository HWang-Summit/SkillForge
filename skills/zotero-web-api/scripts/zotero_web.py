#!/usr/bin/env python3
"""Operate Zotero through the official Web API.

This helper is stdlib-only so it can be used by Codex, Claude Code, and plain
shell sessions without plugin dependencies.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from typing import Any

BASE_URL = "https://api.zotero.org"
API_VERSION = "3"
PAGE_LIMIT = 100


class ZoteroError(RuntimeError):
    pass


@dataclass(frozen=True)
class Response:
    status: int
    headers: dict[str, str]
    text: str


@dataclass(frozen=True)
class Library:
    kind: str
    identifier: str

    @property
    def path(self) -> str:
        return f"/{self.kind}s/{self.identifier}"

    @property
    def label(self) -> str:
        return f"{self.kind}:{self.identifier}"


def dump_json(value: Any) -> None:
    print(json.dumps(value, indent=2, ensure_ascii=False))


def api_key() -> str:
    key = os.environ.get("ZOTERO_API_KEY", "").strip()
    if not key:
        raise ZoteroError(
            "ZOTERO_API_KEY is not set. Add it to $HOME/.skillforge/env "
            "or export it in the current environment."
        )
    return key


def request(
    path: str,
    *,
    method: str = "GET",
    data: Any = None,
    extra_headers: dict[str, str] | None = None,
) -> Response:
    headers = {
        "Zotero-API-Key": api_key(),
        "Zotero-API-Version": API_VERSION,
    }
    if extra_headers:
        headers.update(extra_headers)

    body: bytes | None = None
    if data is not None:
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        headers.setdefault("Content-Type", "application/json")

    req = urllib.request.Request(BASE_URL + path, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return Response(
                status=resp.status,
                headers=dict(resp.headers.items()),
                text=resp.read().decode("utf-8", errors="replace"),
            )
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise ZoteroError(f"{method} {path} failed: status={exc.code} detail={detail}") from exc
    except urllib.error.URLError as exc:
        raise ZoteroError(f"{method} {path} failed: {exc.reason}") from exc


def parse_json_response(response: Response) -> Any:
    if not response.text:
        return None
    try:
        return json.loads(response.text)
    except json.JSONDecodeError as exc:
        raise ZoteroError(f"Expected JSON response, got: {response.text[:200]}") from exc


def query(params: dict[str, str | int | None]) -> str:
    return urllib.parse.urlencode({k: v for k, v in params.items() if v is not None})


def paged_get(path: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    start = 0
    while True:
        sep = "&" if "?" in path else "?"
        response = request(f"{path}{sep}{query({'limit': PAGE_LIMIT, 'start': start})}")
        page = parse_json_response(response)
        if not isinstance(page, list):
            raise ZoteroError(f"Expected list response from {path}")
        rows.extend(page)
        total_raw = response.headers.get("Total-Results")
        total = int(total_raw) if total_raw and total_raw.isdigit() else None
        start += PAGE_LIMIT
        if total is not None and start >= total:
            break
        if len(page) < PAGE_LIMIT:
            break
    return rows


def key_status() -> dict[str, Any]:
    data = parse_json_response(request("/keys/current"))
    if not isinstance(data, dict):
        raise ZoteroError("Unexpected /keys/current response")
    data.pop("key", None)
    return data


def default_library() -> Library:
    status = key_status()
    user_id = status.get("userID")
    if user_id is None:
        raise ZoteroError("Could not determine userID from /keys/current")
    return Library("user", str(user_id))


def parse_library(raw: str | None) -> Library:
    if not raw:
        return default_library()
    if ":" not in raw:
        raise ZoteroError("Use --library user:<userID> or --library group:<groupID>")
    kind, identifier = raw.split(":", 1)
    if kind not in {"user", "group"} or not identifier:
        raise ZoteroError("Use --library user:<userID> or --library group:<groupID>")
    return Library(kind, identifier)


def collection_data(row: dict[str, Any]) -> dict[str, Any]:
    data = row.get("data")
    return data if isinstance(data, dict) else row


def list_collections(library: Library) -> list[dict[str, Any]]:
    rows = paged_get(f"{library.path}/collections")
    keyed = {row.get("key") or collection_data(row).get("key"): row for row in rows}
    path_cache: dict[str, str] = {}

    def full_path(key: str, seen: set[str] | None = None) -> str:
        if key in path_cache:
            return path_cache[key]
        if key not in keyed:
            return key
        seen = set(seen or set())
        if key in seen:
            raise ZoteroError(f"Collection parent cycle detected at {key}")
        seen.add(key)
        data = collection_data(keyed[key])
        name = data.get("name") or key
        parent = data.get("parentCollection")
        if parent:
            value = full_path(parent, seen) + "/" + name
        else:
            value = name
        path_cache[key] = value
        return value

    out: list[dict[str, Any]] = []
    for row in rows:
        data = collection_data(row)
        key = row.get("key") or data.get("key")
        if not key:
            continue
        out.append(
            {
                "key": key,
                "name": data.get("name"),
                "parentCollection": data.get("parentCollection"),
                "path": full_path(key),
                "version": row.get("version"),
            }
        )
    return sorted(out, key=lambda item: item["path"].casefold())


def clean_collection_path(path: str) -> str:
    parts = [part.strip() for part in path.split("/") if part.strip()]
    if not parts:
        raise ZoteroError("Collection path is empty")
    return "/".join(parts)


def resolve_collection(selector: str, library: Library) -> dict[str, Any]:
    selector = clean_collection_path(selector) if "/" in selector else selector.strip()
    if not selector:
        raise ZoteroError("Collection selector is empty")
    collections = list_collections(library)
    exact_key = [row for row in collections if row["key"] == selector]
    if exact_key:
        return exact_key[0]
    exact_path = [row for row in collections if row["path"] == selector]
    if exact_path:
        return exact_path[0]
    leaf = [row for row in collections if row["name"] == selector]
    if len(leaf) == 1:
        return leaf[0]
    if len(leaf) > 1:
        paths = ", ".join(row["path"] for row in leaf)
        raise ZoteroError(f"Ambiguous collection leaf name {selector!r}; use full path. Matches: {paths}")
    raise ZoteroError(f"No collection matched {selector!r}")


def create_collection(name: str, parent_key: str | None, library: Library) -> dict[str, Any]:
    payload: dict[str, Any] = {"name": name}
    if parent_key:
        payload["parentCollection"] = parent_key
    response = parse_json_response(request(f"{library.path}/collections", method="POST", data=[payload]))
    successful = (response or {}).get("successful", {})
    row = successful.get("0")
    if not row:
        raise ZoteroError(f"Collection creation failed: {response}")
    return row


def ensure_collection(path: str, library: Library, *, yes: bool) -> dict[str, Any]:
    normalized = clean_collection_path(path)
    existing = {row["path"]: row for row in list_collections(library)}
    if normalized in existing:
        return {
            "status": "exists",
            "path": normalized,
            "key": existing[normalized]["key"],
            "created": [],
            "dry_run": False,
        }

    parts = normalized.split("/")
    current_path = ""
    parent_key: str | None = None
    created: list[dict[str, Any]] = []
    missing: list[dict[str, Any]] = []
    collections_by_path = existing

    for part in parts:
        current_path = part if not current_path else current_path + "/" + part
        found = collections_by_path.get(current_path)
        if found:
            parent_key = found["key"]
            continue
        missing.append({"name": part, "path": current_path, "parentCollection": parent_key})
        if yes:
            original_parent_key = parent_key
            row = create_collection(part, parent_key, library)
            parent_key = row["key"]
            created.append(
                {
                    "key": row["key"],
                    "name": part,
                    "path": current_path,
                    "parentCollection": row.get("data", {}).get("parentCollection", original_parent_key),
                }
            )
            collections_by_path[current_path] = {"key": parent_key, "path": current_path, "name": part}
        else:
            parent_key = f"<would-create:{current_path}>"

    if not yes:
        return {
            "status": "would_create",
            "path": normalized,
            "key": None,
            "missing": missing,
            "dry_run": True,
        }

    resolved = resolve_collection(normalized, library)
    return {
        "status": "created",
        "path": normalized,
        "key": resolved["key"],
        "created": created,
        "dry_run": False,
    }


def normalize_doi(value: str | None) -> str | None:
    if not value:
        return None
    doi = value.strip()
    doi = re.sub(r"^https?://(dx\.)?doi\.org/", "", doi, flags=re.I)
    doi = re.sub(r"^doi:\s*", "", doi, flags=re.I)
    return doi.lower() or None


def normalize_title(value: str | None) -> str | None:
    if not value:
        return None
    text = re.sub(r"\s+", " ", value.strip().casefold())
    text = re.sub(r"[^\w\s]+", "", text)
    return text or None


def creators_from_item(data: dict[str, Any]) -> list[str]:
    names: list[str] = []
    for creator in data.get("creators", []) or []:
        name = creator.get("name") or " ".join(
            part for part in [creator.get("firstName"), creator.get("lastName")] if part
        )
        if name:
            names.append(name)
    return names


def summarize_item(row: dict[str, Any]) -> dict[str, Any]:
    data = row.get("data", row)
    return {
        "key": row.get("key") or data.get("key"),
        "version": row.get("version") or data.get("version"),
        "itemType": data.get("itemType"),
        "title": data.get("title"),
        "creators": creators_from_item(data),
        "date": data.get("date"),
        "DOI": data.get("DOI"),
        "url": data.get("url"),
        "collections": data.get("collections") or [],
    }


def search_top_items(query_text: str, library: Library) -> list[dict[str, Any]]:
    params = query({"q": query_text, "limit": PAGE_LIMIT})
    return paged_get(f"{library.path}/items/top?{params}")


def all_top_items(library: Library) -> list[dict[str, Any]]:
    return paged_get(f"{library.path}/items/top")


def find_items(library: Library, *, doi: str | None = None, title: str | None = None) -> list[dict[str, Any]]:
    target_doi = normalize_doi(doi)
    target_title = normalize_title(title)
    candidates: list[dict[str, Any]] = []
    seen: set[str] = set()
    for q in [doi, title]:
        if not q:
            continue
        for row in search_top_items(q, library):
            key = row.get("key") or row.get("data", {}).get("key")
            if key and key not in seen:
                candidates.append(row)
                seen.add(key)

    def exact_matches(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
        matches: list[dict[str, Any]] = []
        match_keys: set[str] = set()
        for row in rows:
            key = row.get("key") or row.get("data", {}).get("key")
            data = row.get("data", row)
            matched = False
            if target_doi and normalize_doi(data.get("DOI")) == target_doi:
                matched = True
            elif target_title and normalize_title(data.get("title")) == target_title:
                matched = True
            if matched and key not in match_keys:
                matches.append(row)
                if key:
                    match_keys.add(key)
        return matches

    matches = exact_matches(candidates)
    doi_matched = any(
        target_doi and normalize_doi(row.get("data", row).get("DOI")) == target_doi
        for row in matches
    )
    if target_doi and not doi_matched:
        # Zotero's q search may not surface DOI-only matches in all libraries.
        # Fall back to an exact scan of top-level items to avoid duplicate imports.
        all_rows = all_top_items(library)
        matches = exact_matches(all_rows)
    return matches


def load_metadata(path: str) -> Any:
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def normalize_tags(tags: Any) -> list[dict[str, str]]:
    if not tags:
        return []
    normalized: list[dict[str, str]] = []
    for tag in tags:
        if isinstance(tag, str):
            if tag.strip():
                normalized.append({"tag": tag.strip()})
        elif isinstance(tag, dict) and tag.get("tag"):
            normalized.append(tag)
    return normalized


def normalize_metadata(raw: dict[str, Any], collection_key: str | None) -> dict[str, Any]:
    item = copy.deepcopy(raw)
    item.pop("collection", None)
    item.pop("collectionKey", None)
    item.setdefault("itemType", "journalArticle")
    item["tags"] = normalize_tags(item.get("tags"))
    if collection_key:
        item["collections"] = [collection_key]
    elif "collections" in item and not isinstance(item["collections"], list):
        raise ZoteroError("metadata.collections must be a list of collection keys")
    return item


def item_identity(metadata: dict[str, Any]) -> tuple[str | None, str | None]:
    return normalize_doi(metadata.get("DOI")), metadata.get("title")


def get_item(library: Library, key: str) -> dict[str, Any]:
    data = parse_json_response(request(f"{library.path}/items/{urllib.parse.quote(key)}"))
    if not isinstance(data, dict):
        raise ZoteroError(f"Unexpected item response for {key}")
    return data


def get_collection(library: Library, key: str) -> dict[str, Any]:
    data = parse_json_response(request(f"{library.path}/collections/{urllib.parse.quote(key)}"))
    if not isinstance(data, dict):
        raise ZoteroError(f"Unexpected collection response for {key}")
    return data


def create_item(library: Library, metadata: dict[str, Any]) -> dict[str, Any]:
    response = parse_json_response(request(f"{library.path}/items", method="POST", data=[metadata]))
    successful = (response or {}).get("successful", {})
    row = successful.get("0")
    if not row:
        raise ZoteroError(f"Item creation failed: {response}")
    return row


def patch_item_collections(library: Library, item: dict[str, Any], collection_key: str) -> dict[str, Any]:
    data = item.get("data", item)
    key = item.get("key") or data.get("key")
    if not key:
        raise ZoteroError("Cannot patch item without key")
    existing = list(data.get("collections") or [])
    if collection_key in existing:
        return {"key": key, "status": "already_in_collection", "collections": existing}
    updated = existing + [collection_key]
    version = item.get("version") or data.get("version")
    headers = {"If-Unmodified-Since-Version": str(version)} if version is not None else {}
    response = parse_json_response(
        request(
            f"{library.path}/items/{urllib.parse.quote(key)}",
            method="PATCH",
            data={"collections": updated},
            extra_headers=headers,
        )
    )
    return {"key": key, "status": "collection_added", "collections": updated, "response": response}


def delete_collection(library: Library, key: str) -> dict[str, Any]:
    collection = get_collection(library, key)
    version = collection.get("version") or collection.get("data", {}).get("version")
    headers = {"If-Unmodified-Since-Version": str(version)} if version is not None else {}
    response = request(
        f"{library.path}/collections/{urllib.parse.quote(key)}",
        method="DELETE",
        extra_headers=headers,
    )
    return {"key": key, "status": response.status}


def collection_for_metadata(
    metadata: dict[str, Any],
    *,
    library: Library,
    explicit_collection: str | None,
    default_collection: str | None,
    create_collection_flag: bool,
    yes: bool,
) -> dict[str, Any] | None:
    selector = explicit_collection or metadata.get("collection") or metadata.get("collectionPath") or default_collection
    if not selector:
        return None
    if create_collection_flag:
        return ensure_collection(selector, library, yes=yes)
    return resolve_collection(selector, library)


def upsert_one(
    metadata: dict[str, Any],
    *,
    library: Library,
    collection_selector: str | None,
    default_collection: str | None,
    create_collection_flag: bool,
    yes: bool,
) -> dict[str, Any]:
    collection = collection_for_metadata(
        metadata,
        library=library,
        explicit_collection=collection_selector,
        default_collection=default_collection,
        create_collection_flag=create_collection_flag,
        yes=yes,
    )
    collection_key = collection.get("key") if collection else None
    doi, title = item_identity(metadata)
    collection_missing_dry_run = bool(
        collection
        and collection.get("dry_run")
        and not collection_key
        and (collection_selector or default_collection or metadata.get("collection"))
    )

    matches = find_items(library, doi=doi, title=title)
    if matches:
        item = matches[0]
        summary = summarize_item(item)
        if collection_missing_dry_run:
            return {
                "status": "would_create_collection_and_update_existing",
                "item": summary,
                "collection": collection,
                "dry_run": True,
            }
        if not collection_key:
            return {"status": "exists", "item": summary, "dry_run": not yes}
        if collection_key in summary["collections"]:
            return {
                "status": "exists_in_collection",
                "item": summary,
                "collection": collection,
                "dry_run": not yes,
            }
        if not yes:
            return {
                "status": "would_update_collection",
                "item": summary,
                "collection": collection,
                "dry_run": True,
            }
        patched = patch_item_collections(library, item, collection_key)
        refreshed = get_item(library, summary["key"])
        return {
            "status": "updated_collection",
            "item": summarize_item(refreshed),
            "collection": collection,
            "patch": patched["status"],
            "dry_run": False,
        }

    item_payload = normalize_metadata(metadata, collection_key)
    if collection_missing_dry_run:
        return {
            "status": "would_create_collection_and_item",
            "item": summarize_item({"data": item_payload}),
            "collection": collection,
            "dry_run": True,
        }
    if not yes:
        return {
            "status": "would_create",
            "item": summarize_item({"data": item_payload}),
            "collection": collection,
            "dry_run": True,
        }
    created = create_item(library, item_payload)
    created_key = created.get("key")
    item = get_item(library, created_key) if created_key else {"data": created.get("data", item_payload)}
    return {
        "status": "created",
        "item": summarize_item(item),
        "collection": collection,
        "dry_run": False,
    }


def cmd_status(args: argparse.Namespace) -> None:
    status = key_status()
    access = status.get("access") or {}
    payload = {
        "userID": status.get("userID"),
        "username": status.get("username"),
        "displayName": status.get("displayName"),
        "access": access,
        "has_key": True,
    }
    output(payload, args.json)


def cmd_collections(args: argparse.Namespace) -> None:
    library = parse_library(args.library)
    output({"library": library.label, "collections": list_collections(library)}, args.json)


def cmd_resolve_collection(args: argparse.Namespace) -> None:
    library = parse_library(args.library)
    row = resolve_collection(args.path, library)
    output({"library": library.label, "collection": row}, args.json)


def cmd_ensure_collection(args: argparse.Namespace) -> None:
    library = parse_library(args.library)
    result = ensure_collection(args.path, library, yes=args.yes)
    result["library"] = library.label
    output(result, args.json)


def cmd_delete_collection(args: argparse.Namespace) -> None:
    library = parse_library(args.library)
    row = resolve_collection(args.path, library)
    if not args.yes:
        output(
            {
                "library": library.label,
                "status": "would_delete",
                "collection": row,
                "dry_run": True,
            },
            args.json,
        )
        return
    result = delete_collection(library, row["key"])
    result["library"] = library.label
    result["collection"] = row
    output(result, args.json)


def cmd_find(args: argparse.Namespace) -> None:
    library = parse_library(args.library)
    if not args.doi and not args.title:
        raise ZoteroError("Provide --doi or --title")
    matches = [summarize_item(row) for row in find_items(library, doi=args.doi, title=args.title)]
    output({"library": library.label, "matches": matches}, args.json)


def cmd_upsert_item(args: argparse.Namespace) -> None:
    library = parse_library(args.library)
    metadata = load_metadata(args.metadata)
    if not isinstance(metadata, dict):
        raise ZoteroError("--metadata for upsert-item must be a JSON object")
    result = upsert_one(
        metadata,
        library=library,
        collection_selector=args.collection,
        default_collection=None,
        create_collection_flag=args.create_collection,
        yes=args.yes,
    )
    result["library"] = library.label
    output(result, args.json)


def cmd_import_batch(args: argparse.Namespace) -> None:
    library = parse_library(args.library)
    metadata = load_metadata(args.metadata)
    if isinstance(metadata, dict):
        records = metadata.get("items")
        if not isinstance(records, list):
            raise ZoteroError("Batch metadata must be a JSON array or an object with an items array")
    elif isinstance(metadata, list):
        records = metadata
    else:
        raise ZoteroError("Batch metadata must be a JSON array")

    results: list[dict[str, Any]] = []
    for index, record in enumerate(records):
        if not isinstance(record, dict):
            results.append({"index": index, "status": "error", "error": "record is not an object"})
            continue
        try:
            result = upsert_one(
                record,
                library=library,
                collection_selector=None,
                default_collection=args.default_collection,
                create_collection_flag=args.create_collection,
                yes=args.yes,
            )
            result["index"] = index
            results.append(result)
        except Exception as exc:  # keep batch moving and report per-record errors
            results.append({"index": index, "status": "error", "error": str(exc)})

    summary: dict[str, int] = {}
    for result in results:
        summary[result.get("status", "unknown")] = summary.get(result.get("status", "unknown"), 0) + 1
    output({"library": library.label, "dry_run": not args.yes, "summary": summary, "results": results}, args.json)


def output(payload: Any, as_json: bool) -> None:
    if as_json:
        dump_json(payload)
        return
    if isinstance(payload, dict):
        for key, value in payload.items():
            print(f"{key}: {value}")
    else:
        print(payload)


def add_common(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--library", help="Target library as user:<id> or group:<id>; defaults to API key user")
    parser.add_argument("--json", action="store_true", help="Print JSON output")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Write Zotero metadata through the Web API")
    sub = parser.add_subparsers(dest="command", required=True)

    status = sub.add_parser("status", help="Show sanitized API key status")
    status.add_argument("--json", action="store_true")
    status.set_defaults(func=cmd_status)

    collections = sub.add_parser("collections", help="List collection paths")
    add_common(collections)
    collections.set_defaults(func=cmd_collections)

    resolve = sub.add_parser("resolve-collection", help="Resolve a collection path/name/key")
    add_common(resolve)
    resolve.add_argument("--path", required=True)
    resolve.set_defaults(func=cmd_resolve_collection)

    ensure = sub.add_parser("ensure-collection", help="Create a collection path if missing")
    add_common(ensure)
    ensure.add_argument("--path", required=True)
    ensure.add_argument("--yes", action="store_true", help="Actually create missing collections")
    ensure.set_defaults(func=cmd_ensure_collection)

    delete = sub.add_parser("delete-collection", help="Delete a collection; intended for test cleanup")
    add_common(delete)
    delete.add_argument("--path", required=True)
    delete.add_argument("--yes", action="store_true", help="Actually delete the collection")
    delete.set_defaults(func=cmd_delete_collection)

    find = sub.add_parser("find", help="Find existing items by DOI or title")
    add_common(find)
    find.add_argument("--doi")
    find.add_argument("--title")
    find.set_defaults(func=cmd_find)

    upsert = sub.add_parser("upsert-item", help="Create item or add existing item to collection")
    add_common(upsert)
    upsert.add_argument("--metadata", required=True)
    upsert.add_argument("--collection")
    upsert.add_argument("--create-collection", action="store_true")
    upsert.add_argument("--yes", action="store_true", help="Actually write to Zotero")
    upsert.set_defaults(func=cmd_upsert_item)

    batch = sub.add_parser("import-batch", help="Import a JSON array of item metadata")
    add_common(batch)
    batch.add_argument("--metadata", required=True)
    batch.add_argument("--default-collection")
    batch.add_argument("--create-collection", action="store_true")
    batch.add_argument("--yes", action="store_true", help="Actually write to Zotero")
    batch.set_defaults(func=cmd_import_batch)

    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        args.func(args)
        return 0
    except ZoteroError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
