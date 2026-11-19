#!/usr/bin/env python3
"""Flask-Exts Markdown 文档集静态自检脚本。

检查项（语法层，始终执行）：
1. 代码围栏（```）成对闭合（奇偶性）。
2. Markdown 表格列数一致性（表头、分隔线与数据行）。
3. 本地相对文件路径有效性；`flask-exts/` 前缀的仓库路径仅在设置
   `FLASK_EXTS_REPO` 环境变量时校验。
4. 内部 Heading 锚点与显式 <a id="..."> 标签有效性。
5. 结构性检查：标题缺少空格、标题与正文粘连、编号深度与标题层级不一致。
   Markdown 规范同样在语法层校验：MD036（强调被当作标题）、
   MD032（列表前后缺空行，含块引用内的列表）、MD022（标题后缺空行）、
   MD012（连续空行，代码块内除外）。

检查项（语义层，始终执行）：
6. 契约数量声明一致性：正文声明的“N 条契约”必须等于实际 `REQ-*` 条目数。
7. 三维状态取值合法性：`lifecycle`/`implementation`/`verification` 的取值
   必须在 `requirements.md` 第 2.1 节登记的枚举内。
8. `passed` 证据可追溯：凡标 `verification: passed` 的契约，其证据必须能
   定位到 `testing.md` 小节或带 commit/HEAD，不允许裸测试数字。
9. 缺陷编号体系：主清单只允许 `CR-*`；旧前缀 `C<数字>`/`V-<数字>` 仅可出现在
   映射、废止或缺号说明语境；缺号必须在主清单下方声明。

检查项（仓库交叉层，仅在设置 FLASK_EXTS_REPO 时执行）：
10. 契约“验收”字段引用的测试文件必须存在。
11. 引用的测试函数/夹具（`path::name` 或裸 `test_xxx`）必须在仓库测试中定义。
12. 引用的 `TC-*` 用例编号必须在 `testing.md` 中登记。

派生数据核对（第 13 项，纯只读校验）：
13. 只读核对 `README.md` 与 `requirements.md` 头部的状态块数据（契约进度、
    文档集健康度），其中缺口计数来自 `gaps.md`。本脚本为纯只读门禁，严禁自动
    写入或回写文档；核对不一致时仅报错阻断并输出期望值，由维护者依据文档规则
    人工修正。

用法：
    python check_docs.py
    FLASK_EXTS_REPO=/path/to/flask-exts python check_docs.py
"""

import os
import re
import sys
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parent
REPO = (
    Path(os.environ["FLASK_EXTS_REPO"]).expanduser().resolve()
    if os.environ.get("FLASK_EXTS_REPO")
    else None
)

# requirements.md 第 2.1 节登记的三维状态取值。
LIFECYCLE_VALUES = {
    "draft",
    "in-review",
    "approved",
    "deprecated",
    "superseded",
    "unknown",
}
IMPLEMENTATION_VALUES = {"not-started", "in-progress", "implemented", "unknown"}
VERIFICATION_VALUES = {"unverified", "passed", "failed", "blocked", "unknown"}
STATUS_FIELD_VALUES = {
    "lifecycle": LIFECYCLE_VALUES,
    "implementation": IMPLEMENTATION_VALUES,
    "verification": VERIFICATION_VALUES,
}

# 缺陷编号合法语境：出现旧前缀但属于这些情形时不报错。
LEGACY_ALLOWED = ("旧编号映射", "缺号说明", "已废止", "别名", "前缀语义", "停用")


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
    """收集单个 Markdown 文件中所有的合法锚点(含 Heading 自动 Slug 与显式 a id)。"""
    ids: set[str] = set()
    duplicates: dict[str, int] = {}
    in_fence = False

    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip().startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence:
            continue

        explicit = re.search(r'<a\s+id=["\']?([^"\' >]+)', line, re.IGNORECASE)
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
            errors.append(
                f"{name}:{num}: 标题与正文粘连，标题前应有换行 -> {line.strip()[:60]}"
            )

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


def check_markdown_lint(name: str, lines: list[str]) -> list[str]:
    """MD036（强调被当作标题）与 MD032（列表前后空行）。"""
    errors: list[str] = []
    emphasis_only = re.compile(r"^\s*(?:>\s*)?\*\*[^*]+\*\*\s*$")
    list_item = re.compile(r"^\s*(?:[-*+]|\d+[.)])\s+")
    heading = re.compile(r"^\s*(?:>\s*)*#{1,6}\s")

    def unquote(text: str) -> str:
        return re.sub(r"^\s*(?:>\s*)+", "", text)

    def is_blank(index: int) -> bool:
        return unquote(lines[index]).strip() == ""

    def is_item(index: int) -> bool:
        return bool(list_item.match(unquote(lines[index])))

    def is_continuation(index: int) -> bool:
        body = unquote(lines[index])
        return bool(body) and (body.startswith(("  ", "\t")))

    in_fence = False
    for i, line in enumerate(lines):
        if line.strip().startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence:
            continue

        if emphasis_only.match(line):
            errors.append(f"{name}:{i + 1}: MD036 强调被当作标题 -> {line.strip()[:50]}")

        if i > 0 and not line.strip() and not lines[i - 1].strip() and not in_fence:
            errors.append(f"{name}:{i + 1}: MD012 连续空行")

        if heading.match(line) and i + 1 < len(lines) and lines[i + 1].strip():
            errors.append(
                f"{name}:{i + 2}: MD022 标题后缺空行 -> {lines[i + 1].strip()[:50]}"
            )

        if not is_item(i):
            continue
        if i > 0 and not (
            is_blank(i - 1)
            or is_item(i - 1)
            or is_continuation(i - 1)
            or heading.match(lines[i - 1])
            or lines[i - 1].strip().startswith("```")
        ):
            errors.append(f"{name}:{i + 1}: MD032 列表前缺空行 -> {line.strip()[:50]}")
        if i + 1 < len(lines) and not (
            is_blank(i + 1)
            or is_item(i + 1)
            or is_continuation(i + 1)
            or heading.match(lines[i + 1])
            or lines[i + 1].strip().startswith("```")
        ):
            errors.append(f"{name}:{i + 2}: MD032 列表后缺空行 -> {lines[i + 1].strip()[:50]}")
    return errors


def split_syntax_errors(name: str, lines: list[str]) -> list[str]:
    """原有的围栏与表格列数检查。"""
    errors: list[str] = []
    fences = sum(1 for line in lines if line.strip().startswith("```"))
    if fences % 2 != 0:
        errors.append(f"{name}: 代码围栏未闭合（总数={fences}，应为偶数）")

    in_fence = False
    table_rows: list[tuple[int, int]] = []
    for num, line in enumerate(lines, 1):
        if line.strip().startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        if line.lstrip().startswith("|") and line.rstrip().endswith("|"):
            table_rows.append((num, count_table_columns(line)))
        elif table_rows:
            if len({c for _, c in table_rows}) > 1:
                errors.append(
                    f"{name}: 第 {table_rows[0][0]} 行附近表格列数不一致: {table_rows}"
                )
            table_rows = []
    if table_rows and len({c for _, c in table_rows}) > 1:
        errors.append(f"{name}: 结尾附近表格列数不一致: {table_rows}")
    return errors


# --------------------------------------------------------------------------
# 语义层检查
# --------------------------------------------------------------------------


def parse_contracts(text: str) -> dict[str, tuple[int, str]]:
    """按 `### REQ-*` 小节切出契约块，返回 {编号: (起始行号, 块文本)}。"""
    contracts: dict[str, list[str]] = {}
    starts: dict[str, int] = {}
    current: str | None = None

    for num, line in enumerate(text.splitlines(), 1):
        match = re.match(r"^### (REQ-[A-Z]+-\d+)(?=\s|$)", line)
        if match:
            current = match.group(1)
            starts[current] = num
            contracts[current] = []
            continue
        # 遇到二级标题即离开契约区，避免把汇总章节并入最后一条契约。
        if re.match(r"^##\s", line):
            current = None
            continue
        if current is not None:
            contracts[current].append(line)

    return {cid: (starts[cid], "\n".join(lines)) for cid, lines in contracts.items()}


def check_contract_counts(files: dict[str, str], contracts: dict) -> list[str]:
    """第 6 项：声明的契约数量必须等于实际条目数。"""
    errors: list[str] = []
    actual = len(contracts)
    # 只认总数声明的权威句式；“写入 34 条契约”“16 条契约仍无法”这类分组计数
    # 不是总数声明，不能被当作矛盾报出来。
    patterns = [
        re.compile(r"共\s*\*\*(\d{2,3})\s*条\*\*\s*契约"),
        re.compile(r"v\d+\.\d+（(?:首批\s*)?(\d{2,3})\s*条）"),
        re.compile(r"(\d{2,3})\s*条契约编号保持不变"),
        re.compile(r"已建立\s*(\d{2,3})\s*条契约"),
    ]
    for name, text in files.items():
        for num, line in enumerate(text.splitlines(), 1):
            reported: set[str] = set()
            for pattern in patterns:
                for match in pattern.finditer(line):
                    declared = match.group(1)
                    if declared == str(actual) or declared in reported:
                        continue
                    reported.add(declared)
                    errors.append(
                        f"{name}:{num}: 声明 {declared} 条契约，实际 {actual} 条"
                        f" -> {line.strip()[:60]}"
                    )
    return errors


def check_status_values(contracts: dict) -> list[str]:
    """第 7 项：三维状态取值必须在登记的枚举内。"""
    errors: list[str] = []
    field_re = re.compile(
        r"^-\s+\*\*(lifecycle|implementation|verification)\*\*：\s*`?([a-z-]+)`?"
    )
    for cid, (start, block) in contracts.items():
        for offset, line in enumerate(block.splitlines(), 1):
            match = field_re.match(line)
            if not match:
                continue
            field, value = match.group(1), match.group(2)
            if value not in STATUS_FIELD_VALUES[field]:
                errors.append(
                    f"requirements.md:{start + offset}: {cid} 的 {field}=`{value}` "
                    f"不在取值范围 {sorted(STATUS_FIELD_VALUES[field])}"
                )
    return errors


def check_passed_evidence(contracts: dict) -> list[str]:
    """第 8 项：标 passed 的契约必须给出可定位的执行证据。"""
    errors: list[str] = []
    bare_count = re.compile(r"\d+\s+passed|\d+\s+skipped|\d+\s+条通过")
    for cid, (start, block) in contracts.items():
        match = re.search(
            r"^-\s+\*\*verification\*\*：\s*`passed`", block, re.MULTILINE
        )
        if not match:
            continue
        has_section = "testing.md" in block and re.search(
            r"第\s*1[0-9]\.\d+\s*节", block
        )
        has_commit = re.search(r"HEAD\s*`?[0-9a-f]{7,40}`?", block)
        if bare_count.search(block):
            errors.append(
                f"requirements.md:{start}: {cid} 标 passed 但仍含裸测试数字"
                "（应改为指向 testing.md 基线小节并带 HEAD）"
            )
        elif not (has_section or has_commit):
            errors.append(
                f"requirements.md:{start}: {cid} 标 passed 但证据无法定位到"
                " testing.md 小节或 commit/HEAD"
            )
    return errors


def check_defect_ids(spec_lines: list[str], all_files: dict[str, str]) -> list[str]:
    """第 9 项：缺陷主清单只用 CR-*；旧前缀仅允许出现在映射/废止语境。"""
    errors: list[str] = []
    legacy = re.compile(r"(?<![A-Za-z0-9-])(C\d{1,2}|V-\d{1,2})(?![\w-])")

    for name, text in all_files.items():
        for num, line in enumerate(text.splitlines(), 1):
            for match in legacy.finditer(line):
                if any(word in line for word in LEGACY_ALLOWED):
                    continue
                errors.append(
                    f"{name}:{num}: 仍使用已停用前缀 `{match.group(1)}`，且不在"
                    f"映射/废止语境 -> {line.strip()[:60]}"
                )

    # 主清单 ID 必须是 CR-NNN，且缺号必须声明。
    table_ids: list[str] = []
    in_table = False
    for line in spec_lines:
        if line.startswith("### 10.16"):
            in_table = True
            continue
        if in_table and line.startswith("#### "):
            break
        if in_table:
            cell = re.match(r"^- `(CR-\d{3})`", line)
            if cell:
                table_ids.append(cell.group(1))

    used = {int(i.split("-")[1]) for i in table_ids}
    if used:
        declared_gaps = set()
        joined = "\n".join(spec_lines)
        for gap in re.finditer(r"`CR-00(\d)`", joined):
            declared_gaps.add(int(gap.group(1)))
        for gap in re.finditer(r"`CR-0(0\d|1\d)`", joined):
            declared_gaps.add(int(gap.group(1)))
        for number in range(1, max(used) + 1):
            if number in used or number in declared_gaps:
                continue
            errors.append(
                f"spec.md: CR-{number:03d} 既不在 10.16 主清单，也未在缺号说明中声明"
            )
    return errors


# --------------------------------------------------------------------------
# 仓库交叉检查
# --------------------------------------------------------------------------


def build_test_index(repo: Path) -> tuple[set[str], set[str]]:
    """返回（测试文件相对路径集合，测试内定义的函数/夹具名集合）。"""
    files: set[str] = set()
    names: set[str] = set()
    tests_dir = repo / "tests"
    if not tests_dir.is_dir():
        return files, names
    for path in tests_dir.rglob("*.py"):
        rel = path.relative_to(repo).as_posix()
        files.add(rel)
        try:
            content = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        names.update(re.findall(r"^\s*(?:async\s+)?def\s+(\w+)", content, re.MULTILINE))
    return files, names


def collect_tcs(testing_text: str) -> set[str]:
    """testing.md 中登记过的 TC 编号（含范围展开）。"""
    known: set[str] = set()
    single = re.compile(r"TC-[A-Z]+-\d+")
    for match in single.finditer(testing_text):
        known.add(match.group(0))
    # 展开 TC-EXT-001～TC-EXT-004 这类范围写法。
    span = re.compile(r"(TC-([A-Z]+)-)(\d+)～\s*TC-[A-Z]+-(\d+)")
    for match in span.finditer(testing_text):
        prefix, _domain, lo, hi = match.groups()
        for number in range(int(lo), int(hi) + 1):
            known.add(f"{prefix}{number:03d}")
    return known


def check_repo_traceability(
    contracts: dict, repo: Path, testing_text: str
) -> tuple[list[str], int]:
    """第 10-12 项：验收字段指向的测试入口与 TC 编号是否真实存在。"""
    errors: list[str] = []
    test_files, test_names = build_test_index(repo)
    known_tcs = collect_tcs(testing_text)
    checked = 0

    path_re = re.compile(r"(tests/[A-Za-z0-9_./-]+\.py)")
    tc_re = re.compile(r"TC-[A-Z]+-\d+")
    re.compile(r"`(test_\w+|fixture_\w+|\w+(?=夹具))`")

    for cid, (start, block) in contracts.items():
        lines = [
            line
            for line in block.splitlines()
            if re.match(r"^-\s+\*\*(验收|关联)\*\*", line)
        ]
        for line in lines:
            for match in path_re.finditer(line):
                checked += 1
                rel = match.group(1)
                if rel not in test_files and not (repo / rel).exists():
                    errors.append(
                        f"requirements.md:{start}: {cid} 引用不存在的测试文件 {rel}"
                    )
            for tc in tc_re.findall(line):
                checked += 1
                if tc not in known_tcs:
                    errors.append(
                        f"requirements.md:{start}: {cid} 引用未在 testing.md 登记的用例 {tc}"
                    )
            # 只有没有给出文件路径时才按裸函数名全局查找，避免重复报错。
            if not path_re.search(line):
                for name in re.findall(r"`((?:test|fixture)_\w+)`", line):
                    checked += 1
                    if name not in test_names:
                        errors.append(
                            f"requirements.md:{start}: {cid} 引用的测试入口"
                            f" `{name}` 在仓库测试中未定义"
                        )
    return errors, checked


def check_repo_doc_links(files: dict[str, str]) -> list[str]:
    """README/AGENTS 里以行内代码写的 `flask-exts/...` 仓库路径是否存在。"""
    errors: list[str] = []
    inline = re.compile(r"`(flask-exts/[A-Za-z0-9_./-]+)`")
    for name, text in files.items():
        for num, line in enumerate(text.splitlines(), 1):
            for match in inline.finditer(line):
                rel = match.group(1)[len("flask-exts/") :]
                if not (REPO / rel).exists():
                    errors.append(
                        f"{name}:{num}: 引用的仓库文件不存在 -> {match.group(1)}"
                    )
    return errors


# --------------------------------------------------------------------------
# 派生数据核对（纯只读门禁：校对不一致仅报错，严禁写入文档）
# --------------------------------------------------------------------------

CLOSED_RE = re.compile(r"已(?:在[^）)]*?)?(?:修复|关闭|删除|废止)")


def defect_closed(severity: str) -> bool:
    """“部分修复”按 AGENTS.md 第 5.7.4 节不算闭环。"""
    if "部分" in severity:
        return False
    return bool(CLOSED_RE.search(severity))


def collect_open_defects(files: dict[str, str]) -> dict[str, str]:
    """从两份缺陷主清单（列表形式）收集仍未闭环的缺陷编号。"""
    open_ids: dict[str, str] = {}
    specs = (
        ("spec.md", r"^- `(CR-\d{3})`", "严重度"),
        ("security.md", r"^- `(SEC-\d{2})`", "等级"),
    )
    for name, pattern, severity_key in specs:
        current: str | None = None
        for line in files.get(name, "").splitlines():
            match = re.match(pattern, line)
            if match:
                current = match.group(1)
                continue
            if current is None:
                continue
            detail = re.match(rf"^  - {severity_key}：(.+)$", line)
            if detail:
                severity = detail.group(1).strip()
                if not defect_closed(severity):
                    open_ids[current] = severity
                current = None
    return open_ids


def contract_stats(contracts: dict) -> tuple[int, int, int, int]:
    """返回（总数, approved 且 passed, 未取证, 已停用）。"""
    retired = verified = 0
    for _start, block in contracts.values():
        life = re.search(r"^- \*\*lifecycle\*\*：`([a-z-]+)`", block, re.MULTILINE)
        ver = re.search(r"^- \*\*verification\*\*：`([a-z]+)`", block, re.MULTILINE)
        state = life.group(1) if life else "unknown"
        if state in ("superseded", "deprecated"):
            retired += 1
            continue
        if state == "approved" and ver and ver.group(1) == "passed":
            verified += 1
    total = len(contracts)
    return total, verified, total - retired - verified, retired


def count_gaps(gaps_text: str) -> dict[str, int]:
    """统计 gaps.md 各级缺口条目数。"""
    counts: dict[str, int] = {}
    section = None
    for line in gaps_text.splitlines():
        match = re.match(r"^### (P[012])：", line)
        if match:
            section = match.group(1)
            counts[section] = 0
            continue
        if re.match(r"^#{2,3}\s", line):
            section = None
            continue
        if section and re.match(r"^- \*\*P[012]-\d+\*\*$", line):
            counts[section] += 1
    return counts


def check_metadata_snapshots(files: dict[str, str]) -> list[str]:
    """核对数据快照只出现在 release.md，且恰好一条。"""
    errors: list[str] = []
    for name, text in files.items():
        rows = re.findall(r"^> 数据快照：", text, re.MULTILINE)
        if name == "release.md":
            if len(rows) != 1:
                errors.append(
                    f"release.md: 必须有且只有一条数据快照，实际 {len(rows)} 条"
                )
        elif rows:
            errors.append(f"{name}: 数据快照只允许在 release.md 维护")
    return errors


def check_status_blocks(files: dict[str, str], contracts: dict) -> list[str]:
    """第 14 项：只读核对头部置顶清单数据；不一致仅报错阻断，严禁自动写入。"""
    errors: list[str] = []

    # 核对 requirements.md 头部契约进度清单
    req_text = files.get("requirements.md", "")
    actual = contract_stats(contracts)
    m_total = re.search(r"^- \*\*契约总数\*\*：(\d+) 条", req_text, re.MULTILINE)
    m_ver = re.search(
        r"^- \*\*已批准且验证通过[^\n]*?\*\*：(\d+) 条", req_text, re.MULTILINE
    )
    m_unver = re.search(r"^- \*\*未取证[^\n]*?\*\*：(\d+) 条", req_text, re.MULTILINE)
    m_ret = re.search(r"^- \*\*已停用[^\n]*?\*\*：(\d+) 条", req_text, re.MULTILINE)

    if not (m_total and m_ver and m_unver and m_ret):
        errors.append("requirements.md: 头部缺少完整的契约进度指标条目")
    else:
        parsed = (
            int(m_total.group(1)),
            int(m_ver.group(1)),
            int(m_unver.group(1)),
            int(m_ret.group(1)),
        )
        if parsed != actual:
            errors.append(
                f"requirements.md: 契约进度清单 {parsed} 与当前实算 {actual} 不一致，请依据文档规则人工修正"
            )

    # 核对 README.md 头部文档集健康度清单
    readme_text = files.get("README.md", "")
    opens = collect_open_defects(files)
    cr = sum(1 for key in opens if key.startswith("CR"))
    sec = sum(1 for key in opens if key.startswith("SEC"))
    gaps = count_gaps(files.get("gaps.md", ""))
    want_defects = f"CR {cr} · SEC {sec}"
    want_gaps = f"{gaps.get('P0', 0)} / {gaps.get('P1', 0)} / {gaps.get('P2', 0)}"

    m_defects = re.search(
        r"^- \*\*未闭环缺陷\*\*：([^\n]+)$", readme_text, re.MULTILINE
    )
    m_gaps = re.search(
        r"^- \*\*当前缺口[^\n]*?\*\*：([^\n]+)$", readme_text, re.MULTILINE
    )

    if not (m_defects and m_gaps):
        errors.append("README.md: 头部缺少完整的文档集健康度指标条目")
    else:
        if want_defects not in m_defects.group(1):
            errors.append(
                f"README.md: 健康度清单中未闭环缺陷（{m_defects.group(1).strip()}）与实算（{want_defects}）不一致"
            )
        if want_gaps not in m_gaps.group(1):
            errors.append(
                f"README.md: 健康度清单中缺口统计（{m_gaps.group(1).strip()}）与实算（{want_gaps}）不一致"
            )
    return errors


def main() -> int:
    errors: list[str] = []
    files = {
        src.name: src.read_text(encoding="utf-8") for src in sorted(ROOT.glob("*.md"))
    }
    anchor_cache: dict[Path, set[str]] = {}
    skipped_repo_links = 0

    for name, text in files.items():
        lines = text.splitlines()
        errors.extend(split_syntax_errors(name, lines))
        errors.extend(check_structure(name, lines))
        errors.extend(check_markdown_lint(name, lines))

        for num, line in enumerate(lines, 1):
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
                    dst = (ROOT / raw_path).resolve()
                else:
                    dst = ROOT / name

                if not dst.exists():
                    errors.append(f"{name}:{num}: 目标文件不存在 -> {raw_path or raw}")
                    continue

                frag = unquote(parsed.fragment)
                if frag and dst.suffix.lower() == ".md":
                    if dst not in anchor_cache:
                        anchor_cache[dst] = collect_anchors(dst)
                    if frag not in anchor_cache[dst]:
                        errors.append(
                            f"{name}:{num}: 文件 {dst.name} 中缺少锚点 #{frag}"
                        )

    # 语义层
    req_text = files.get("requirements.md", "")
    contracts = parse_contracts(req_text)
    errors.extend(check_contract_counts(files, contracts))
    errors.extend(check_status_values(contracts))
    errors.extend(check_passed_evidence(contracts))
    errors.extend(check_defect_ids(files.get("spec.md", "").splitlines(), files))
    errors.extend(check_metadata_snapshots(files))
    errors.extend(check_status_blocks(files, contracts))

    # 仓库交叉层
    repo_checked = 0
    if REPO is not None:
        repo_errors, repo_checked = check_repo_traceability(
            contracts, REPO, files.get("testing.md", "")
        )
        errors.extend(repo_errors)
        errors.extend(check_repo_doc_links(files))

    if errors:
        print(f"自检失败，共发现 {len(errors)} 处问题：", file=sys.stderr)
        for err in errors:
            print(f"  - {err}", file=sys.stderr)
        return 1

    print(
        f"自检通过！已核验 {len(files)} 份文档：代码围栏、表格列数、相对路径和内部锚点全部有效。"
    )
    print("结构性检查通过：标题空格、标题粘连与编号层级均正常。")
    print(
        f"语义层检查通过：契约 {len(contracts)} 条、状态取值与 passed 证据一致，"
        "缺陷编号无停用前缀残留。"
    )
    if REPO is not None:
        print(
            f"仓库交叉检查通过：核验测试入口/用例引用 {repo_checked} 处（仓库 {REPO}）。"
        )
    else:
        print("未设置 FLASK_EXTS_REPO：跳过测试入口与仓库文件存在性校验。")
    if skipped_repo_links:
        print(
            f"另有 {skipped_repo_links} 个 `flask-exts/` Markdown 链接未校验；"
            "设置 FLASK_EXTS_REPO 后可校验。"
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
