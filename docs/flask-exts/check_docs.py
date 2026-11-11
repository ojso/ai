#!/usr/bin/env python3
"""Flask-Exts Markdown 文档集静态自检脚本。

检查项：
1. 代码围栏（```）成对闭合（奇偶性）。
2. Markdown 表格列数一致性（表头、分隔线与数据行）。
3. 本地相对文件路径有效性；`flask-exts/` 前缀的仓库路径仅在设置
   `FLASK_EXTS_REPO` 环境变量时校验。
4. 内部 Heading 锚点与显式 <a id="..."> 标签有效性。
5. 结构性检查：标题缺少空格、标题与正文粘连、编号深度与标题层级不一致。

用法：
    python check_docs.py
    FLASK_EXTS_REPO=/path/to/flask-exts python check_docs.py
"""

from pathlib import Path
from urllib.parse import unquote, urlsplit
import os
import re
import sys

ROOT = Path(__file__).resolve().parent
REPO = (
    Path(os.environ["FLASK_EXTS_REPO"]).expanduser().resolve()
    if os.environ.get("FLASK_EXTS_REPO")
    else None
)


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


def check_structure(name: str, lines: list[str]) -> list[str]:
    """检查标题空格、标题粘连与编号层级。"""
    errors: list[str] = []
    in_fence = False

    for num, line in enumerate(lines, 1):
        if line.strip().startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence:
            continue

        # 标题标记后缺少空格，例如 "##标题"。
        if re.match(r"^#{1,6}[^#\s]", line):
            errors.append(f"{name}:{num}: 标题标记后缺少空格 -> {line.strip()[:60]}")

        # 标题与正文粘连，例如 "正文## 标题"；要求标题标记前是非空白且非 # 字符。
        if re.search(r"[^\s#]#{2,6}\s", line):
            errors.append(f"{name}:{num}: 标题与正文粘连，标题前应有换行 -> {line.strip()[:60]}")

        # 编号深度应与标题层级一致：H2=1 段、H3=2 段、H4=3 段……
        heading = re.match(r"^(#{1,6})\s+(\d+(?:\.\d+)*)\.?\s", line)
        if heading:
            level = len(heading.group(1))
            expected = len(heading.group(2).split(".")) + 1
            if level != expected:
                errors.append(
                    f"{name}:{num}: 编号 {heading.group(2)} 使用 H{level}，"
                    f"按层级应为 H{expected} -> {line.strip()[:60]}"
                )

    return errors


def main() -> int:
    errors: list[str] = []
    md_files = sorted(ROOT.glob("*.md"))
    anchor_cache: dict[Path, set[str]] = {}
    skipped_repo_links = 0

    for src in md_files:
        lines = src.read_text(encoding="utf-8").splitlines()
        fences = sum(1 for line in lines if line.strip().startswith("```"))
        if fences % 2 != 0:
            errors.append(f"{src.name}: 代码围栏未闭合（总数={fences}，应为偶数）")

        errors.extend(check_structure(src.name, lines))

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
                    if REPO is None:
                        skipped_repo_links += 1
                        continue
                    dst = REPO / raw_path[len("flask-exts/") :]
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
    print("结构性检查通过：标题空格、标题粘连与编号层级均正常。")
    if skipped_repo_links:
        print(
            f"跳过 {skipped_repo_links} 个 `flask-exts/` 仓库链接；"
            "设置 FLASK_EXTS_REPO 后可校验。"
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
