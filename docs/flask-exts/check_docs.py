#!/usr/bin/env python3
"""Flask-Exts Markdown 文档集静态自检脚本。

检查项：
1. 代码围栏（```）成对闭合（奇偶性）。
2. Markdown 表格列数一致性（表头、分隔线与数据行）。
3. 本地相对文件路径有效性（含指向代码仓库的 flask-exts/ 路径）。
4. 内部 Heading 锚点与显式 <a id="..."> 标签有效性。

用法：
    python check_docs.py
"""

from pathlib import Path
from urllib.parse import unquote, urlsplit
import re
import sys

ROOT = Path(__file__).resolve().parent
REPO = Path.home() / "projects" / "flask-exts"


def slugify(text: str) -> str:
    """提取 Markdown 标题对应的标准锚点 Slug。"""
    text = re.sub(r"<[^>]+>", "", text)
    text = re.sub(r"[`*_~]", "", text).lower().strip()
    text = re.sub(r"[^\w\s-]", "", text, flags=re.UNICODE)
    return re.sub(r"\s", "-", text).strip("-")


def count_table_columns(line: str) -> int:
    """计算 Markdown 表格行的有效单元格数（忽略转义管道符）。"""
    pipes = 0
    escaped = False
    for char in line:
        if char == "|" and not escaped:
            pipes += 1
        if ord(char) == 92 and not escaped:
            escaped = True
        else:
            escaped = False
    return pipes - 1


def collect_anchors(path: Path) -> set[str]:
    """收集单个 Markdown 文件中所有的合法锚点（含 Heading 自动 Slug 与显式 a id）。"""
    ids: set[str] = set()
    duplicates: dict[str, int] = {}
    in_fence = False

    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip().startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence:
            continue

        explicit = re.search(r'<a\s+id=["\']?([^"\' >]+)', line, re.I)
        if explicit:
            ids.add(explicit.group(1))

        heading = re.match(r"^#{1,6}\s+(.+?)\s*#*$", line)
        if heading:
            base = slugify(heading.group(1))
            index = duplicates.get(base, 0)
            duplicates[base] = index + 1
            ids.add(base if index == 0 else f"{base}-{index}")

    return ids


def main() -> int:
    errors: list[str] = []
    md_files = sorted(ROOT.glob("*.md"))
    anchor_cache: dict[Path, set[str]] = {}

    for src in md_files:
        lines = src.read_text(encoding="utf-8").splitlines()
        fences = sum(1 for line in lines if line.strip().startswith("```"))
        if fences % 2 != 0:
            errors.append(f"{src.name}: 代码围栏未闭合（总数={fences}，应为偶数）")

        in_fence = False
        table_rows: list[tuple[int, int]] = []

        for num, line in enumerate(lines, 1):
            if line.strip().startswith("```"):
                in_fence = not in_fence
                continue
            if in_fence:
                continue

            # 表格列数检查
            if line.lstrip().startswith("|") and line.rstrip().endswith("|"):
                table_rows.append((num, count_table_columns(line)))
            elif table_rows:
                distinct_counts = {c for _, c in table_rows}
                if len(distinct_counts) > 1:
                    errors.append(f"{src.name}: 第 {table_rows[0][0]} 行附近表格列数不一致: {table_rows}")
                table_rows = []

            # 本地链接与锚点检查
            for match in re.finditer(r"\[[^\]]+\]\(([^)]+)\)", line):
                raw = match.group(1).split()[0].strip("<>")
                if raw.startswith(("http://", "https://", "mailto:", "tel:")):
                    continue

                parsed = urlsplit(raw)
                raw_path = unquote(parsed.path)

                if raw_path.startswith("flask-exts/"):
                    dst = REPO / raw_path[len("flask-exts/"):]
                elif raw_path:
                    dst = (src.parent / raw_path).resolve()
                else:
                    dst = src

                if not dst.exists():
                    errors.append(f"{src.name}:{num}: 目标文件不存在 -> {raw_path or raw}")
                    continue

                frag = unquote(parsed.fragment)
                if frag and dst.suffix.lower() == ".md":
                    if dst not in anchor_cache:
                        anchor_cache[dst] = collect_anchors(dst)
                    if frag not in anchor_cache[dst]:
                        errors.append(f"{src.name}:{num}: 文件 {dst.name} 中缺少锚点 #{frag}")

        if table_rows:
            distinct_counts = {c for _, c in table_rows}
            if len(distinct_counts) > 1:
                errors.append(f"{src.name}: 结尾附近表格列数不一致: {table_rows}")

    if errors:
        print(f"自检失败，共发现 {len(errors)} 处问题：", file=sys.stderr)
        for err in errors:
            print(f"  - {err}", file=sys.stderr)
        return 1

    print(f"自检通过！已核验 {len(md_files)} 份文档：代码围栏、表格列数、相对路径和内部锚点全部有效。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
