#!/usr/bin/env python3
"""使用 MinerU 解析 PDF，并把结果保存到当前项目的 minerU/outputs。"""

from __future__ import annotations

import argparse
import io
import os
import re
import sys
import time
import urllib.parse
import uuid
import zipfile
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any



PROJECT_ROOT = Path.cwd().resolve()
MINERU_ROOT = PROJECT_ROOT / "minerU"
OUTPUT_ROOT = MINERU_ROOT / "outputs"
MINERU_BASE = "https://mineru.net"
IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".gif", ".bmp", ".tif", ".tiff"}


class MinerUError(RuntimeError):
    pass


def get_requests():
    try:
        import requests
    except ModuleNotFoundError as exc:
        raise MinerUError("缺少 Python 依赖 requests，请先运行：pip install requests") from exc
    return requests


@dataclass
class ParseResult:
    markdown: str
    assets: dict[str, bytes]


class ChineseArgumentParser(argparse.ArgumentParser):
    def format_help(self) -> str:
        text = super().format_help()
        return (
            text.replace("usage:", "用法:")
            .replace("positional arguments:", "位置参数:")
            .replace("options:", "选项:")
            .replace("optional arguments:", "选项:")
            .replace("show this help message and exit", "显示帮助信息并退出")
        )

    def format_usage(self) -> str:
        return super().format_usage().replace("usage:", "用法:")


def is_url(value: str) -> bool:
    parsed = urllib.parse.urlparse(value)
    return parsed.scheme in {"http", "https"}


def safe_url(url: str) -> str:
    parsed = urllib.parse.urlparse(url)
    if not parsed.query:
        return url
    return urllib.parse.urlunparse(parsed._replace(query="<redacted>"))


def slugify(value: str) -> str:
    value = Path(value).stem or "document"
    value = value.lower()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    return value.strip("-") or "document"


def source_display_name(source: str, file_name: str | None = None) -> str:
    if file_name:
        return file_name
    if is_url(source):
        parsed = urllib.parse.urlparse(source)
        return Path(urllib.parse.unquote(parsed.path)).name or "document.pdf"
    return Path(source).name or "document.pdf"


def resolve_local_source(source: str) -> Path:
    path = Path(source).expanduser()
    if not path.is_absolute():
        path = Path.cwd() / path
    path = path.resolve()
    if not path.is_file():
        raise MinerUError(f"找不到输入文件：{source}")
    return path


def json_request(
    method: str,
    url: str,
    payload: dict[str, Any] | None = None,
    headers: dict[str, str] | None = None,
    timeout: int = 60,
    retries: int = 2,
) -> dict[str, Any]:
    requests = get_requests()
    request_headers = {"Accept": "application/json"}
    if headers:
        request_headers.update(headers)

    for attempt in range(retries + 1):
        try:
            response = requests.request(method, url, json=payload, headers=request_headers, timeout=timeout)
            if response.status_code >= 400:
                raise MinerUError(f"HTTP {response.status_code} from {safe_url(url)}: {response.text[:800]}")
            return response.json()
        except requests.JSONDecodeError as exc:
            raise MinerUError(f"{safe_url(url)} 返回的不是 JSON：{response.text[:200]!r}") from exc
        except requests.RequestException as exc:
            if attempt < retries:
                time.sleep(2**attempt)
                continue
            raise MinerUError(f"请求 {safe_url(url)} 时发生网络错误：{exc}") from exc

    raise MinerUError(f"请求 {safe_url(url)} 时发生未知错误")


def binary_request(
    method: str,
    url: str,
    data: bytes | None = None,
    headers: dict[str, str] | None = None,
    timeout: int = 120,
    retries: int = 2,
) -> bytes:
    requests = get_requests()
    request_headers = dict(headers or {})

    for attempt in range(retries + 1):
        try:
            response = requests.request(method, url, data=data, headers=request_headers, timeout=timeout)
            if response.status_code >= 400:
                raise MinerUError(f"HTTP {response.status_code} from {safe_url(url)}: {response.text[:800]}")
            return response.content
        except requests.RequestException as exc:
            if attempt < retries:
                time.sleep(2**attempt)
                continue
            raise MinerUError(f"请求 {safe_url(url)} 时发生网络错误：{exc}") from exc
    raise MinerUError(f"请求 {safe_url(url)} 时发生未知错误")


def upload_file(url: str, path: Path, timeout: int = 120, retries: int = 2) -> None:
    """按 MinerU 要求上传文件：PUT 文件流，不设置 Content-Type。"""

    requests = get_requests()
    for attempt in range(retries + 1):
        try:
            with path.open("rb") as file:
                response = requests.put(url, data=file, timeout=timeout)
            if response.status_code >= 400:
                raise MinerUError(f"HTTP {response.status_code} from {safe_url(url)}: {response.text[:800]}")
            return
        except requests.RequestException as exc:
            if attempt < retries:
                time.sleep(2**attempt)
                continue
            raise MinerUError(f"上传 {path} 到 {safe_url(url)} 时失败：{exc}") from exc


def require_success(result: dict[str, Any], context: str) -> dict[str, Any]:
    if result.get("code") != 0:
        raise MinerUError(f"{context} 失败：{result.get('msg', result)}")
    data = result.get("data")
    if not isinstance(data, dict):
        raise MinerUError(f"{context} 未返回 data 对象：{result}")
    return data


def ensure_inside_output_root(path: Path) -> None:
    try:
        path.relative_to(OUTPUT_ROOT.resolve())
    except ValueError as exc:
        raise MinerUError(f"输出路径必须位于 minerU/outputs/ 下：{path}") from exc


def resolve_output(source: str, out: str | None, force: bool, file_name: str | None = None) -> Path:
    if out:
        target = Path(out).expanduser()
        if not target.is_absolute():
            target = PROJECT_ROOT / target
        target = target.resolve()
    else:
        name = source_display_name(source, file_name)
        target = (OUTPUT_ROOT / f"{slugify(name)}.mineru.md").resolve()

    ensure_inside_output_root(target)
    if target.suffix.lower() != ".md":
        raise MinerUError(f"输出路径必须是 Markdown 文件：{target}")

    if force or not target.exists():
        return target

    stem = target.stem
    suffix = target.suffix
    for index in range(1, 1000):
        candidate = target.with_name(f"{stem}-{index}{suffix}")
        if not candidate.exists():
            return candidate
    raise MinerUError(f"无法在 {target} 附近找到可用输出路径")


def is_safe_relative_path(path: str) -> bool:
    parts = PurePosixPath(path).parts
    return bool(parts) and not PurePosixPath(path).is_absolute() and ".." not in parts


def markdown_asset_dir(output: Path) -> Path:
    return output.with_suffix("")


def normalize_zip_asset_path(name: str, markdown_name: str) -> str | None:
    if name.endswith("/"):
        return None

    path = PurePosixPath(name)
    if path.suffix.lower() not in IMAGE_EXTENSIONS:
        return None

    markdown_parent = PurePosixPath(markdown_name).parent
    try:
        rel = path.relative_to(markdown_parent)
    except ValueError:
        parts = path.parts
        if "images" not in parts:
            return None
        rel = PurePosixPath(*parts[parts.index("images") :])

    rel_text = rel.as_posix()
    return rel_text if is_safe_relative_path(rel_text) else None


def rewrite_image_links(markdown: str, output: Path, assets: dict[str, bytes]) -> str:
    asset_root = markdown_asset_dir(output).name
    asset_names = set(assets)

    def replace(match: re.Match[str]) -> str:
        alt = match.group("alt")
        target = match.group("target").strip()
        if target.startswith("<") and target.endswith(">"):
            target = target[1:-1].strip()
        parsed = urllib.parse.urlparse(target)
        if parsed.scheme or target.startswith("#"):
            return match.group(0)

        clean_target = urllib.parse.unquote(parsed.path)
        if clean_target not in asset_names:
            return match.group(0)

        rewritten = f"{asset_root}/{clean_target}"
        if parsed.query:
            rewritten = f"{rewritten}?{parsed.query}"
        if parsed.fragment:
            rewritten = f"{rewritten}#{parsed.fragment}"
        return f"![{alt}]({rewritten})"

    return re.sub(r"!\[(?P<alt>[^\]]*)\]\((?P<target>[^)]+)\)", replace, markdown)


def write_parse_result(output: Path, result: ParseResult, force: bool) -> list[Path]:
    output.parent.mkdir(parents=True, exist_ok=True)
    if output.exists() and not force:
        raise MinerUError(f"输出文件已存在：{output}")

    written_assets: list[Path] = []
    asset_dir = markdown_asset_dir(output)
    for rel_name, content in result.assets.items():
        if not is_safe_relative_path(rel_name):
            raise MinerUError(f"结果包中包含不安全的资源路径：{rel_name}")
        target = asset_dir / rel_name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(content)
        written_assets.append(target)

    markdown = rewrite_image_links(result.markdown, output, result.assets)
    output.write_text(markdown, encoding="utf-8")
    return written_assets


def poll_agent(task_id: str, timeout: int, interval: int) -> ParseResult:
    deadline = time.time() + timeout
    while time.time() < deadline:
        result = json_request("GET", f"{MINERU_BASE}/api/v1/agent/parse/{task_id}")
        data = require_success(result, "轮询 agent 任务")
        state = data.get("state")
        if state == "done":
            markdown_url = data.get("markdown_url")
            if not markdown_url:
                raise MinerUError(f"Agent 任务 {task_id} 已完成，但未返回 markdown_url")
            return ParseResult(binary_request("GET", markdown_url).decode("utf-8", errors="replace"), {})
        if state == "failed":
            raise MinerUError(f"Agent 任务 {task_id} 失败：{data.get('err_msg', data)}")
        print(f"MinerU agent 任务 {task_id}：{state or 'pending'}")
        time.sleep(interval)
    raise MinerUError(f"等待 MinerU agent 任务 {task_id} 超时")


def parse_agent(source: str, args: argparse.Namespace) -> ParseResult:
    payload = {
        "language": args.language,
        "enable_table": not args.no_table,
        "is_ocr": args.ocr,
        "enable_formula": not args.no_formula,
    }
    if args.page_range:
        payload["page_range"] = args.page_range

    if is_url(source):
        payload["url"] = source
        if args.file_name:
            payload["file_name"] = args.file_name
        data = require_success(
            json_request("POST", f"{MINERU_BASE}/api/v1/agent/parse/url", payload),
            "提交 agent URL 解析任务",
        )
    else:
        path = resolve_local_source(source)
        payload["file_name"] = args.file_name or path.name
        data = require_success(
            json_request("POST", f"{MINERU_BASE}/api/v1/agent/parse/file", payload),
            "提交 agent 文件解析任务",
        )
        file_url = data.get("file_url")
        if not file_url:
            raise MinerUError("提交 agent 文件解析任务后未返回 file_url")
        upload_file(file_url, path)

    task_id = data.get("task_id")
    if not task_id:
        raise MinerUError(f"MinerU 未返回 task_id：{data}")
    return poll_agent(task_id, args.timeout, args.interval)


def extract_result_from_zip(zip_bytes: bytes) -> ParseResult:
    with zipfile.ZipFile(io.BytesIO(zip_bytes)) as archive:
        markdown_names = [name for name in archive.namelist() if name.lower().endswith(".md")]
        if not markdown_names:
            raise MinerUError("精准解析结果 zip 中没有 Markdown 文件")
        markdown_names.sort(key=lambda name: archive.getinfo(name).file_size, reverse=True)
        markdown_name = markdown_names[0]
        assets: dict[str, bytes] = {}
        for name in archive.namelist():
            rel_name = normalize_zip_asset_path(name, markdown_name)
            if rel_name:
                assets[rel_name] = archive.read(name)
        return ParseResult(archive.read(markdown_name).decode("utf-8", errors="replace"), assets)


def poll_precision_task(task_id: str, token: str, timeout: int, interval: int) -> ParseResult:
    headers = {"Authorization": f"Bearer {token}"}
    deadline = time.time() + timeout
    while time.time() < deadline:
        result = json_request("GET", f"{MINERU_BASE}/api/v4/extract/task/{task_id}", headers=headers)
        data = require_success(result, "轮询精准解析任务")
        state = data.get("state")
        if state == "done":
            zip_url = data.get("full_zip_url")
            if not zip_url:
                raise MinerUError(f"精准解析任务 {task_id} 已完成，但未返回 full_zip_url")
            return extract_result_from_zip(binary_request("GET", zip_url))
        if state == "failed":
            raise MinerUError(f"精准解析任务 {task_id} 失败：{data.get('err_msg', data)}")
        print(f"MinerU 精准解析任务 {task_id}：{state or 'pending'}")
        time.sleep(interval)
    raise MinerUError(f"等待 MinerU 精准解析任务 {task_id} 超时")


def poll_precision_batch(batch_id: str, token: str, timeout: int, interval: int) -> ParseResult:
    headers = {"Authorization": f"Bearer {token}"}
    deadline = time.time() + timeout
    while time.time() < deadline:
        result = json_request("GET", f"{MINERU_BASE}/api/v4/extract-results/batch/{batch_id}", headers=headers)
        data = require_success(result, "轮询精准解析批量任务")
        state = find_first(data, "state")
        if state == "failed":
            raise MinerUError(f"精准解析批量任务 {batch_id} 失败：{data}")
        zip_url = find_first_url(data, "full_zip_url")
        if zip_url:
            return extract_result_from_zip(binary_request("GET", zip_url))
        print(f"MinerU 精准解析批量任务 {batch_id}：{state or 'pending'}")
        time.sleep(interval)
    raise MinerUError(f"等待 MinerU 精准解析批量任务 {batch_id} 超时")


def find_first(value: Any, key: str) -> Any:
    if isinstance(value, dict):
        if key in value:
            return value[key]
        for child in value.values():
            found = find_first(child, key)
            if found is not None:
                return found
    elif isinstance(value, list):
        for child in value:
            found = find_first(child, key)
            if found is not None:
                return found
    return None


def find_first_url(value: Any, key: str) -> str | None:
    found = find_first(value, key)
    return found if isinstance(found, str) and found.startswith(("http://", "https://")) else None


def parse_precision(source: str, args: argparse.Namespace) -> ParseResult:
    token = os.environ.get("MINERU_API_TOKEN")
    if not token:
        raise MinerUError("precision 模式需要先设置环境变量 MINERU_API_TOKEN")
    headers = {"Authorization": f"Bearer {token}"}

    common = {
        "model_version": args.model_version,
        "language": args.language,
        "enable_table": not args.no_table,
        "enable_formula": not args.no_formula,
    }
    if args.page_range:
        common["page_range"] = args.page_range

    if is_url(source):
        payload = {**common, "url": source, "is_ocr": args.ocr}
        if args.file_name:
            payload["file_name"] = args.file_name
        data = require_success(
            json_request("POST", f"{MINERU_BASE}/api/v4/extract/task", payload, headers=headers),
            "提交精准 URL 解析任务",
        )
        task_id = data.get("task_id")
        if not task_id:
            raise MinerUError(f"MinerU 未返回 task_id：{data}")
        return poll_precision_task(task_id, token, args.timeout, args.interval)

    path = resolve_local_source(source)
    data_id = f"mineru-pdf-parse-{uuid.uuid4()}"
    payload = {
        **common,
        "files": [{"name": args.file_name or path.name, "data_id": data_id, "is_ocr": args.ocr}],
    }
    data = require_success(
        json_request("POST", f"{MINERU_BASE}/api/v4/file-urls/batch", payload, headers=headers),
        "请求精准解析文件上传地址",
    )
    batch_id = data.get("batch_id")
    file_urls = data.get("file_urls")
    if not batch_id or not isinstance(file_urls, list) or not file_urls:
        raise MinerUError(f"MinerU 返回的批量上传数据不完整：{data}")
    upload_file(file_urls[0], path)
    return poll_precision_batch(batch_id, token, args.timeout, args.interval)


def parse_args() -> argparse.Namespace:
    parser = ChineseArgumentParser(description=__doc__)
    parser.add_argument("source", help="本地 PDF 路径或远程 PDF URL")
    parser.add_argument("--project-root", help="项目根目录；默认使用当前工作目录")
    parser.add_argument("--out", help="输出 Markdown 路径，必须位于 minerU/outputs/ 下")
    parser.add_argument("--force", action="store_true", help="如果输出文件已存在则覆盖；默认自动追加 -1、-2 后缀")
    parser.add_argument("--mode", choices=["auto", "agent", "precision"], default="auto", help="auto 有 token 时使用 precision，否则使用 agent")
    parser.add_argument("--model-version", default="vlm", help="精准解析 API 的 model_version")
    parser.add_argument("--language", default="ch", help="解析语言，例如 ch、en")
    parser.add_argument("--page-range", help="页码范围，例如 1-5 或 1,3,8-10")
    parser.add_argument("--file-name", help="覆盖发送给 MinerU 的文件名；URL 输入时建议显式指定")
    parser.add_argument("--ocr", action="store_true", help="启用 OCR")
    parser.add_argument("--no-table", action="store_true", help="禁用表格识别")
    parser.add_argument("--no-formula", action="store_true", help="禁用公式识别")
    parser.add_argument("--timeout", type=int, default=600, help="最长等待秒数")
    parser.add_argument("--interval", type=int, default=5, help="轮询间隔秒数")
    return parser.parse_args()


def main() -> int:
    global PROJECT_ROOT, MINERU_ROOT, OUTPUT_ROOT

    args = parse_args()
    if args.project_root:
        PROJECT_ROOT = Path(args.project_root).expanduser().resolve()
        MINERU_ROOT = PROJECT_ROOT / "minerU"
        OUTPUT_ROOT = MINERU_ROOT / "outputs"

    mode = args.mode
    if mode == "auto":
        mode = "precision" if os.environ.get("MINERU_API_TOKEN") else "agent"

    try:
        output = resolve_output(args.source, args.out, args.force, args.file_name)
        result = parse_precision(args.source, args) if mode == "precision" else parse_agent(args.source, args)
        written_assets = write_parse_result(output, result, args.force)
    except MinerUError as exc:
        print(f"mineru_parse.py: {exc}", file=sys.stderr)
        return 1

    rel = output.relative_to(PROJECT_ROOT)
    print(f"已写入 Markdown：{rel}")
    if written_assets:
        asset_rel = markdown_asset_dir(output).relative_to(PROJECT_ROOT)
        print(f"已写入资源目录：{asset_rel}（{len(written_assets)} 个文件）")
    print("下一步：检查 Markdown 中的标题、公式、表格和图片链接；必要时手工修正。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
