# Flask-Exts 测试方案（Test-Driven）

> 本文是 [`spec.md`](./spec.md) 的**测试驱动配套文档**，独立维护。
>
> | 项目 | 内容 |
> | --- | --- |
> | 文档版本 | v0.1（工作稿） |
> | 状态 | 工作稿 |
> | 最后更新 | 2026-11-11 |
> | 数据快照 | 2026-11-11（发布版本 `0.4.1`；HEAD `03006024d21167c0f6285a5724a3be5ef24d9a59`；测试清单和统计已复核） |
> | 适用仓库 | `flask-exts` |
> | 文档驱动 | `architecture.md`：架构；`spec.md`：设计和实现，第 10 章涵盖 View/Admin 路由、ModelView、DataBackend、Inline、AJAX、导出 |
> | 行为契约 | `requirements.md`：`REQ-*`、验收标准、追溯 |
> | 测试驱动 | `testing.md`（本文）：测试策略、用例、执行计划、质量门禁 |
> | 安全治理 | `security.md`：威胁模型、控制措施、风险清单、发布检查 |
>
> **文档状态说明**：本文的测试目录与数量以 2026-11-11 的 HEAD `03006024d21167c0f6285a5724a3be5ef24d9a59`（发布版本 `0.4.1`）为基线。当前仓库没有 `tests/e2e/`、`tests/performance/`，源码/测试中未发现 `mail_outbox`；这些仍属目标结构。凡标“待补”“待修”“目标”“规划”的内容，均需按第 12 节分阶段实施后再视为已落地。重新统计现状的方法见 1.5。
>
> **使用方式**：修改代码前先对照 `requirements.md` 确认行为契约，再查相关架构/安全/领域约束；按变更设计测试并尽可能先验证失败，修改后运行实际可用的项目检查。缺陷修复优先复现并先写失败测试。本文中标记为目标的规划不代表已实现；当前 CI 实现范围见第 11 节。

## 目录

- [0. 快速开始](#0-快速开始)
- [1. 测试现状盘点](#1-测试现状盘点)
- [2. 测试策略与分层](#2-测试策略与分层)
- [3. 测试目录与标记规划](#3-测试目录与标记规划)
- [4. Fixtures 设计规范](#4-fixtures-设计规范)
- [5. 测试数据与工厂](#5-测试数据与工厂)
- [6. 测试覆盖矩阵](#6-测试覆盖矩阵)
- [7. 详细测试用例设计](#7-详细测试用例设计)
- [8. 端到端测试方案](#8-端到端测试方案)
- [9. 性能测试方案](#9-性能测试方案)
- [10. 覆盖率与质量门禁](#10-覆盖率与质量门禁)
- [11. CI 流水线](#11-ci-流水线)
- [12. 分阶段执行计划](#12-分阶段执行计划)
- [13. 测试目标与现状对照](#13-测试目标与现状对照)
- [14. 测试债务与改进清单](#14-测试债务与改进清单)
- [15. 测试编写规范与检查清单](#15-测试编写规范与检查清单)
- [16. 验收标准](#16-验收标准)
- [17. 文档维护与更新](#17-文档维护与更新)

## 0. 快速开始

### 0.1 环境准备

以下命令在用户确认的仓库根目录执行；仓库位置每轮任务开始时确认，不假定固定路径。按仓库 `AGENTS.md` 使用 uv 管理的项目内虚拟环境，不要全局安装：

```bash
uv sync
```

`uv sync` 会自动创建/更新项目内 `.venv`，安装运行时依赖及 `dev` 依赖组；该组包含测试工具与文档构建依赖（`docs` 组）。未激活虚拟环境时，后续命令统一使用 `uv run` 前缀（例如 `uv run pytest -q`）；本文其余小节沿用已激活环境下的 `python -m ...` 写法。

文档构建依赖已包含在 `dev` 组中，无需单独安装。

### 0.2 第一条命令

```bash
# 全量测试
uv run pytest -q

# 只跑某个文件
uv run pytest -q tests/unit/datastore/sqla/test_query.py

# 只跑某个目录
uv run pytest -q tests/integration/admin

# 带覆盖率
uv run coverage run -m pytest -q
uv run coverage report -m
```

安全相关测试入口（路径与可执行性需结合仓库当前状态核实）：

```bash
uv run pytest -q tests/unit/security
uv run pytest -q tests/integration/security
uv run pytest -q tests/integration/usercenter/test_user_view.py
uv run pytest -q tests/unit/forms/form/test_form.py
```

> 当前 `pyproject.toml` 已开启 `--strict-markers`。在 3.3 的 markers 尚未注册前，不要使用 `-m unit` 这类命令，否则 pytest 会直接报错。
>
> 项目级 pytest 配置已将 `DeprecationWarning` 视为错误；修复行为或依赖问题，不要在单个测试中过滤告警。

### 0.3 本文阅读顺序

| 角色 | 建议顺序 |
| --- | --- |
| 第一次接触项目 | 0 → 1 → 2 → 3 → 4 |
| 要写新测试 | 4 → 5 → 6 → 7 → 15 |
| 要补 E2E / 性能 | 8 → 9 → 11 → 12 |
| 要做质量门禁 | 10 → 11 → 16 |
| 要修缺陷 | 相关契约与问题清单（`spec.md` 第 10.16 节 / `security.md` 第 11 节）→ 本文 7 → 12 |

### 0.4 状态图例

| 标记 | 含义 |
| --- | --- |
| 现有 | 当前仓库已有测试 |
| 待补 | 尚无测试，需要新增 |
| 待修 | 已有测试但断言不足或未触发缺陷 |
| 目标 | 目标结构，当前未落地 |
| 规划 | 尚未进入执行计划 |

## 1. 测试现状盘点

### 1.1 当前规模

| 指标 | 当前值 | 说明 |
| --- | --- | --- |
| 测试文件 | 47 个 `test_*.py` | 全部位于 `tests/unit/` 与 `tests/integration/` |
| 测试函数 | 210 个 | 以 `def test_...` 统计 |
| 断言 | 约 950 处 | 以 `assert` 统计，不含 `pytest.raises` 等 |
| 测试框架 | pytest | `pyproject.toml` 配置 |
| 覆盖率工具 | `pytest-cov` / `coverage` | 已列入 `dev` 组；已测定基线，CI 每轮报告覆盖率，尚无 `fail-under` 门槛 |
| E2E 目录 | 无 | `tests/e2e/` 尚未创建 |
| 性能目录 | 无 | `tests/performance/` 尚未创建 |
| 浏览器测试 | 无 | 未引入 Selenium/Playwright |
| 基准工具 | 无 | 未引入 `pytest-benchmark` |
| 数据工厂 | 无 | 未引入 `factory-boy` / `faker` |
| 最近完整测试运行 | 245 passed, 1 skipped | 2026-11-11；Python 3.13.5；HEAD `03006024d21167c0f6285a5724a3be5ef24d9a59`（发布版本 `0.4.1`）；跳过 `test_smtp.py`，未配置 `REAL_EMAIL_SENDER` |

`pyproject.toml` 当前 pytest 配置：

```toml
[tool.pytest.ini_options]
minversion = "8.0"
testpaths = ["tests"]
addopts = "-ra --strict-markers --strict-config"
```

注意 `--strict-markers`：**新增 marker 必须注册**，否则测试会直接报错。

### 1.2 现有测试分布

| 区域 | 测试函数数 | 主要文件 | 评价 |
| --- | ---: | --- | --- |
| `integration/admin` | 53 | 完整入口见 1.2.1 | 历史快照覆盖 CRUD、Inline、搜索、排序、分页、批量操作、导出、复合主键；现状待核实 |
| `unit/extension_core` | 30 | `test_registry.py`、`test_manager.py` | 覆盖依赖排序、循环依赖、幂等、关闭、内置扩展装配 |
| `unit/admin` | 19 | `test_mockview.py`、`test_type_formatters.py`、`test_admin.py`、`test_view.py` | 覆盖视图元数据与格式化，偏“配置读取” |
| `unit/forms` | 23 | `test_json.py`、`test_datetime.py`、`test_filefield.py`、`test_uploadfile.py`、`test_select.py`、`test_wtforms.py`、`tests/unit/forms/form/test_form.py` | 覆盖字段、文件、选择字段、CSRF 生成/校验、派生密钥和关闭配置；边界与错误路径仍可补 |
| `integration/usercenter` | 14 | `tests/integration/usercenter/test_user_view.py` | 覆盖注册、重复邮箱、改邮箱确认/密码/非法地址、重发验证、登录前置、TFA 启用/关闭/登录/防绕过、inactive 账号、改密码、找回/重置、恢复码 |
| `unit/datastore` | 14 | `test_db.py`、`test_query.py` | 覆盖单例、重绑定、内存 SQLite、JOIN 复用、类型推断；计数正确性未覆盖 |
| `unit/security` | 9 | `tests/unit/security/test_authorizer.py`、`tests/unit/security/test_tfa.py`、`tests/unit/security/test_urls.py` | 授权包括 admin、普通用户、无角色/无用户、`allow_access` 和 `role_need`；TFA 涉及 URI、生成/校验；URL 涉及外部/畸形拒绝和本地路径放行 |
| `integration/builtin_extensions` | 8 | `test_login.py`、`test_admin_views.py` | 覆盖 JWT、蓝图、默认视图 |
| `unit/builtin_extensions` | 8 | `test_babel.py`、`test_exts.py`、`test_frontend.py` | 覆盖 Babel、扩展注册、Jinja 全局 |
| `integration/security` | 5 | `tests/integration/security/test_core.py` | 覆盖密钥派生、哈希、序列化、邮箱验证、重置密码、密码变更使 session 失效 |
| `integration/userstore` | 3 | `test_sqla_userstore.py` | 覆盖模型注册、基础 CRUD、角色；`get_users`/`remove_user` 未覆盖 |
| `unit/emailer` | 2 | `test_base.py`、`test_smtp.py` | 仅基础路径；错误路径与默认发送器未覆盖 |
| `unit/frontend` | 9 | `test_plugin_manager.py`、`test_base.py`、宏测试 | 覆盖注册、排序、循环依赖、资源拼接 |
| `commands` | 0 | 无 | CLI 完全未测试 |

#### 1.2.1 Admin 测试文件清单

以下文件路径已与 2026-11-11 的仓库 HEAD 及当前工作树核对；各文件的断言覆盖未逐项审计。文件名不证明相关断言存在或测试通过。

- `tests/integration/admin/sqla/test_views.py`
- `tests/integration/admin/sqla/test_forms.py`
- `tests/integration/admin/sqla/test_search.py`
- `tests/integration/admin/sqla/test_sorting.py`
- `tests/integration/admin/sqla/test_translation.py`
- `tests/integration/admin/sqla/test_pagination.py`
- `tests/integration/admin/sqla/test_actions.py`
- `tests/integration/admin/sqla/test_export.py`
- `tests/integration/admin/sqla/test_inline_forms.py`
- `tests/integration/admin/sqla/test_inline_views.py`
- `tests/integration/admin/sqla/test_inline_ajax.py`
- `tests/integration/admin/sqla/test_ajax.py`
- `tests/integration/admin/sqla/test_primary_keys.py`

### 1.3 主要缺口

| 缺口 | 影响 | 对应目标 |
| --- | --- | --- |
| 无 HTTP 级 E2E 流程测试 | 跨模块流程（注册→验证→登录→TFA）只能靠零散集成测试拼接 | 目标见第 13 节 |
| 无性能基准 | 无法量化列表查询、搜索、渲染、认证的退化 | 目标见第 13 节 |
| 覆盖率无 CI 门槛 | 覆盖率回退无法自动阻断 | 基线见第 10.5 节；`ci.yml` 已报告覆盖率，门槛见第 10.3 节 |
| CI 未检查本套 Markdown 与 demo smoke | 外部文档死链、demo 启动问题不会被现有 CI 捕获 | 仓库 Sphinx 构建与测试 CI 已在 `docs.yml` / `ci.yml`；本套文档的链接检查与 demo smoke 仍待接入 |
| 一对多搜索计数未断言 | `build_count` 重复计数风险可能潜伏 | 新增 |
| Inline + AJAX 外键未覆盖 | `create_ajax_loader` 参数缺陷可能未被触发 | 新增 |
| `UserStore.get_users` / `remove_user` 未覆盖 | 接口契约与实现不一致 | 新增 |
| CLI 未覆盖 | 建表/建用户命令回归无保护 | 新增 |
| 安全令牌过期测试被注释 | 过期路径没有自动化保护 | 新增 |
| `mail_data` 模块级全局 | 测试顺序/并行敏感 | 测试隔离 |
| 无浏览器/JS 测试 | 前端插件、Tom Select、模态框等只能人工验证 | 可选 |

### 1.4 与目标基线的差距

目标、当前状态与差距统一见第 13 节，本节不重复指标。当前优先事项为 E2E、性能基线，以及覆盖率门槛（`ci.yml` 已报告覆盖率，尚未设置 `fail-under`）；阶段行动见第 12 节。

### 1.5 数据快照与重新统计

本文的 47 / 210 / 950 已按 2026-11-11 的 HEAD `03006024d21167c0f6285a5724a3be5ef24d9a59`（发布版本 `0.4.1`）重新统计。统计是文本近似值；代码更新后应重新运行以下脚本：

```bash
python - <<'PY'
import re
from collections import Counter
from pathlib import Path

files = funcs = asserts = 0
areas = Counter()
for path in sorted(Path("tests").rglob("test_*.py")):
    text = path.read_text(encoding="utf-8")
    n = len(re.findall(r"^\s*(?:async\s+)?def test_", text, re.M))
    files += 1
    funcs += n
    asserts += len(re.findall(r"\bassert\b", text))
    area = "/".join(path.parts[1:3]) if len(path.parts) > 2 else path.parts[1]
    areas[area] += n

print(f"files={files} funcs={funcs} asserts={asserts}")
for area, n in areas.most_common():
    print(f"{n:4d}  {area}")
PY
```

更新本文时，同步修改 1.1、1.2 的数字和顶部“数据快照”日期。

**统计口径：**

- 文件：`tests/**/test_*.py`
- 用例：行首 `def test_`（含 `async def test_`）
- 断言：文本中的 `assert` 关键字，不含 `pytest.raises` 的隐式断言
- 限制：按文本匹配，可能计入注释或字符串中的 `assert`；数量不代表有效断言数或测试质量。

## 2. 测试策略与分层

### 2.1 测试金字塔

```text
                 ┌─────────────────────┐
                 │  Browser E2E (可选) │  少量、慢、验证真实 UI/JS
                 ├─────────────────────┤
                 │  HTTP E2E           │  跨模块用户旅程
                 ├─────────────────────┤
                 │  Integration        │  Flask + DB + 组件协作
                 ├─────────────────────┤
                 │  Unit               │  纯逻辑、快速、隔离
                 └─────────────────────┘
```

建议比例（按数量，不按运行时间）：

| 层级 | 建议占比 | 运行时间 | 依赖 |
| --- | ---: | --- | --- |
| Unit | ~55% | < 5s | 无 Flask 或最小 app |
| Integration | ~30% | < 60s | Flask app + 内存 SQLite |
| HTTP E2E | ~10% | < 60s | Flask test client + 邮件捕获 |
| Browser E2E | ~3% | 分钟级 | 浏览器 + 运行中的服务 |
| Performance | ~2% | 分钟级 | 大数据集 + benchmark |

### 2.2 各层职责

| 层级 | 测什么 | 不测什么 |
| --- | --- | --- |
| Unit | 纯函数、Query 构造、格式化器、插件排序、Registry 状态机、密钥/哈希/序列化 | 路由、模板、数据库提交 |
| Integration | 视图 + 表单 + DB + 扩展协作；HTTP 状态码与页面关键内容 | 真实浏览器、外部 SMTP、跨进程 |
| HTTP E2E | 完整用户旅程：注册→验证→登录→TFA→资料→登出；Admin CRUD | 像素级 UI、JS 交互 |
| Browser E2E | JS 插件、Tom Select、模态框、日期选择器、响应式布局 | 业务规则（已由下层覆盖） |
| Performance | 查询次数、查询耗时、渲染耗时、内存增长 | 正确性（由功能测试覆盖） |

### 2.3 测试原则

1. **一个测试只验证一个行为**，失败时能直接定位。
2. **Arrange–Act–Assert** 结构清晰。
3. **确定性**：不依赖当前时间、随机数、网络、执行顺序。
4. **隔离性**：每个测试独立建数据、独立清理；不共享模块级可变状态。
5. **可读性**：测试名描述“条件 + 行为 + 期望”。
6. **断言最终状态**：不仅断言状态码，还断言数据库/响应关键内容。
7. **错误路径优先**：安全、权限、边界、异常路径至少与成功路径同等重要。
8. **快慢分离**：性能/浏览器测试用 marker 标记，默认不跑。
9. **证据分离**：测试设计、测试代码存在、成功收集和执行通过分别记录，任何一步都不能由上一阶段推定。
10. **防止自证**：先从契约设计预期和错误路径，再检查实现；不以当前实现输出倒推期望，不通过放宽断言、删除或跳过测试消除失败。适用时由未参与实现的人员复核关键断言。
11. **真实边界**：Mock 只替代可控的外部边界，记录未覆盖的真实行为；涉及事务、权限、浏览器交互或协议兼容时，按风险补充真实或隔离环境验证。

新增行为和缺陷优先先运行针对性测试并记录预期失败，再实施修复并确认转绿。若失败阶段无法运行或现有测试已能稳定复现，记录原因与实际证据，不伪称已完成先红；完成后还需运行受影响的回归检查。

### 2.4 并行、顺序与 flaky 处理

当前测试默认串行执行，且存在模块级 `mail_data` 这类顺序敏感状态。目标状态：

| 能力 | 工具 | 是否已有 | 建议 |
| --- | --- | --- | --- |
| 并行执行 | `pytest-xdist` | 否 | 可选；先消除模块级可变状态 |
| 随机顺序 | `pytest-randomly` | 否 | 可选；用于暴露顺序依赖 |
| 超时保护 | `pytest-timeout` | 否 | 可选；防止挂起 |
| 失败重试 | `pytest-rerunfailures` | 否 | **不推荐**作为常规手段 |

规则：

1. 每个测试自己造数据、自己清理，不依赖前一个测试的残留状态。
2. 不使用模块级可变容器收集状态；改用 function-scope fixture。
3. 用户名/邮箱/主键使用唯一值（测试名前缀 + 序号）。
4. 不依赖当前时间；过期逻辑用显式时间或 `monkeypatch`。
5. 不依赖字典/集合迭代顺序；需要顺序时显式排序。
6. 不访问网络、真实 SMTP、外部服务。
7. flaky 测试先定位根因；确需隔离时加 `@pytest.mark.skip(reason="issue #...")` 并登记，而不是自动重试。

引入 `pytest-xdist` 前，先确认所有测试在随机顺序下都能通过；引入后，带数据库状态的测试必须保持 function scope。

## 3. 测试目录与标记规划

### 3.1 当前目录

```text
tests/
├── __init__.py
├── conftest.py                 # 全局 app/client fixtures
├── blackhole.py                # 测试辅助
├── dummypostdata.py            # 测试辅助
├── tmp/                        # 临时输出（含 .gitignore）
├── translations/               # i18n 测试用翻译
│   ├── messages.pot
│   ├── en/LC_MESSAGES/
│   └── zh_CN/LC_MESSAGES/
├── unit/
│   ├── admin/
│   │   └── model/
│   ├── builtin_extensions/
│   ├── datastore/sqla/
│   ├── emailer/
│   ├── extension_core/
│   ├── forms/
│   │   ├── fields/
│   │   └── form/
│   ├── frontend/
│   │   └── macros/
│   └── security/
└── integration/
    ├── admin/
    │   ├── model/
    │   └── sqla/
    │       └── models/
    ├── builtin_extensions/
    ├── data/                   # 上传测试用图片等静态数据
    ├── security/
    ├── tmp/                    # 上传/导出临时目录（运行时生成）
    ├── usercenter/
    └── userstore/
```

### 3.2 目标目录（分阶段落地）

```text
tests/
├── conftest.py                 # 全局 app/client/db fixtures
├── fixtures/                   # 新增：数据构造器与工厂
│   ├── __init__.py
│   ├── models.py               # AdminTestModel 等测试模型
│   └── factories.py            # user_factory / admin_user_factory
├── unit/
│   ├── extension_core/
│   ├── datastore/
│   ├── admin/
│   ├── forms/
│   ├── security/
│   ├── userstore/              # 补：get_users/remove_user
│   ├── emailer/
│   └── frontend/
├── integration/
│   ├── admin/
│   ├── security/
│   ├── usercenter/
│   ├── userstore/
│   └── builtin_extensions/
├── e2e/                        # 新增：HTTP 级用户旅程
│   ├── conftest.py
│   ├── test_auth_flow.py
│   ├── test_admin_flow.py
│   └── test_password_reset_flow.py
├── performance/                # 新增：基准与 N+1
│   ├── conftest.py
│   ├── test_query_perf.py
│   ├── test_render_perf.py
│   └── test_n_plus_one.py
└── browser/                    # 可选：真实浏览器
    ├── conftest.py
    └── test_ui_flow.py
```

> 注意：`e2e/`、`performance/`、`browser/` 是**目标结构**，当前尚未创建。创建时应同步更新 `pyproject.toml` 的 markers 与 CI。

### 3.3 Marker 规划

在 `pyproject.toml` 中注册：

```toml
[tool.pytest.ini_options]
minversion = "8.0"
testpaths = ["tests"]
addopts = "-ra --strict-markers --strict-config"
markers = [
  "unit: fast, isolated tests",
  "integration: Flask/DB integration tests",
  "e2e: HTTP-level end-to-end tests",
  "browser: requires a real browser",
  "performance: benchmark or resource tests",
  "slow: long-running tests",
]
```

使用方式：

```python
@pytest.mark.unit
def test_registry_dependency_order(): ...

@pytest.mark.integration
def test_admin_list_pagination(app, client, admin): ...

@pytest.mark.e2e
def test_signup_verify_login(app, client, mail_outbox): ...

@pytest.mark.performance
@pytest.mark.slow
def test_list_query_performance(benchmark, seeded_db): ...
```

常用命令：

```bash
# 默认：只跑 unit + integration
python -m pytest -q -m "not performance and not browser"

# 只跑 E2E
python -m pytest -q -m e2e

# 只跑性能
python -m pytest -q -m performance

# 只跑某个模块
python -m pytest -q tests/integration/admin
```

### 3.4 文件命名与放置规则

| 规则 | 说明 |
| --- | --- |
| 文件名 | `test_<主题>.py`；一个文件聚焦一个模块或一个流程 |
| 测试函数 | `test_<条件>_<行为>_<期望>` |
| 类 | 只在需要共享 fixture/参数化时使用 `TestXxx`，不要用它隐藏测试 |
| 放置 | 纯逻辑放 `unit/`；涉及 Flask app/DB/路由放 `integration/`；跨模块旅程放 `e2e/`；基准放 `performance/` |
| 测试模型 | 放对应目录的 `models/` 或 `tests/fixtures/models.py`，不要在生产模块中定义 |
| 静态数据 | 上传/导出素材放 `tests/integration/data/`；运行时产物放 `tests/tmp/` 或 `tmp_path` |
| 翻译 | i18n 测试用 `tests/translations/`，不要复用生产翻译目录 |

### 3.5 数据库与运行环境矩阵

当前所有测试使用内存 SQLite（`sqlite://`）。这对速度有利，但不能覆盖生产数据库差异：

| 维度 | SQLite（当前） | PostgreSQL | MySQL/MariaDB |
| --- | --- | --- | --- |
| 大小写敏感 | 默认不敏感 | 敏感 | 取决于 collation |
| `LIKE` 行为 | 默认不区分大小写 | 区分大小写 | 取决于 collation |
| 外键约束 | 默认关闭，需 `PRAGMA foreign_keys=ON` | 默认开启 | 默认开启 |
| 并发/锁 | 单写者 | MVCC | MVCC/表锁 |
| `count` + JOIN | 同样会重复计数 | 同 | 同 |
| 日期/时区 | 文本存储 | 原生类型 | 原生类型 |

建议：

1. **日常开发**：继续用 SQLite，保持测试快速。
2. **合并前/夜间**：至少用 PostgreSQL 跑一遍 `integration/`，重点覆盖 C2（一对多计数）、外键、大小写搜索。
3. **SQLite 外键测试**：在 fixture 中执行 `PRAGMA foreign_keys=ON`，否则级联/约束测试会“假通过”。
4. **数据库差异**：不要把“SQLite 下通过”当作“生产等价”；涉及 `LIKE`、排序、`NULL` 排序的断言要显式。

> 多数据库矩阵属于目标能力，当前未配置。引入时需要新增依赖与 CI service，先按 `AGENTS.md` 询问。

## 4. Fixtures 设计规范

### 4.1 当前全局 fixtures

`tests/conftest.py`：

```python
@pytest.fixture
def app():
    app = Flask(__name__)
    app.config.update(TESTING=True, SECRET_KEY="test_key")
    app.config["BABEL_ACCEPT_LANGUAGES"] = "en;zh;fr;de;ru"
    app.config["BABEL_DEFAULT_TIMEZONE"] = "Asia/Shanghai"
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite://"
    app.config["CSRF_ENABLED"] = False
    app.config["JWT_SECRET_KEY"] = "SHA256_SECRET_KEY_RECOMMENDED_32_BYTES"
    app.config["JWT_HASH"] = "HS256"

    exts = ExtensionManager()
    exts.init_app(app)
    yield app
    with app.app_context():
        exts.shutdown()
```

特点：

- `sqlite://` 内存数据库
- 默认关闭 CSRF，简化表单测试
- teardown 调用 `exts.shutdown()` → `db.dispose()`
- 每个测试一个 app，避免单例重绑定

### 4.2 建议新增的 fixtures

| Fixture | 作用域 | 状态 | 作用 |
| --- | --- | --- | --- |
| `app` | function | 现有 | 每个测试独立 app |
| `client` | function | 现有 | `app.test_client()` |
| `admin` | function | 现有 | `integration/admin/conftest.py`，返回 Admin 实例 |
| `login_as_admin` | function | 现有 | 可调用 fixture，在 `db.reset_all()` 后创建并登录 admin |
| `sqla_view_factory` | function | 现有 | 构造 `MockSqlaView` |
| `db_setup` | function | 待补 | 在 app context 内 `db.reset_all()`，结束时 `db.session.remove()` |
| `user_factory` | function | 待补 | 创建用户，支持 `username/password/email/is_active/roles` |
| `admin_user` | function | 待补 | 创建激活的 admin 角色用户 |
| `authenticated_client` | function | 待补 | 已登录的 `client`（session 注入或走登录路由） |
| `admin_client` | function | 待补 | 已登录且具备 admin 角色的 client |
| `mail_outbox` | function | 待补 | 捕获邮件数据，替代模块级 `mail_data` |
| `csrf_client` | function | 待补 | 开启 CSRF 的 client，并提供取 token 的辅助 |
| `query_counter` | function | 待补 | 统计当前 app 引擎的 SQL 次数，用于 N+1 检测 |
| `seeded_db` | function | 待补 | 预置 100/1000/10000 条数据，供性能测试 |
| `app_factory` | function | 待补 | 创建独立 app，用于多 app/重绑定测试 |
| `tmp_upload_dir` | function | 待补 | 基于 `tmp_path` 的上传目录，测试后自动清理 |

> “待补”表示本文给出设计，但仓库尚未实现。落地顺序见第 12 节 Phase 0。

### 4.3 `mail_outbox` 设计（替换 `mail_data`）

当前 `tests/integration/usercenter/test_user_view.py` 使用模块级：

```python
mail_data = []

class EmailSender(Sender):
    def send(self, data):
        mail_data.append(data)
```

建议改为：

```python
@pytest.fixture
def mail_outbox(app):
    outbox = []

    class CapturingSender(Sender):
        def send(self, data):
            outbox.append(data)

    with app.app_context():
        emailer = app.extensions["exts"].get_extension("emailer").get_emailer()
        # register_sender 在名称已存在时会抛 ValueError（例如应用配置了
        # NOREPLY_EMAIL_SENDER）。测试中先移除再注册，保证 fixture 可重复使用。
        # 注意：email_change 复用了 verify_email 的 sender/type，不需要单独注册。
        for name in ("verify_email", "reset_password"):
            emailer.senders.pop(name, None)
            emailer.register_sender(name, CapturingSender())

    yield outbox
    outbox.clear()
```

使用：

```python
def last_email(outbox, type_):
    matches = [data for data in outbox if data.get("type") == type_]
    assert matches, f"no email of type {type_!r}: {[d.get('type') for d in outbox]}"
    return matches[-1]


def test_signup_sends_verification(app, client, mail_outbox):
    ...
    email = last_email(mail_outbox, "verify_email")
    assert email["email"] == "user@example.com"
    assert "token=" in email["verification_link"]
```

优点：每个测试独立 outbox，可重排、可并行、失败信息更清晰。

> 邮件 `data` 的字段契约见 7.12。`verify_email` 用 `verification_link` + `verification_token`，`reset_password` 用 `reset_password_link` + `reset_password_token`；两者都带 `email` 和 `type`。

### 4.4 `authenticated_client` 设计

两种方式：

**方式 A：直接写 session（快，适合大多数测试）**

```python
@pytest.fixture
def authenticated_client(app, client, user_factory):
    with app.app_context():
        user = user_factory()
        with client.session_transaction() as sess:
            sess["_user_id"] = user.get_id()
            sess["_fresh"] = True
    return client
```

**方式 B：走真实登录路由（慢，适合 E2E）**

```python
def login(client, username, password):
    return client.post(
        "/user/login/",
        data={"username": username, "password": password},
        follow_redirects=True,
    )
```

约定：

- 集成测试优先方式 A，减少与登录流程的耦合。
- E2E 测试必须走方式 B，验证真实流程。

### 4.5 Fixture 作用域规则

| 作用域 | 适用 | 风险 |
| --- | --- | --- |
| `function` | 绝大多数测试 | 安全，推荐默认 |
| `module` | 只读、不可变数据 | 状态泄漏 |
| `session` | 极少数昂贵资源（浏览器驱动） | 必须显式清理 |
| `class` | 同类测试共享 | 谨慎 |

**禁止**：把可变数据库状态、用户、邮件 outbox 放在 `module`/`session` 作用域。

### 4.6 文件上传与临时目录

`FileField` 的 `save_path` 由字段自己持有，没有全局配置键。测试中一律用 `tmp_path`，不要写入仓库：

```python
@pytest.fixture
def tmp_upload_dir(tmp_path):
    upload_dir = tmp_path / "uploads"
    upload_dir.mkdir()
    return upload_dir


def test_file_upload(app, tmp_upload_dir):
    field = FileField(save_path=str(tmp_upload_dir))
    ...
    assert list(tmp_upload_dir.iterdir())
```

规则：

- 不把上传文件写到 `tests/integration/data/`（那是只读素材）。
- 不依赖测试执行后的残留文件；`tmp_path` 由 pytest 自动清理。
- 测试导出/下载时，同样写到 `tmp_path`，不要写 `tests/tmp/` 的固定文件名。
- 需要校验文件名、扩展名、大小限制时，分别造边界数据。

### 4.7 多 app 与重绑定测试

`db` 是模块级单例，绑定一个 Flask app；重复 `init_app` 会抛错，必须先 `dispose()`。多 app 测试用工厂 fixture：

```python
@pytest.fixture
def app_factory():
    created = []

    def make(**config):
        # db 是单例：创建新 app 前先释放上一个绑定。
        for previous_app, previous_exts in created:
            with previous_app.app_context():
                previous_exts.shutdown()
        created.clear()

        app = Flask(__name__)
        app.config.update(TESTING=True, SECRET_KEY="test_key", **config)
        exts = ExtensionManager()
        exts.init_app(app)
        created.append((app, exts))
        return app, exts

    yield make

    for app, exts in created:
        with app.app_context():
            exts.shutdown()
```

注意：

- 同一测试内不要并行持有两个已初始化的 `db`；工厂会在创建新 app 前释放上一个。
- 多 app 测试优先放在 `unit/datastore/`，不要污染常规集成测试。
- `app_factory` 的清理必须放在 teardown，避免单例泄漏到后续测试。

## 5. 测试数据与工厂

### 5.1 当前方式

现有测试直接构造模型：

```python
db.session.add_all([
    AdminTestModel(name="model1", integer_value=5000),
    AdminTestModel(name="model2", integer_value=9000),
])
db.session.commit()
```

优点：直观、无额外依赖。
缺点：重复多、字段变化时要改多处、容易遗漏必填字段。

### 5.2 推荐方式：轻量工厂函数（不引入新依赖）

先不引入 `factory-boy`，用普通函数即可：

```python
# tests/fixtures/factories.py
from uuid import uuid4

from sqlalchemy import select

from flask_exts.datastore.sqla import db
from flask_exts.proxies import current_userstore


def unique(prefix="user"):
    """Return a process-safe unique name, e.g. ``user-3f9a1c2e``."""
    return f"{prefix}-{uuid4().hex[:8]}"


def _get_or_create_role(name):
    role = db.session.execute(
        select(current_userstore.role_class).filter_by(name=name)
    ).scalar()
    if role is None:
        role = current_userstore.create_role(name)
    return role


def make_user(*, username=None, password="password", email=None, active=True, roles=()):
    username = username or unique("user")
    email = email or f"{username}@example.com"
    user = current_userstore.create_user(
        username=username, password=password, email=email
    )
    current_userstore.user_set(user, is_active=active)
    for role_name in roles:
        current_userstore.user_add_role(user, _get_or_create_role(role_name))
    return user


def make_admin(**kwargs):
    kwargs.setdefault("username", unique("admin"))
    return make_user(roles=("admin",), **kwargs)


def make_records(model, count, **defaults):
    """Bulk-create ``count`` rows with a stable name prefix."""
    objs = [
        model(**{**defaults, "name": f"{defaults.get('name', 'record')}-{i}"})
        for i in range(count)
    ]
    db.session.add_all(objs)
    db.session.commit()
    return objs


def make_admin_record(**kwargs):
    from tests.integration.admin.sqla.models.admin_records import AdminTestModel

    defaults = {"name": unique("record"), "description": "description"}
    defaults.update(kwargs)
    obj = AdminTestModel(**defaults)
    db.session.add(obj)
    db.session.commit()
    return obj
```

### 5.3 可选：factory-boy / faker

如果团队接受新增测试依赖，可用：

```python
import factory
from flask_exts.userstore.sqla.models import User


class UserFactory(factory.Factory):
    class Meta:
        model = User

    username = factory.Sequence(lambda n: f"user{n}")
    email = factory.LazyAttribute(lambda o: f"{o.username}@example.com")
    password = "password"
```

注意：

- 新增依赖需要先询问（见 `AGENTS.md` 变更边界）。
- `factory-boy` 直接构造 ORM 对象时，仍需 `db.session.add/commit`。
- `faker` 生成随机数据时要固定 seed，保证可复现。

### 5.4 数据构造原则

1. **显式优于隐式**：测试中只设置与行为相关的字段。
2. **最小数据**：能用 2 条数据验证，不要造 100 条。
3. **唯一性**：用户名/邮箱加测试名前缀或序号，避免跨测试冲突。
4. **批量插入**：大数据集用 `add_all` + 一次 `commit`。
5. **清理**：依赖 `db.reset_all()` 或 fixture teardown，不手动删表。
6. **时间**：需要“过期”时用 `monkeypatch` 或直接构造过期令牌，不 `sleep`。

### 5.5 固定时间、随机数与外部输入

- **时间**：优先让被测函数接受显式时间参数；无法注入时用 `monkeypatch` 固定 `datetime`/`time`，不要 `sleep`。
- **随机**：需要随机值时固定 seed；不要用随机值生成断言依赖的数据。
- **唯一值**：用 `uuid4().hex` 或测试名前缀 + 序号，避免跨测试、跨进程冲突。
- **外部输入**：搜索词、文件名、URL 参数用表驱动覆盖边界（空串、空格、`&`、中文、超长）。
- **上传/导出**：一律写 `tmp_path`，不提交二进制产物。
- **网络**：不访问真实 SMTP、HTTP、DNS；在边界处 mock。

## 6. 测试覆盖矩阵

### 6.1 模块覆盖矩阵

图例：✅ 已有较好覆盖；⏳ 部分覆盖/需补强；❌ 基本没有。

| 模块 | Unit | Integration | HTTP E2E | Performance | 主要缺口 |
| --- | :---: | :---: | :---: | :---: | --- |
| Extension 系统 | ✅ | ⏳ | ❌ | ❌ | 晚注册待补；shutdown 异常隔离与现有测试行为冲突（C11）；E2E 不需要 |
| Datastore / Query | ✅ | ⏳ | ❌ | ⏳ | 计数正确性、N+1、复杂过滤 |
| Admin 基础 | ✅ | ✅ | ⏳ | ❌ | 权限矩阵、导出类型、URL 特殊字符 |
| Admin Inline | ⏳ | ✅ | ⏳ | ❌ | Inline + AJAX 外键、复杂关系 |
| Forms | ✅ | ✅ | ⏳ | ❌ | CSRF 过期/篡改、文件边界、Recaptcha |
| Security | ✅ | ✅ | ⏳ | ❌ | 令牌过期、加密篡改、TFA 恢复码 |
| UserStore | ❌ | ⏳ | ⏳ | ❌ | `get_users`、`remove_user`、profile |
| UserCenter | ⏳ | ✅ | ⏳ | ❌ | 完整旅程、并发/重复提交、错误页 |
| Emailer | ✅ | ⏳ | ⏳ | ❌ | SMTP 错误、默认发送器、未知类型 |
| Frontend | ✅ | ⏳ | ❌ | ❌ | 插件资源顺序、模板集成 |
| Commands | ❌ | ❌ | ❌ | ❌ | 建表、建用户、错误处理 |
| Babel / i18n | ✅ | ⏳ | ⏳ | ❌ | 语言切换、时区、复数 |

**关键路径（必须 100% 覆盖）：**

1. 扩展注册 → 依赖排序 → `init_app` → `post_init` → `shutdown`
2. 登录 → TFA 待验证 → TFA 验证 → 登录成功
3. 注册 → 发验证邮件 → 验证邮箱
4. 改邮箱/改密码 → 旧令牌失效
5. CSRF 生成 → 校验 → 过期/篡改拒绝
6. Admin 列表 → 搜索/筛选/排序/分页 → 计数
7. Admin 创建/编辑/删除 → 数据库最终状态
8. Inline 父子记录 → 新增/修改/删除
9. 权限：匿名/普通用户/admin/未激活
10. 开放重定向防护

<a id="62-需求追溯矩阵"></a>

### 6.2 需求追溯与用例导航

`requirements.md` 定义 `REQ-*` 契约，本文维护测试设计。具体 `REQ → TC → 测试入口` 唯一维护在 [`requirements.md`](./requirements.md) 各契约的“验收”字段；`TC` 的编号规则和历史别名见第 6.3 节。下表只按能力导航，不推断契约关联、层级或覆盖情况；用例层级、状态及断言以各用例条目为准。

| 能力 | 测试用例入口 |
| --- | --- |
| 扩展生命周期、依赖、关闭 | [扩展测试](#71-extension-系统) |
| 数据库绑定、会话、Query、事务 | [数据测试](#72-datastore--query)、[事务与约束](#711-数据库事务与约束) |
| Admin 列表、CRUD、Inline、导出、权限 | [Admin 测试](#73-admin) |
| 表单、CSRF、上传 | [表单测试](#74-forms) |
| 授权、令牌、加密、TFA | [安全测试](#75-security)、[用户中心测试](#77-usercenter) |
| 用户存储 | [UserStore 测试](#76-userstore) |
| 注册、邮箱、密码 | [用户中心测试](#77-usercenter) |
| 邮件与信号 | [邮件测试](#78-emailer)、[信号测试](#712-错误处理与信号契约) |
| 前端插件与模板 | [前端测试](#79-frontend) |
| CLI | [命令测试](#710-commands) |
| i18n / 时区 | [国际化测试](#713-i18n时区与复数) |
| 错误处理 | [错误处理测试](#712-错误处理与信号契约) |
| 端到端流程 | [HTTP E2E 流程](#82-http-e2e-流程清单) |

#### 追溯证据检查

对每条本次变更涉及的契约，核实：

1. 需求中的预期和验收条件是否明确；列出正常、边界、错误及适用的安全场景。
2. 是否存在对应 `TC-*` 测试用例和测试文件/函数；检查断言是否真正验证该预期，而非仅匹配名称或编号。
3. 测试是否实际被收集并执行；记录命令、环境、代码基线及通过/失败/未执行结果。
4. 测试不存在、不能执行或未覆盖某条边界时分别登记缺口；不要将“已设计”写成“已验证”。
5. 按 `requirements.md` 第 2 节分别维护 `implementation`、`verification` 和问题关联；所有适用验收通过并记录契约修订、代码版本、环境、范围及结果后，才能标 `passed`。

例如 `REQ-AUTHZ-005` 关联 SEC-01：本轮 HEAD 静态源码仍显示 inactive admin 会被放行，但未运行针对性回归用例。应按契约设计禁用管理员访问被拒的测试，并记录真实执行结果；全套测试通过不等于该缺口已关闭。

### 6.3 测试用例编号规则

测试用例采用 `TC-<领域>-<序号>`；`TC` 表示 Test Case，领域使用 [`glossary.md`](./glossary.md) 第 1.1 节词表。领域由大写字母开头，后续只能使用大写字母或数字，不含分隔符；范围尚未登记时，先核对既有分类，确需新增则先维护词表。

序号按领域独立分配：`001`～`999` 使用三位，之后使用自然位数，不使用 `000`。分配前检查已登记编号、历史别名及废弃编号，取该领域已分配的最大序号加一，无已分配编号时从 `001` 开始；并行变更合并前检查并解决冲突。完整编号全局唯一、永不复用，领域调整不自动重编号。

测试用例编号与契约编号独立分配：一个 `REQ` 可以关联多个 `TC`，一个 `TC` 也可以验证多个 `REQ`，不能凭序号相同推断关联。跨领域场景选择主要验证的领域，并显式关联其他受影响契约；测试状态、执行入口和执行结果分别记录，不能从编号推断。

**测试层级不放入编号**：Unit、Integration、HTTP E2E、浏览器 E2E 和 Performance 在用例的“类型”字段或所属测试章节中记录；需要区分 HTTP 与浏览器时写明具体类型。同一用例可关联不同层级的多个测试入口，分别记录结果；执行方式或层级调整不因此改号。仓库支持时可用测试标记区分，本文的 marker 规划不代表仓库已注册。

**历史用例迁移（2026-11-09）**：本目录已有用例按下表一对一迁移，范围内从起始编号按顺序对应。旧 `TST-*` 编号保留为历史别名；更早的不带 `TST-` 的编号仍可先补上 `TST-` 再查下表。仅适用于下表所列范围，不能据此前缀或相同序号猜测其他映射。

| 历史测试编号 | 当前测试编号 |
| --- | --- |
| `TST-E-01`～`TST-E-20` | `TC-EXT-001`～`TC-EXT-020` |
| `TST-D-01`～`TST-D-18` | `TC-DATA-001`～`TC-DATA-018` |
| `TST-A-01`～`TST-A-33` | `TC-ADMIN-001`～`TC-ADMIN-033` |
| `TST-F-01`～`TST-F-17` | `TC-FORM-001`～`TC-FORM-017` |
| `TST-S-01`～`TST-S-21` | `TC-SEC-001`～`TC-SEC-021` |
| `TST-U-01`～`TST-U-15` | `TC-USER-001`～`TC-USER-015` |
| `TST-UC-01`～`TST-UC-22` | `TC-AUTH-001`～`TC-AUTH-022` |
| `TST-M-01`～`TST-M-09` | `TC-EMAIL-001`～`TC-EMAIL-009` |
| `TST-FE-01`～`TST-FE-10` | `TC-FRONTEND-001`～`TC-FRONTEND-010` |
| `TST-CLI-01`～`TST-CLI-06` | `TC-CLI-001`～`TC-CLI-006` |
| `TST-TX-01`～`TST-TX-09` | `TC-DATA-019`～`TC-DATA-027` |
| `TST-ERR-01`～`TST-ERR-08` | `TC-ERROR-001`～`TC-ERROR-008` |
| `TST-SIG-01`～`TST-SIG-06` | `TC-SIGNAL-001`～`TC-SIGNAL-006` |
| `TST-I18N-01`～`TST-I18N-06` | `TC-I18N-001`～`TC-I18N-006` |
| `TST-E2E-AUTH-01`～`TST-E2E-AUTH-06` | `TC-AUTH-023`～`TC-AUTH-028` |
| `TST-E2E-ADMIN-01`～`TST-E2E-ADMIN-06` | `TC-ADMIN-034`～`TC-ADMIN-039` |
| `TST-E2E-ERR-01` | `TC-ERROR-009` |
| `TST-E2E-I18N-01` | `TC-I18N-007` |

迁移仅改变本文档集的编号和引用，不改变用例内容、状态或执行结果。此前带能力段的 `TST-*` 和 `TEST-*` 文档示例未分配；如仓库或外部记录已使用，应先核实实际指向，保留历史引用，不推定与某条 `TC-*` 等价。后续变更或拆分编号时先核实关联并记录映射，按授权同步相关文档、测试代码和工具；仓库不可见时记录未核验。

## 7. 详细测试用例设计

> 说明：
> - **类型**：U=Unit，I=Integration，E=HTTP E2E，P=Performance。
> - **优先级**：P0=必须，P1=应该，P2=可选。
> - **状态**：现有=已有测试；待补=建议新增；待修=已有测试但断言不足。

### 7.1 Extension 系统

| ID | 场景 | 类型 | 优先级 | 状态 | 关键断言 |
| --- | --- | --- | --- | --- | --- |
| TC-EXT-001 | 注册合法扩展 | U | P0 | 现有 | 返回实例，name 正确 |
| TC-EXT-002 | 重复名称注册 | U | P0 | 现有 | 抛 `ExtensionError`，消息含名称 |
| TC-EXT-003 | 非 Extension 类注册 | U | P0 | 现有 | 抛 `ExtensionError` |
| TC-EXT-004 | 非法名称（空/非 ASCII/特殊字符） | U | P0 | 现有 | 抛 `ExtensionError` |
| TC-EXT-005 | 依赖项先于依赖者初始化 | U | P0 | 现有 | 依赖项在记录顺序中先于依赖者 |
| TC-EXT-006 | 无依赖扩展保持注册顺序 | U | P1 | 现有 | 顺序稳定 |
| TC-EXT-007 | 深链依赖 A→B→C | U | P1 | 现有 | C→B→A |
| TC-EXT-008 | 缺失依赖 | U | P0 | 现有 | 抛 `ExtensionNotFoundError` |
| TC-EXT-009 | 循环依赖 | U | P0 | 现有 | 抛 `ExtensionDependencyError`，消息含环 |
| TC-EXT-010 | 自依赖 | U | P1 | 现有 | 抛 `ExtensionDependencyError` |
| TC-EXT-011 | `init` 幂等 | U | P0 | 现有 | 第二次不重复调用 |
| TC-EXT-012 | `post_init` 前必须 `init` | U | P0 | 现有 | 抛 `ExtensionInitError` |
| TC-EXT-013 | `post_init` 幂等 | U | P0 | 现有 | 第二次不重复调用 |
| TC-EXT-014 | `post_init` 按依赖顺序 | U | P1 | 现有 | 顺序正确 |
| TC-EXT-015 | `shutdown` 逆序 | U | P0 | 现有 | 与初始化相反 |
| TC-EXT-016 | `shutdown` 单扩展异常隔离 | U | P1 | 现有测试与契约冲突 | 预期应继续关闭其他扩展并产生 warning；当前 `tests/unit/extension_core/test_registry.py::test_shutdown_exception` 断言 `ValueError` 传播，见 C11 |
| TC-EXT-017 | 内置扩展图可初始化 | I | P0 | 现有 | 所有内置扩展初始化成功 |
| TC-EXT-018 | Admin 收集 Portal/UserCenter 视图 | I | P0 | 现有 | 视图注册到 admin |
| TC-EXT-019 | 晚注册扩展 | U | P2 | 待补 | 文档化行为：不回溯扫描 |
| TC-EXT-020 | `has_extension` 语义 | U | P2 | 待补 | 明确“已注册”还是“已初始化” |

### 7.2 Datastore / Query

| ID | 场景 | 类型 | 优先级 | 状态 | 关键断言 |
| --- | --- | --- | --- | --- | --- |
| TC-DATA-001 | 缺少 `SQLALCHEMY_DATABASE_URI` | U | P0 | 现有 | 抛 `RuntimeError` |
| TC-DATA-002 | 扩展 key 与 Flask-SQLAlchemy 区分 | U | P0 | 现有 | 使用 `flask_exts_sqla` |
| TC-DATA-003 | 内存 SQLite 共享连接 | U | P0 | 现有 | `StaticPool` + `check_same_thread=False` |
| TC-DATA-004 | 未 dispose 重复绑定 | U | P0 | 现有 | 抛 `RuntimeError` |
| TC-DATA-005 | dispose 后可重绑定 | U | P0 | 现有 | 新 app 可用 |
| TC-DATA-006 | 无 app context dispose | U | P1 | 现有 | 不抛异常 |
| TC-DATA-007 | scoped session 按 app context | U | P0 | 现有 | 同 context 同 session |
| TC-DATA-008 | `reset_all` 删表重建 | U | P1 | 现有 | 表存在且为空 |
| TC-DATA-009 | JOIN 路径复用 | U | P0 | 现有 | 相同路径返回同一 alias |
| TC-DATA-010 | 前缀路径复用 | U | P1 | 现有 | 扩展路径复用前缀 |
| TC-DATA-011 | 不同关系生成不同 alias | U | P0 | 现有 | 多路径不串 |
| TC-DATA-012 | 搜索 `^`/`$`/`=` 语义 | U | P1 | 待补 | 前缀/后缀/精确 |
| TC-DATA-013 | 过滤操作符 | U | P1 | 待补 | `==`/`!=`/`>`/`<`/`like`/`in`/`between`/`is_null` |
| TC-DATA-014 | 一对多 JOIN 计数 | U | P0 | 待补 | `count` 等于根记录数，不重复 |
| TC-DATA-015 | eager load 配置 | U | P2 | 现有（弱） | `joinedload`/`selectinload` 生效 |
| TC-DATA-016 | 复合主键删除 | I | P1 | 现有 | 正确删除 |
| TC-DATA-017 | 无效关系路径 | U | P1 | 待补 | 抛 `ValueError`/`AttributeError` |
| TC-DATA-018 | 类型推断 | U | P1 | 现有 | 常见列类型正确 |

### 7.3 Admin

> View/ModelView/SqlaModelView 的实现与配置见 [`spec.md` 第 10 章](./spec.md#10-view-与-admin-专题)。本节只定义 Admin 测试用例；C1/C2/C5/C6 的问题说明见 `spec.md` 第 10.16 节，C1/C2/C6 的相关用例为 TC-ADMIN-021/TC-ADMIN-031/TC-ADMIN-032，状态以用例表为准。

| ID | 场景 | 类型 | 优先级 | 状态 | 关键断言 |
| --- | --- | --- | --- | --- | --- |
| TC-ADMIN-001 | 列表列渲染 | I | P0 | 现有 | 列名/值正确 |
| TC-ADMIN-002 | 默认分页 | I | P0 | 现有 | 页大小、页数、记录数 |
| TC-ADMIN-003 | 可配置页大小白名单 | I | P0 | 现有 | 非白名单回退默认 |
| TC-ADMIN-004 | 无分页（page_size=0） | I | P1 | 现有 | 返回全部 |
| TC-ADMIN-005 | 排序（升/降/关联） | I | P0 | 现有 | 顺序正确 |
| TC-ADMIN-006 | 默认排序 | I | P1 | 现有 | 无参数时按默认 |
| TC-ADMIN-007 | 搜索（普通/关联/无关联行） | I | P0 | 现有 | 命中/不命中 |
| TC-ADMIN-008 | 搜索保留额外参数 | I | P1 | 现有 | 隐藏字段保留 |
| TC-ADMIN-009 | 筛选操作符 | I | P0 | 现有 | 7 种文本操作、数值/日期/布尔 |
| TC-ADMIN-010 | 关联列筛选 | I | P1 | 现有 | 关联表过滤正确 |
| TC-ADMIN-011 | CRUD | I | P0 | 现有 | 创建/编辑/删除 + DB 状态 |
| TC-ADMIN-012 | 详情页 | I | P1 | 现有 | 字段值正确 |
| TC-ADMIN-013 | CSV 导出 | I | P1 | 现有 | 内容/表头 |
| TC-ADMIN-014 | 导出最大行数 | I | P2 | 待补 | 超限行为 |
| TC-ADMIN-015 | 其他导出类型 | I | P2 | 待补 | tablib 支持类型 |
| TC-ADMIN-016 | 行内编辑 | I | P1 | 现有 | 列表页保存 |
| TC-ADMIN-017 | 批量删除 | I | P0 | 现有 | 选中记录删除 |
| TC-ADMIN-018 | Inline 创建/编辑/删除 | I | P0 | 现有 | 父子记录最终状态 |
| TC-ADMIN-019 | Inline 一对多/多对多/一对一 | I | P1 | 现有 | 关系正确 |
| TC-ADMIN-020 | Inline 多外键 | I | P1 | 现有 | 关系映射正确 |
| TC-ADMIN-021 | Inline + AJAX 外键 | I | P0 | 待补 | 页面 200，能搜索/保存（对应 C1） |
| TC-ADMIN-022 | AJAX 外键/多对多 | I | P1 | 现有 | 返回 JSON 正确 |
| TC-ADMIN-023 | 复合主键 | I | P1 | 现有 | 列表/删除正确 |
| TC-ADMIN-024 | 字符串主键 | I | P1 | 现有 | 列表/删除正确 |
| TC-ADMIN-025 | 权限：匿名 | I | P0 | 待补/部分 | 默认 403（加 @login_required 时重定向） |
| TC-ADMIN-026 | 权限：普通用户 | I | P0 | 待补/部分 | 403 |
| TC-ADMIN-027 | 权限：admin | I | P0 | 现有 | 200 |
| TC-ADMIN-028 | 权限：未激活账号 | I | P0 | 待补 | 拒绝账号功能 |
| TC-ADMIN-029 | 动态翻译 | I | P1 | 现有 | 语言切换后文本变化 |
| TC-ADMIN-030 | 表单额外字段/自定义基类 | I | P1 | 现有 | 字段存在/渲染 |
| TC-ADMIN-031 | 一对多搜索计数 | I | P0 | 待补 | 分页总数不重复（对应 C2） |
| TC-ADMIN-032 | URL 特殊字符 | I | P1 | 待补 | 搜索词含 `&`/空格/中文仍正确（对应 C6） |
| TC-ADMIN-033 | 列表空结果/越界页 | I | P1 | 待补 | 200，空列表，页数合理 |

补充测试缺口（2026-11-07 快照，现状待核实）：

- 自定义 `DataBackend` 缺少单元测试。
- V-02 涉及的单行操作与批量操作渲染/执行缺少专门测试；`test_actions.py` 的历史记录以行内编辑和批量删除为主。
- 视图编辑开关 `can_edit=False` 的 AJAX 更新边界另见第 7.5 节 SEC-19；不能把普通行内编辑用例当成该边界已覆盖。

### 7.4 Forms

| ID | 场景 | 类型 | 优先级 | 状态 | 关键断言 |
| --- | --- | --- | --- | --- | --- |
| TC-FORM-001 | JSON 合法/非法/空 | U | P0 | 现有 | 解析/错误 |
| TC-FORM-002 | 日期/时间/日期时间字段 | U | P0 | 现有 | 解析/格式化 |
| TC-FORM-003 | 文件字段无输入 | U | P0 | 现有 | 不报错/None |
| TC-FORM-004 | 文件上传/多文件 | U | P0 | 现有 | 保存/读取 |
| TC-FORM-005 | 图片上传 | U | P1 | 现有 | 类型/尺寸 |
| TC-FORM-006 | 必填文件 | U | P1 | 现有 | 缺失报错 |
| TC-FORM-007 | FieldList / FormField | U | P1 | 现有 | 子表单数据 |
| TC-FORM-008 | CSRF 开启 | U | P0 | 现有 | token 存在/校验通过 |
| TC-FORM-009 | CSRF 关闭 | U | P1 | 现有 | 不生成/不校验 |
| TC-FORM-010 | CSRF 缺失/篡改/过期 | U | P0 | 待补 | 分别报错 |
| TC-FORM-011 | CSRF 独立派生密钥 | U | P1 | 现有 | 不等于主密钥 |
| TC-FORM-012 | `wrap_formdata` JSON/files | U | P1 | 待补 | 正确合并 |
| TC-FORM-013 | Unique 校验器 | I | P1 | 现有（间接） | 重复值报错 |
| TC-FORM-014 | Recaptcha（mock） | U | P2 | 待补 | 成功/失败 |
| TC-FORM-015 | InlineModelField | U | P1 | 待补 | 子表单渲染/取值 |
| TC-FORM-016 | Widget 渲染 | U | P2 | 待补 | Bootstrap 类/属性 |
| TC-FORM-017 | i18n 标签/错误 | I | P2 | 部分 | 语言切换 |

`TC-FORM-010` 另需覆盖 HTTP 请求中缺失、篡改和过期 token 的边界；该层级待补，不能以基础表单测试代替。

### 7.5 Security

> 安全威胁模型、控制措施、配置基线与风险清单见 [`security.md`](./security.md)。本节只定义测试用例；若实现行为与安全预期冲突，先在 `security.md` 登记风险，再补失败测试。

| ID | 场景 | 类型 | 优先级 | 状态 | 关键断言 |
| --- | --- | --- | --- | --- | --- |
| TC-SEC-001 | 不同 purpose 派生不同 key | U | P0 | 现有 | key 不相等且不等于主密钥 |
| TC-SEC-002 | 哈希正确/错误 | U | P0 | 现有 | verify True/False |
| TC-SEC-003 | AES-GCM 加解密 | U | P0 | 待补 | 往返一致 |
| TC-SEC-004 | 密文篡改 | U | P0 | 待补 | 解密失败 |
| TC-SEC-005 | 序列化有效 | U | P0 | 现有 | 数据一致 |
| TC-SEC-006 | 序列化过期 | U | P0 | 待补（现有注释） | `expired=True` |
| TC-SEC-007 | 序列化篡改/错误 salt | U | P0 | 待补 | `invalid=True` |
| TC-SEC-008 | 邮箱验证令牌 | I | P0 | 现有 | 验证成功/重复失败 |
| TC-SEC-009 | 改邮箱令牌 | I | P0 | 现有（部分） | 旧邮箱/密码变化后失效；密码变更后令牌失效待补 |
| TC-SEC-010 | 重置密码令牌 | I | P0 | 现有（间接） | 成功/过期/无效 |
| TC-SEC-011 | 令牌用户不存在 | U | P1 | 待补 | `TokenUserNotFoundError` |
| TC-SEC-012 | 授权：admin | U | P0 | 现有 | 允许 |
| TC-SEC-013 | 授权：普通用户/无角色 | U | P0 | 现有 | 拒绝 |
| TC-SEC-014 | `allow_access` 公开视图 | U | P0 | 现有 | 允许 |
| TC-SEC-015 | `requires_active` 未激活 | U | P0 | 现有 | 拒绝 |
| TC-SEC-016 | TFA 生成/校验 | U | P0 | 现有（弱） | 正确码通过，错误码失败 |
| TC-SEC-017 | TFA 恢复码 | U | P0 | 待补 | 一次性使用/失效 |
| TC-SEC-018 | TFA 待验证不能访问 | I | P0 | 现有 | 重定向/401 |
| TC-SEC-019 | 密码变更使会话失效 | I | P0 | 现有 | 旧 session 失效 |
| TC-SEC-020 | 安全重定向 | U | P0 | 现有 | 外部/畸形 URL 拒绝 |
| TC-SEC-021 | JWT 编解码/过期/畸形 | I | P1 | 现有 | 正确/异常 |

补充场景与测试建议（2026-11-07 快照，现状待核实；风险编号不是测试编号）：

- `AesGcmEncryptor` 除往返和篡改外还需验证错误密钥；序列化过期/篡改可使用可控时间或短 `max_age`。
- `TC-SEC-009` 的历史测试主要覆盖确认成功和密码校验；密码变化后旧改邮箱令牌失效的边界待补。
- SEC-01：构造 `admin` 且 `is_active=False`，断言受保护操作被拒；旧快照预期该测试先失败。
- SEC-02：启用 TFA 的用户使用 Bearer token 访问受保护资源时，验证不能绕过第二因子。
- SEC-03：限流/锁定须先明确由应用或反向代理负责，再设计对应测试；可添加集成测试桩。
- SEC-04：核实 `TFA_EXEMPT_ENDPOINTS` 是否实现，若实现则补测试，否则从配置文档移除并说明。
- SEC-07：设计密钥轮换及 TOTP 数据迁移测试；快照中迁移实现待补。
- SEC-12：配置安全 Cookie 后断言 `Set-Cookie` 的 `Secure`、`HttpOnly` 和 `SameSite`。
- SEC-16：禁用、重新启用 TFA 后断言旧恢复码被拒。
- SEC-17：模拟 SMTP，确认使用校验证书与主机名的 SSL context。
- SEC-18：模拟 logger，断言 warning 不含令牌和链接。
- SEC-19 / V-01：`can_edit=False` 且配置 `column_editable_list` 时，断言 `ajax_update` 被拒；两个编号指向同一问题。

上述风险场景尚未在此单独分配 TC 编号；不能凭风险编号或已有文件推断测试实现和执行结果。

### 7.6 UserStore

| ID | 场景 | 类型 | 优先级 | 状态 | 关键断言 |
| --- | --- | --- | --- | --- | --- |
| TC-USER-001 | 创建用户 | I | P0 | 现有 | id/username/email |
| TC-USER-002 | 重复用户名 | I | P0 | 现有 | `UserAlreadyExistsError` |
| TC-USER-003 | 重复邮箱 | I | P0 | 现有 | `UserAlreadyExistsError` |
| TC-USER-004 | 登录成功 | I | P0 | 现有 | 返回用户 |
| TC-USER-005 | 登录失败（用户不存在/密码错） | I | P0 | 现有 | `InvalidCredentialsError` |
| TC-USER-006 | dummy hash 抗枚举 | I | P1 | 待补 | 不存在用户也执行校验 |
| TC-USER-007 | 按 id/identity/username 查询 | I | P0 | 现有 | 正确用户 |
| TC-USER-008 | `identity_name` 切换 | I | P1 | 现有 | 按 username 查 |
| TC-USER-009 | 角色创建/关联 | I | P0 | 现有 | 角色列表 |
| TC-USER-010 | `user_set` 更新 | I | P1 | 待补 | 属性持久化 |
| TC-USER-011 | `save_user` | I | P1 | 待补 | 更新持久化 |
| TC-USER-012 | `get_users` 过滤 | I | P1 | 待补 | 按条件筛选（问题编号待核实） |
| TC-USER-013 | `remove_user` | I | P1 | 待补 | 删除或明确抛错（问题编号待核实） |
| TC-USER-014 | profile 一对一 | I | P1 | 待补 | 关联正确 |
| TC-USER-015 | 密码哈希 | I | P0 | 现有 | 明文不落库 |

### 7.7 UserCenter

| ID | 场景 | 类型 | 优先级 | 状态 | 关键断言 |
| --- | --- | --- | --- | --- | --- |
| TC-AUTH-001 | 注册成功 | I/E | P0 | 现有 | 用户创建 + 发验证邮件 |
| TC-AUTH-002 | 重复邮箱/用户名 | I | P0 | 现有 | 错误提示 |
| TC-AUTH-003 | 登录成功 | I/E | P0 | 现有 | 重定向/会话 |
| TC-AUTH-004 | 登录失败 | I | P0 | 现有 | 统一错误，不枚举 |
| TC-AUTH-005 | 未激活登录 | I | P0 | 现有 | 按设计处理 |
| TC-AUTH-006 | 登出 | I/E | P0 | 现有 | 会话清理 |
| TC-AUTH-007 | 资料页需登录 | I | P0 | 现有 | 重定向登录 |
| TC-AUTH-008 | 邮箱验证 | I/E | P0 | 现有 | `email_verified=True` |
| TC-AUTH-009 | 重发验证邮件 | I | P1 | 现有 | 发送一次 |
| TC-AUTH-010 | 改邮箱需密码 | I | P0 | 现有 | 密码错拒绝 |
| TC-AUTH-011 | 改邮箱需确认 | I/E | P0 | 现有 | 点击链接后生效 |
| TC-AUTH-012 | 改邮箱重复 | I | P1 | 现有 | 拒绝 |
| TC-AUTH-013 | 改密码 | I/E | P0 | 现有 | 新密码可登录，旧密码失败 |
| TC-AUTH-014 | 找回密码 | I/E | P0 | 现有 | 发邮件 |
| TC-AUTH-015 | 重置密码 | I/E | P0 | 现有 | 新密码生效 |
| TC-AUTH-016 | 恢复码 | I | P0 | 现有 | 登录成功/码失效 |
| TC-AUTH-017 | TFA 启用/关闭 | I | P0 | 现有（部分） | `tfa_enabled` 变化 |
| TC-AUTH-018 | TFA 登录完整流程 | E | P0 | 待补 | 密码→验证码→登录 |
| TC-AUTH-019 | TFA 待验证不能绕过 | I | P0 | 现有 | 受保护页拒绝 |
| TC-AUTH-020 | 未激活账号功能限制 | I | P0 | 现有 | 账号功能拒绝 |
| TC-AUTH-021 | 开放重定向 | I | P0 | 待补 | `next` 外部 URL 被拒 |
| TC-AUTH-022 | 重复提交/并发注册 | I | P2 | 待补 | 唯一约束生效 |

### 7.8 Emailer

| ID | 场景 | 类型 | 优先级 | 状态 | 关键断言 |
| --- | --- | --- | --- | --- | --- |
| TC-EMAIL-001 | 信号触发发送 | U | P0 | 现有 | sender 收到 data |
| TC-EMAIL-002 | 缺少 `type` | U | P1 | 待补 | warning，不发送 |
| TC-EMAIL-003 | 未知 sender | U | P1 | 待补 | warning，不抛 |
| TC-EMAIL-004 | SMTP 成功（mock） | U | P1 | 现有（基础） | 调用成功 |
| TC-EMAIL-005 | SMTP 异常 | U | P1 | 待补 | `SmtpError` 处理 |
| TC-EMAIL-006 | 重复注册 sender | U | P1 | 待补 | `ValueError` |
| TC-EMAIL-007 | 默认 sender 配置存在/缺失 | U | P1 | 待补 | 注册/不注册 |
| TC-EMAIL-008 | 验证邮件/重置邮件内容 | I | P1 | 待补 | 主题/链接/收件人 |
| TC-EMAIL-009 | `email_change` 复用 `verify_email` sender | I | P0 | 待补 | 收件人为新邮箱，链接指向 `confirm_email_change` |

### 7.9 Frontend

| ID | 场景 | 类型 | 优先级 | 状态 | 关键断言 |
| --- | --- | --- | --- | --- | --- |
| TC-FRONTEND-001 | 插件自动发现 | U | P0 | 现有（间接） | 注册表包含内置插件 |
| TC-FRONTEND-002 | 重复插件名 | U | P0 | 现有 | `ValueError` |
| TC-FRONTEND-003 | 默认插件顺序 | U | P0 | 现有 | 输入顺序保留 |
| TC-FRONTEND-004 | 请求插件依赖排序 | U | P0 | 现有 | 依赖在前 |
| TC-FRONTEND-005 | 循环依赖 | U | P0 | 现有 | `PluginCycleError` |
| TC-FRONTEND-006 | 未知插件 | U | P1 | 待补 | `ValueError` |
| TC-FRONTEND-007 | 样式/脚本拼接顺序 | U | P1 | 现有 | 依赖顺序 + `Markup` |
| TC-FRONTEND-008 | Jinja 全局变量 | I | P0 | 现有 | `_template`/`csrf_token` |
| TC-FRONTEND-009 | 模板集成 | I | P1 | 待补 | 页面包含插件资源 |
| TC-FRONTEND-010 | vendor 资源存在 | U | P2 | 待补 | 关键文件存在 |

### 7.10 Commands

| ID | 场景 | 类型 | 优先级 | 状态 | 关键断言 |
| --- | --- | --- | --- | --- | --- |
| TC-CLI-001 | `datastore create_all` | I | P1 | 待补 | 表创建 |
| TC-CLI-002 | `datastore drop_all` | I | P1 | 待补 | 表删除 |
| TC-CLI-003 | `security create_user` | I | P1 | 待补 | 用户创建 |
| TC-CLI-004 | 重复用户 | I | P1 | 待补 | 错误提示 |
| TC-CLI-005 | `--active` / `--email` | I | P1 | 待补 | 属性正确 |
| TC-CLI-006 | 命令注册/帮助 | I | P2 | 待补 | 命令可见 |

CLI 测试写法：

```python
def test_cli_create_all(app):
    runner = app.test_cli_runner()
    result = runner.invoke(args=["datastore", "create_all"])
    assert result.exit_code == 0
    assert "create_all" in result.output


def test_cli_create_user(app):
    runner = app.test_cli_runner()
    result = runner.invoke(
        args=["security", "create_user", "cli-user", "--password", "secret", "--active"]
    )
    assert result.exit_code == 0
    assert "Created user cli-user" in result.output
```

注意：

- `app.test_cli_runner()` 会自动进入 app context，不需要手动 `with app.app_context()`。
- 命令失败时断言 `exit_code != 0` 且 `result.output` 含错误信息。
- 密码不要出现在断言输出中。

### 7.11 数据库事务与约束

事务回滚、级联删除、外键完整性目前均未覆盖，建议补充：

| ID | 场景 | 类型 | 优先级 | 状态 | 关键断言 |
| --- | --- | --- | --- | --- | --- |
| TC-DATA-019 | 正常提交后数据持久化 | I | P0 | 待补 | 重新查询可见 |
| TC-DATA-020 | 视图异常时回滚 | I | P0 | 待补 | 无部分写入 |
| TC-DATA-021 | `IntegrityError` 后 session 可复用 | I | P0 | 待补 | `rollback()` 后可继续查询/写入 |
| TC-DATA-022 | 级联删除（`cascade="all, delete-orphan"`） | I | P1 | 待补 | 子记录一并删除 |
| TC-DATA-023 | 受限删除（无级联） | I | P1 | 待补 | 抛 `IntegrityError` 或按设计拒绝 |
| TC-DATA-024 | 外键完整性 | I | P0 | 待补 | 非法外键被拒绝（SQLite 需 `PRAGMA foreign_keys=ON`） |
| TC-DATA-025 | 唯一约束 | I | P0 | 待补 | 重复用户名/邮箱被拒绝 |
| TC-DATA-026 | 并发更新/丢失更新 | I | P2 | 待补 | 记录当前行为，不假设乐观锁 |
| TC-DATA-027 | 一对多增删后计数一致 | I | P0 | 待补 | `count` 与根记录数一致（对应 C2） |

> SQLite 默认不启用外键约束。测试 TC-DATA-024 前必须显式执行 `PRAGMA foreign_keys=ON`，否则会“假通过”。

### 7.12 错误处理与信号契约

| ID | 场景 | 类型 | 优先级 | 状态 | 关键断言 |
| --- | --- | --- | --- | --- | --- |
| TC-ERROR-001 | 未知路由 404 | I | P1 | 待补 | 状态码 404，模板可渲染 |
| TC-ERROR-002 | 无权限 403 | I | P0 | 待补 | 普通用户访问 admin 被拒 |
| TC-ERROR-003 | 方法不允许 405 | I | P2 | 待补 | 状态码 405 |
| TC-ERROR-004 | 未捕获异常 | I | P2 | 待补 | `TESTING=True` 下异常上抛；生产配置下 500 页 |
| TC-ERROR-005 | 无效/过期令牌页 | I | P0 | 待补 | 友好错误，不泄露用户信息 |
| TC-ERROR-006 | 畸形表单数据 | I | P1 | 待补 | 400/表单错误，不 500 |
| TC-ERROR-007 | 未知导出类型 | I | P2 | 待补 | 明确错误，不崩溃 |
| TC-ERROR-008 | CSRF 校验失败 | I | P0 | 待补 | 拒绝提交，提示可理解 |

信号契约：

| ID | 场景 | 类型 | 优先级 | 状态 | 关键断言 |
| --- | --- | --- | --- | --- | --- |
| TC-SIGNAL-001 | `user_registered` 载荷 | U | P0 | 待补 | `user` 为刚创建用户 |
| TC-SIGNAL-002 | `verify_email` 邮件字段 | U | P0 | 待补 | `type=verify_email`、`email`、`verification_token`、`verification_link` |
| TC-SIGNAL-003 | `reset_password` 邮件字段 | U | P0 | 待补 | `type=reset_password`、`email`、`reset_password_token`、`reset_password_link` |
| TC-SIGNAL-004 | `email_change` 邮件字段 | U | P0 | 待补 | `type=verify_email`、`email`（新邮箱）、`verification_token`、`verification_link` |
| TC-SIGNAL-005 | 未注册 sender | U | P1 | 待补 | warning，不抛异常 |
| TC-SIGNAL-006 | sender 抛 `SmtpError` | U | P1 | 待补 | 被捕获，返回提示 |

> `email_change` 复用 `type=verify_email`，但收件人是新邮箱；断言时结合 `email` 或 token 键区分，不能只按 `type` 判断。

### 7.13 i18n、时区与复数

| ID | 场景 | 类型 | 优先级 | 状态 | 关键断言 |
| --- | --- | --- | --- | --- | --- |
| TC-I18N-001 | 默认语言 | I | P1 | 待补 | 按 `BABEL_DEFAULT_LOCALE` 渲染 |
| TC-I18N-002 | `?lang=zh` 切换 | I | P1 | 待补 | 文本变为中文，cookie/session 生效 |
| TC-I18N-003 | 不支持语言回退 | I | P1 | 待补 | 回退默认语言，不报错 |
| TC-I18N-004 | 时区渲染 | I | P2 | 待补 | 按 `BABEL_DEFAULT_TIMEZONE` 输出 |
| TC-I18N-005 | 复数形式 | U | P2 | 待补 | 单复数选择正确 |
| TC-I18N-006 | 缺失翻译回退 | U | P2 | 待补 | 回退 msgid，不抛异常 |

## 8. 端到端测试方案

> **状态声明**：本章为目标设计/规划草案。当前仓库不存在 `tests/e2e/` 目录或端到端测试用例；本章用例在落地并接入运行前仅作为测试设计参考。

### 8.1 两种 E2E

| 方式 | 工具 | 优点 | 缺点 | 建议 |
| --- | --- | --- | --- | --- |
| HTTP 级 E2E | Flask `test_client` | 快、稳定、无浏览器依赖 | 不验证 JS/CSS | **默认采用** |
| 浏览器 E2E | Selenium/Playwright | 验证真实 UI/JS | 慢、脆弱、需环境 | 可选、夜间运行 |

Selenium/Playwright 属于第二种。建议先用 HTTP 级 E2E 覆盖业务旅程，再对少数 JS 交互补浏览器测试。

### 8.2 HTTP E2E 流程清单

| ID | 流程 | 步骤 | 关键断言 |
| --- | --- | --- | --- |
| TC-AUTH-023 | 注册 → 验证 → 登录 | 注册 → 捕获邮件 → 访问验证链接 → 登录 | 用户激活、登录成功、资料页可访问 |
| TC-AUTH-024 | 登录 → TFA → 访问 | 登录（密码）→ 跳转 TFA → 输入 TOTP → 访问受保护页 | TFA 前拒绝、TFA 后 200 |
| TC-AUTH-025 | 找回 → 重置 → 登录 | 提交邮箱 → 捕获链接 → 设置新密码 → 登录 | 新密码成功、旧密码失败 |
| TC-AUTH-026 | 改邮箱 | 登录 → 改邮箱 → 捕获确认链接 → 访问 → 用新邮箱登录 | 旧邮箱失效、新邮箱生效 |
| TC-AUTH-027 | 恢复码登录 | 启用 TFA → 登出 → 用恢复码登录 | 成功、恢复码失效 |
| TC-ADMIN-034 | Admin CRUD | 登录 admin → 创建 → 编辑 → 删除 | 列表/DB 状态 |
| TC-ADMIN-035 | 搜索/筛选/排序/分页 | 造数据 → 访问带参数 URL | 结果正确、计数正确 |
| TC-ADMIN-036 | Inline | 创建父+子 → 编辑 → 删除子 | 父子状态 |
| TC-ADMIN-037 | 导出 | 访问导出 URL | CSV 内容/表头 |
| TC-ADMIN-038 | 权限 | 匿名/普通/admin/未激活 | 重定向/403/200 |
| TC-ADMIN-039 | Inline + AJAX 外键 | 配置子模型 `ajax_refs` → 打开创建页 → 搜索 → 保存 | 页面 200、JSON 正确、父子落库（对应 C1） |
| TC-AUTH-028 | 令牌重复/过期 | 使用已验证/已过期链接再次访问 | 友好提示，不重复生效 |
| TC-ERROR-009 | 错误页 | 访问不存在路由、无权限路由 | 404/403 页面可渲染 |
| TC-I18N-007 | 语言切换 | 带 `?lang=zh` 访问 | 文本语言变化 |

### 8.3 HTTP E2E 示例

```python
# tests/e2e/test_auth_flow.py
import re

import pytest
from flask import url_for


def extract_token(link):
    match = re.search(r"[?&]token=([^&]+)", link)
    assert match, f"token not found in {link!r}"
    return match.group(1)


@pytest.mark.e2e
def test_signup_verify_login(app, client, mail_outbox):
    with app.test_request_context():
        register_url = url_for("user.register")
        verify_url = url_for("user.verify_email")
        login_url = url_for("user.login")
        profile_url = url_for("user.profile")

    # 1. 注册
    rv = client.post(
        register_url,
        data={
            "username": "e2e_user",
            "email": "e2e@example.com",
            "password": "password123",
            "confirm": "password123",
        },
        follow_redirects=True,
    )
    assert rv.status_code == 200

    # 2. 捕获验证邮件
    email = last_email(mail_outbox, "verify_email")
    token = extract_token(email["verification_link"])

    # 3. 验证邮箱
    rv = client.get(verify_url, query_string={"token": token}, follow_redirects=True)
    assert rv.status_code == 200
    assert "verified" in rv.text.lower()

    # 4. 登录
    rv = client.post(
        login_url,
        data={"username": "e2e_user", "password": "password123"},
        follow_redirects=True,
    )
    assert rv.status_code == 200

    # 5. 访问资料页
    rv = client.get(profile_url)
    assert rv.status_code == 200
    assert "e2e_user" in rv.text
```

> `last_email` 来自 4.3 的辅助函数。E2E 中每个测试使用唯一用户名/邮箱，避免数据库残留导致重复注册失败。

### 8.4 浏览器 E2E（可选）

前置条件：

- 新增 `selenium` 或 `playwright` 依赖（需询问）
- 启动 demo 应用或测试服务器
- 准备浏览器驱动

建议只覆盖：

- Tom Select 远程搜索
- 模态框打开/提交
- Flatpickr 日期选择
- Bootstrap 5 下拉/提示
- 移动端布局（可选）

标记：

```python
@pytest.mark.browser
@pytest.mark.slow
def test_admin_ajax_select(browser, live_server):
    browser.get(f"{live_server.url}/admin/...")
    ...
```

CI 中仅在 nightly 或手动触发，失败保存截图/HTML。

### 8.5 E2E 断言策略

每个 E2E 流程至少断言三类结果：

1. **HTTP 层**：状态码、重定向目标、`Location`。
2. **页面层**：关键文本、表单错误、成功提示。
3. **持久层**：数据库最终状态（用户激活、邮箱变更、记录删除）。
4. **副作用层**（如适用）：邮件 outbox、信号、导出文件内容。

避免只断言 `status_code == 200`；空白页、错误页也可能返回 200。

### 8.6 E2E 隔离与稳定性

- 每个测试使用唯一用户名/邮箱（`unique("e2e")`），不依赖固定账号。
- 每个测试前 `db.reset_all()` 或使用独立内存数据库；测试后清理 outbox。
- 使用 `url_for` 生成 URL，不硬编码蓝图前缀。
- 不依赖邮件发送顺序；用 `last_email(outbox, type)` 按类型取。
- 浏览器 E2E 使用显式等待（元素可见/可点击），不使用固定 `sleep`。
- 失败时保存截图、页面 HTML、浏览器 console 日志。

## 9. 性能测试方案

> **状态声明**：本章为目标设计/规划草案。当前仓库不存在 `tests/performance/` 目录或性能基准用例；依赖项（如 `pytest-benchmark`）尚未引入，相关指标待首测落地后建立。

### 9.1 目标

性能测试不是“证明快”，而是：

1. 建立基线；
2. 发现 N+1；
3. 防止明显退化；
4. 为优化提供数据。

### 9.2 工具

| 工具 | 用途 | 是否已有依赖 |
| --- | --- | --- |
| `pytest-benchmark` | 查询/渲染耗时基准 | 否，需新增（需询问） |
| SQLAlchemy `event` | 统计查询次数，检测 N+1 | 是（SQLAlchemy 自带） |
| `tracemalloc` | 内存快照 | 是（标准库） |
| `cProfile` / `py-spy` | 性能剖析 | 可选 |

如果不引入 `pytest-benchmark`，也可以先用 `time.perf_counter()` + `pytest.mark.performance` 做简单阈值断言。但基准工具更适合统计波动。

### 9.3 基准指标

结合本项目实际确定基准指标：

| 操作 | 数据量 | 目标 | 说明 |
| --- | ---: | --- | --- |
| Admin 列表查询 | 1,000 | < 500ms | 不含模板渲染 |
| Admin 搜索 | 10,000 | < 1000ms | 单列/关联列分别测 |
| Admin 筛选 | 10,000 | < 1000ms | 常用操作符 |
| 表单渲染 | 50 字段 | < 100ms | 不含 DB |
| 列表模板渲染 | 100 行 | < 500ms | 含 Jinja |
| 登录（含哈希） | 1 用户 | < 200ms | 含密码校验 |
| 批量删除 | 1,000 | < 5s | 含提交 |
| 注册+发信 | 1 用户 | < 300ms | 邮件 mock |

> 这些是**初始目标**，不是硬性 SLA。首次运行后应根据机器性能调整，并记录基线。

### 9.4 N+1 检测

```python
# tests/performance/test_n_plus_one.py
import pytest
from sqlalchemy import event


@pytest.mark.performance
def test_admin_list_has_no_n_plus_one(app, client, admin, login_as_admin, query_counter):
    with app.app_context():
        # 造 50 条父记录，每条 3 个子记录
        ...
        login_as_admin()

    query_counter.value = 0
    rv = client.get("/admin/parent/")
    assert rv.status_code == 200

    # 期望：count 查询 + 主查询 + eager load 查询，而不是 1 + 50。
    # MAX_QUERIES 首次实测后按基线调整，不要长期写死 5。
    MAX_QUERIES = 5
    assert query_counter.value <= MAX_QUERIES
```

`query_counter` fixture：

```python
@pytest.fixture
def query_counter(app):
    from sqlalchemy import event

    from flask_exts.datastore.sqla import db

    class Counter:
        value = 0

    counter = Counter()

    # 只监听当前 app 的引擎，避免多 app 测试互相计数。
    with app.app_context():
        engine = db.engine

    def before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
        counter.value += 1

    event.listen(engine, "before_cursor_execute", before_cursor_execute)
    yield counter
    event.remove(engine, "before_cursor_execute", before_cursor_execute)
```

使用建议：

- 每个请求前把 `counter.value = 0`，只统计该请求。
- 先记录当前查询数，再设阈值；不要一开始就写死 `<= 5`。
- 关联列渲染、Inline 子记录、导出最容易出现 N+1。

### 9.5 基准示例

```python
# tests/performance/test_query_perf.py
import pytest


@pytest.mark.performance
@pytest.mark.slow
def test_admin_list_query_performance(benchmark, app, client, admin, login_as_admin, seeded_db):
    with app.app_context():
        login_as_admin()

    def run():
        rv = client.get("/admin/admintestmodel/?page=1")
        assert rv.status_code == 200
        return rv

    result = benchmark.pedantic(run, rounds=5, iterations=10)
    assert result.status_code == 200
```

运行：

```bash
python -m pytest -q tests/performance -m performance
```

### 9.6 内存测试（可选）

```python
import tracemalloc


@pytest.mark.performance
def test_no_obvious_memory_leak(app, client):
    tracemalloc.start()
    baseline = tracemalloc.take_snapshot()

    for _ in range(100):
        client.get("/")

    current = tracemalloc.take_snapshot()
    top = current.compare_to(baseline, "lineno")[:10]
    # 断言没有异常增长；具体阈值需按实际调整
    assert sum(stat.size_diff for stat in top) < 10 * 1024 * 1024
```

内存测试容易受环境干扰，建议只做“趋势监控”，不作为硬门禁。

### 9.7 基线记录模板

首次运行后，把结果记录在团队可访问的位置（本文附录或 CI artifact）：

| 日期 | commit | 机器/CI | 场景 | 数据量 | p50 | p95 | 查询数 | 备注 |
| --- | --- | --- | --- | ---: | ---: | ---: | ---: | --- |
| 2026-11-07 | 未记录 | local | Admin 列表 | 1,000 | — | — | — | 初始基线待测 |
| 2026-11-07 | 未记录 | local | Admin 搜索 | 10,000 | — | — | — | 单列/关联列分开 |
| 2026-11-07 | 未记录 | local | 列表渲染 | 100 行 | — | — | — | 含 Jinja |
| 2026-11-07 | 未记录 | local | 登录 | 1 用户 | — | — | — | 含哈希 |

规则：

- 基线必须注明机器/CI 环境，否则不同机器不可比。
- 性能回归阈值建议“相对基线 +20%”，而不是绝对毫秒。
- 性能任务默认不阻塞合并；连续两次明显退化再升级为门禁。

## 10. 覆盖率与质量门禁

### 10.1 覆盖率指标

覆盖率目标与当前状态统一见第 13 节；本节只说明测量与门禁方法。

**先测真实基线再设门槛。** 历史报告中的 ~70% 不可直接采信。

### 10.2 命令

```bash
# 运行并收集
coverage run -m pytest -q

# 终端报告（含缺失行）
coverage report -m

# HTML 报告
coverage html
# 打开 htmlcov/index.html
```

或在 `pyproject.toml` 中配置：

```toml
[tool.coverage.run]
source = ["src/flask_exts"]
branch = true
omit = [
  "*/tests/*",
  "*/examples/*",
  "*/static/vendor/*",
]

[tool.coverage.report]
show_missing = true
skip_covered = true
```

### 10.3 质量门禁

当前 CI 与建议门禁：

1. 所有测试通过（Python 3.11–3.13）。（已实现：`tests` job）
2. 无新增 `skip`/`xfail`（除非有 issue 链接和期限）。（目标）
3. `ruff check` 通过（至少变更文件）。（已实现：`lint` job，仅 PR）
4. `sphinx -W` 通过（文档无 warning）。（已实现：`docs.yml`）
5. `djlint --check` 通过（变更模板）。（已实现：`lint` job）
6. 覆盖率不低于基线；新增代码行覆盖率 ≥ 80%。（目标；`coverage` job 目前只报告）
7. 性能基准不退化超过 20%（夜间任务，非阻塞合并）。（目标）

### 10.4 关键路径清单

以下路径必须 100% 覆盖：

- 扩展注册/依赖/初始化/关闭
- 登录/TFA/登出
- 注册/邮箱验证/改邮箱/找回密码
- CSRF 生成/校验/过期/篡改
- 令牌生成/校验/过期/失效
- Admin 列表/搜索/筛选/排序/分页/计数
- Admin CRUD/Inline/导出/批量删除
- 权限（匿名/普通/admin/未激活）
- 安全重定向

### 10.5 覆盖率基线记录

基线已首次测定；后续代码或依赖变化后重新测量并追加记录。10.1 的“目标”仍只是目标，不是已配置的 CI 门槛。

| 日期 | commit | 行覆盖 | 分支覆盖 | 函数覆盖 | 命令 | 备注 |
| --- | --- | ---: | ---: | ---: | --- | --- |
| 2026-11-10 | `171b40968f309c04ae3ad423696227c2767b0055` | 90% | 待测（未启 branch） | 待测 | `coverage run -m pytest -q` | 首次实测基线（229 passed, 1 skipped；全套 31.81s） |
| 2026-11-11 | `171b40968f309c04ae3ad423696227c2767b0055`（工作树含未提交改动） | 90% | 待测（未启 branch） | 待测 | `coverage run -m pytest -q` | 当前工作树复测（233 passed, 1 skipped；全套 32.79s；8601 statements, 866 missed） |
| 2026-11-11 | `171b40968f309c04ae3ad423696227c2767b0055`（工作树含未提交改动） | 90% | 待测（未启 branch） | 待测 | `coverage run -m pytest -q` | 修复 `ChoiceField` 后复测（245 passed, 1 skipped；全套 32.49s；8685 statements, 862 missed） |
| 2026-11-11 | `03006024d21167c0f6285a5724a3be5ef24d9a59`（v0.4.1） | 90% | 待测（未启 branch） | 待测 | `coverage run -m pytest -q` | 发布提交复测（245 passed, 1 skipped；全套 31.25s；8685 statements, 862 missed） |

规则：

- 基线必须与 commit 绑定；代码变化后重新测量。
- 目标改为“基线 + 新增代码 ≥ 80%”，避免整体数字掩盖新代码缺口。
- 覆盖率下降超过 1% 时，CI 给出 warning；下降超过 3% 时阻塞合并（阈值可按团队调整；当前尚未实现）。

### 10.6 排除项与理由

| 排除项 | 理由 |
| --- | --- |
| `*/static/vendor/*` | 第三方生成资源，不手改 |
| `*/examples/*` | 示例应用，不是库代码 |
| `*/tests/*` | 测试自身 |
| `*/migrations/*` | 若未来引入，单独统计 |
| `__main__` / CLI 入口 | 薄封装，由 CLI 用例覆盖 |

不要为了让数字好看而排除业务模块；任何新增排除项都必须在本表登记。

## 11. CI 流水线

> **状态声明**：仓库已有文档构建（`.github/workflows/docs.yml`）、发行构建（`.github/workflows/release.yml`）与测试 workflow（`.github/workflows/ci.yml`）。测试 workflow 提供 Python 3.11–3.13 矩阵、覆盖率报告与仅针对 PR 变更文件的 lint；E2E、浏览器与性能流水线仍为规划，未落地。

### 11.1 阶段设计

```text
┌──────────┐   ┌──────────┐   ┌──────────────┐   ┌──────────┐
│  Lint    │ → │  Unit    │ → │ Integration  │ → │ Coverage │
└──────────┘   └──────────┘   └──────────────┘   └──────────┘
                                                   │
                  ┌────────────────────────────────┘
                  ▼
           ┌──────────┐   ┌──────────────┐
           │  Docs    │   │ HTTP E2E     │
           └──────────┘   └──────────────┘
                  │
                  ▼
           ┌──────────────────────────┐
           │ Nightly: Browser + Perf  │
           └──────────────────────────┘
```

> 图中 Lint/Unit/Integration 为分层目标；当前 `ci.yml` 用单个 `tests` job 运行全量 pytest，`coverage` 独立成 job，`lint` 仅在 PR 上检查变更文件，Docs 由独立 workflow 执行。

### 11.2 命令

以下命令假定已完成 `uv sync` 并激活 `.venv`；未激活时给命令加 `uv run` 前缀。

```bash
# Lint
python -m ruff check .
python -m djlint src --check

# Unit（快速）
python -m pytest -q tests/unit

# Integration
python -m pytest -q tests/integration

# Coverage
coverage run -m pytest -q
coverage report -m

# Docs
python -m sphinx -b html docs docs/_build/html -W -n --keep-going

# E2E
python -m pytest -q tests/e2e -m e2e

# Performance（nightly）
python -m pytest -q tests/performance -m performance
```

### 11.3 测试工作流（已落地）

权威来源为仓库 `.github/workflows/ci.yml`；本节只描述职责，不复制完整 YAML。

| Job | 触发 | 内容 |
| --- | --- | --- |
| `tests` | push / PR / 手动 | Python 3.11、3.12、3.13 矩阵；`uv sync --locked` 后运行 `uv run pytest -q`。3.11 验证最低支持，3.13 验证主力版本 |
| `coverage` | push / PR / 手动 | Python 3.13；`uv run coverage run -m pytest -q` + `coverage report -m` + `coverage xml`，上传 `coverage.xml` artifact；未设置 `fail-under` 门槛 |
| `lint` | 仅 PR | 仅对变更文件运行 `ruff check`、`ruff format --check` 与 `djlint --check`，规避仓库历史格式问题 |

说明：

- Sphinx 依赖由 `pyproject.toml` 的 `docs` 依赖组维护（已包含在 `dev` 组中），`uv sync` 会一并安装，无需单独安装 `docs/requirements.txt`。
- `uv sync --locked` 要求 `uv.lock` 已提交且与 `pyproject.toml` 一致，否则 job 直接失败。
- 主力 Python 版本锚定 Debian stable（当前 3.13），最低支持保持 3.11；决策见 [`architecture.md` ADR-005](./architecture.md#adr-005-开发与主力验证-python-版本锚定-debian-stable)。
- 仓库存在历史 Ruff/模板格式问题，`ruff`/`djlint` 在 CI 中只检查**本次变更文件**，不要全量检查。
- 夜间任务可单独加 `browser` 与 `performance` job，允许失败但不阻塞主分支；当前尚未落地。

### 11.4 产物

- `coverage.xml`（`coverage-data` artifact，已实现）
- 目标产物：`coverage.xml` / `htmlcov/`、`benchmark.json`（pytest-benchmark）、浏览器失败截图/HTML、Sphinx 构建日志

### 11.5 本地与 CI 一致性

| 目标 | 本地命令 | CI 阶段 |
| --- | --- | --- |
| Lint | `uv run python -m ruff check .`（全量；CI 只查变更文件） | `lint` job（仅 PR） |
| 模板 | `uv run python -m djlint <changed> --check` | `lint` job（仅 PR，变更模板） |
| Unit | `uv run python -m pytest -q tests/unit` | `tests` job |
| Integration | `uv run python -m pytest -q tests/integration` | `tests` job |
| 覆盖率 | `uv run coverage run -m pytest -q` | `coverage` job（无门槛） |
| 文档 | `uv run python -m sphinx -b html docs docs/_build/html -W -n --keep-going` | 独立 `docs.yml` |
| E2E | `uv run python -m pytest -q tests/e2e -m e2e` | 未落地 |
| 性能 | `uv run python -m pytest -q tests/performance -m performance` | 未落地（Nightly） |

仓库 `Makefile` 已提供 `coverage` / `coverage-report`，本地优先复用，避免命令漂移。

### 11.6 失败排查顺序

1. 先看**第一个失败**，不要被后续级联失败干扰。
2. 重跑单个文件，排除数据库/临时文件残留。
3. 单独运行该测试，排除顺序依赖（尤其是 `mail_data` 这类模块级状态）。
4. 检查环境差异：Python 版本、依赖版本、SQLite 版本、时区。
5. 最后再怀疑实现；确认是缺陷后，先补失败测试，再修复。

## 12. 分阶段执行计划

> 四周计划按当前真实差距重排。集成测试已超额，不需要再“从 0 建”。

#### Phase 0：基线与清理（1–2 天）

- [x] 运行全量测试，记录通过数/耗时
- [ ] 运行 `coverage`，记录行/分支/函数覆盖率
- [ ] 注册 markers（unit/integration/e2e/browser/performance/slow）
- [ ] 新增 `mail_outbox` fixture，替换 `mail_data`
- [ ] 新增 `db_setup`、`user_factory`、`admin_user`、`authenticated_client`
- [ ] 清理 `tests/tmp`、`tests/integration/tmp` 等临时产物（确认是否应被忽略）

**验收：** 全量测试通过；覆盖率基线记录在文档/CI。

#### Phase 1：Unit 补强（第 1 周）

- [ ] TC-DATA-012/TC-DATA-013/TC-DATA-014：Query 搜索语义、过滤操作符、一对多计数
- [ ] TC-SEC-003/TC-SEC-004/TC-SEC-006/TC-SEC-007/TC-SEC-017：加密、序列化过期/篡改、TFA 恢复码
- [ ] TC-USER-012/TC-USER-013：`get_users`、`remove_user`
- [ ] TC-EMAIL-002/TC-EMAIL-003/TC-EMAIL-005/TC-EMAIL-006/TC-EMAIL-007：Emailer 错误路径
- [ ] TC-CLI-001～TC-CLI-006：Commands（含 `test_cli_runner` 示例）
- [ ] TC-FORM-010/TC-FORM-012/TC-FORM-015：CSRF 边界、formdata、InlineModelField
- [ ] TC-DATA-019～TC-DATA-027：事务、级联、外键、唯一约束
- [ ] TC-SIGNAL-001～TC-SIGNAL-006：信号载荷与 sender 错误
- [ ] TC-I18N-001～TC-I18N-006：语言、时区、复数、回退

**验收：** 新增 P0/P1 用例通过；关键路径 unit 覆盖补齐。

#### Phase 2：Integration 补强（第 2 周）

- [ ] TC-ADMIN-021：Inline + AJAX 外键（先写失败测试，修复 C1）
- [ ] TC-ADMIN-031：一对多搜索计数（修复 C2）
- [ ] TC-ADMIN-025/TC-ADMIN-026/TC-ADMIN-028：权限矩阵
- [ ] TC-ADMIN-014/TC-ADMIN-015：导出边界与类型
- [ ] TC-ADMIN-032/TC-ADMIN-033：URL 特殊字符、空结果/越界页
- [ ] TC-AUTH-018/TC-AUTH-021：TFA 完整流程、开放重定向
- [ ] TC-EMAIL-008：邮件内容
- [ ] TC-ERROR-001～TC-ERROR-008：404/403/405/500、令牌错误、CSRF 失败
- [ ] TC-DATA-022～TC-DATA-027：级联/约束在集成层的最终状态

**验收：** 验收清单中已确认需修复的 P0/P1 缺陷均有回归测试；View/Admin 与安全问题分别参照 `spec.md` 第 10.16 节和 `security.md` 第 11 节。

#### Phase 3：HTTP E2E（第 3 周）

- [ ] 创建 `tests/e2e/` 与 `conftest.py`
- [ ] TC-AUTH-023～TC-AUTH-028
- [ ] TC-ADMIN-034～TC-ADMIN-039
- [ ] TC-ERROR-009
- [ ] TC-I18N-007
- [ ] 统一使用 `mail_outbox`、`url_for` 与真实登录路由

**验收：** 10–20 个 E2E 流程通过；覆盖注册/登录/TFA/重置/改邮箱/Admin CRUD。

#### Phase 4：性能与 CI（第 4 周）

- [ ] 创建 `tests/performance/`
- [ ] N+1 检测（列表/搜索/Inline）
- [ ] 查询/渲染/登录基准
- [ ] 记录基线，设置合理阈值
- [x] CI 加入覆盖率报告与文档构建（`.github/workflows/ci.yml`、`docs.yml`；GitHub 实际运行待验证）
- [ ] CI 加入 E2E
- [ ] 夜间性能/浏览器任务（可选）

**验收：** 性能基线可重复；CI 绿灯；覆盖率达标。

#### Phase 5：可选浏览器 E2E

- [ ] 引入 Selenium/Playwright（需询问）
- [ ] Tom Select/模态框/Flatpickr 3–5 个流程
- [ ] 失败截图/HTML 产物

## 13. 测试目标与现状对照

本表是测试目标与快照状态的唯一维护位置；当前状态引用前按第 1.5 节复核，阶段行动见第 12 节。

| 项目 | 目标 | 当前真实状态 | 本方案动作 |
| --- | --- | --- | --- |
| 集成测试 | 30+ | 约 80+ 个集成测试函数，已超额 | 不再追求数量，补关键缺口 |
| E2E 测试 | 20+ | 0 | Phase 3 在 `tests/e2e/` 覆盖核心旅程；阶段验收见第 12 节 |
| 性能测试 | 15+ | 0 | Phase 4 建 `tests/performance/` 并建立基线；阶段行动见第 12 节 |
| 覆盖率 | ≥85% | 90%（2026-11-11 实测） | 已达标，作为基线监控防退化 |
| 分支覆盖 | ≥75% | 未测量 | 同上 |
| 函数覆盖 | ≥90% | 未测量 | 同上 |
| 关键路径 | 100% | 未系统定义 | 第 6/10 节已列清单 |
| 测试框架 | pytest + 插件 | pytest + pytest-cov | 按需引入 benchmark/browser |
| 测试目录 | unit/integration/e2e/performance | unit/integration | 按 Phase 创建 |
| Fixtures | app/client/db/user/admin/auth | 已有 app/client/admin/login_as_admin | 补 db_setup/user_factory/mail_outbox |
| 数据库事务 | 有设计 | 0 | 新增 TC-DATA-019～TC-DATA-027 |
| 错误处理 | 未明确 | 0 | 新增 TC-ERROR-001～TC-ERROR-008 |
| CI/CD | 集成 | `ci.yml` 已运行 Python 3.11–3.13 矩阵、覆盖率报告与 PR 变更文件 lint；`docs.yml` 构建文档；尚无 `fail-under` 门槛与 E2E | Phase 4 补 |
| 测试文档 | 完整 | 本文 v0.1 | 已补齐；按 Phase 0 升 v1.0 |

**对历史“完成声明”的说明：**

- 历史规划文档曾声称“95% 完成”，但“集成测试 30+ / E2E 20+ / 性能 15+”在验收清单中标记为“计划”，不是“已实现”。
- 其中描述的 `tests/integration/conftest.py`、`tests/e2e/`、`tests/performance/` 在当前仓库中并不存在（当前只有各子目录的 `conftest.py`）。
- 因此，本方案只把它当作“设计参考”，而不是“完成证明”。

## 14. 测试债务与改进清单

| # | 债务 | 位置 | 影响 | 建议 |
| --- | --- | --- | --- | --- |
| T1 | 模块级 `mail_data` | `tests/integration/usercenter/test_user_view.py` | 测试隔离差 | 改 `mail_outbox` fixture |
| T2 | 序列化过期断言被注释 | `tests/integration/security/test_core.py` | 过期路径无保护 | 用可控时间/短 max_age 补测 |
| T3 | `test_count_query` 只断言非空 | `tests/unit/datastore/sqla/test_query.py` | 计数错误无法发现 | 断言具体数值，加一对多用例 |
| T4 | 关联搜索未断言 count | `tests/integration/admin/sqla/test_search.py` | 分页总数可能错 | 加 `count` 断言 |
| T5 | Inline AJAX 未触发缺陷 | `tests/integration/admin/sqla/test_inline_ajax.py` | C1 可能漏测 | 配置子模型 `ajax_refs` 并访问页面 |
| T6 | `get_users`/`remove_user` 无测试 | `tests/integration/userstore/` | 接口不一致 | 补契约测试 |
| T7 | CLI 无测试 | 无 | 命令回归无保护 | 新增 `test_commands.py` |
| T8 | 无 E2E/性能基线 | 全局 | 跨模块流程与性能退化不可度量 | 按 Phase 3/4 落地；覆盖率基线已见 10.5 |
| T9 | 测试名偏泛 | `test_base`、`test_from` 等 | 可读性差 | 改为行为描述 |
| T10 | 注释/print 残留 | 多个测试 | 噪音 | 清理，保留必要说明 |
| T11 | 临时目录 | `tests/tmp`、`tests/integration/tmp`、`tests/integration/data` | 可能污染仓库 | 确认用途，加入 `.gitignore` 或清理 |
| T12 | 无 marker | 全局 | 无法快慢分离 | 注册并使用 |
| T13 | 未验证并行/随机顺序 | 全局 | 隐藏顺序依赖 | 引入 `pytest-xdist`/`pytest-randomly` 前先做隔离审计 |
| T14 | 仅 SQLite | 全局 | 生产数据库差异未覆盖 | 夜间跑 PostgreSQL，重点覆盖 C2/外键/大小写 |
| T15 | 文档示例与仓库未对齐 | 第 4、8、9 节 | 复制示例无法直接运行 | Phase 0 落地 fixture/marker，示例标注状态 |
| T16 | 统计数字易过期 | 1.1/1.2 | 文档失真 | 用 1.5 脚本定期重算 |
| T17 | 邮件/信号载荷契约未文档化 | `security/token_action.py` | 测试断言字段靠猜 | 在 7.12 固定字段表并加契约测试 |
| T18 | 覆盖率未设 CI 门槛 | 10.3/10.5 | 覆盖率回退无法自动阻断 | 以 10.5 基线设置阈值并接入 CI |
| T19 | 上传/导出临时文件路径不统一 | forms/admin 测试 | 残留或互相覆盖 | 统一用 `tmp_path` |

## 15. 测试编写规范与检查清单

### 15.1 命名

```python
# 推荐：条件 + 行为 + 期望
def test_login_with_wrong_password_returns_unified_error(): ...
def test_admin_search_by_related_column_counts_parent_rows(): ...
def test_inline_ajax_foreign_key_renders_create_page(): ...

# 避免
def test_base(): ...
def test_from(): ...
def test_1(): ...
```

### 15.2 结构

```python
def test_something(app, client):
    # Arrange：准备数据/登录/配置
    ...

    # Act：执行被测行为
    rv = client.get("/...")

    # Assert：断言状态、内容、数据库
    assert rv.status_code == 200
    assert "expected" in rv.text
```

### 15.3 检查清单

- [ ] 测试名能说明行为
- [ ] 使用 fixture，不共享模块级可变状态
- [ ] 不依赖执行顺序
- [ ] 不 `sleep`，用 `monkeypatch`/构造过期数据
- [ ] 不访问真实网络/SMTP/外部服务
- [ ] 断言状态码 + 关键内容 + 最终 DB 状态
- [ ] 覆盖错误路径与边界
- [ ] 使用 `pytest.raises(..., match=...)` 断言异常类型与消息
- [ ] 慢测试加 `@pytest.mark.slow` / `performance` / `browser`
- [ ] 清理临时文件/上传文件
- [ ] 测试代码保持英文（i18n 测试除外）
- [ ] 新增公共 fixture 有 docstring
- [ ] 变更缺陷时先写失败测试，再修复
- [ ] 不通过 `warnings.catch_warnings()` / `simplefilter()` 局部处理 `DeprecationWarning`；直接断言声明版本下的行为

### 15.4 反模式

| 反模式 | 问题 | 替代 |
| --- | --- | --- |
| `assert rv.status_code == 200` 唯一断言 | 页面可能空白/错误 | 加内容/DB 断言 |
| `xfail(raises=Exception)` | 掩盖未知异常 | 断言具体异常 |
| 注释掉断言 | 失去保护 | 修复或删除测试 |
| 模块级 list 收集状态 | 顺序/并行敏感 | fixture |
| 测试中复制生产逻辑 | 双重维护 | 调用真实函数 |
| 过度 mock | 测不到集成问题 | 只 mock 外部边界 |
| 依赖当前时间 | 间歇失败 | 固定时间/相对时间 |
| `catch_warnings()` + `simplefilter("error", DeprecationWarning)` | 掩盖对旧 API 的依赖，升级后仍可能失效 | 直接使用并断言新 API；弃用告警交给项目级 pytest 配置 |
| `try: import ... except ImportError` 版本回退 | 兼容分支长期滞留，测试矩阵翻倍 | 只支持声明版本；无法支持时提升下限并记录变更 |

### 15.5 断言层次

| 层次 | 何时必须 | 示例 |
| --- | --- | --- |
| HTTP | 所有请求 | `status_code`、`Location`、`Content-Type` |
| 页面内容 | 渲染类测试 | 关键文本、表单错误、成功提示 |
| 数据库 | 涉及写入/删除 | 重新查询最终状态 |
| 副作用 | 涉及邮件/文件/信号 | outbox、文件存在、信号收到 |
| 计数 | 列表/分页/搜索 | `count`、页数、总记录数 |

只断言状态码是不够的；只断言页面文本也不够。写入类测试至少覆盖“页面 + DB”两层。

### 15.6 提交前检查清单（测试部分）

- [ ] 新测试单独运行通过
- [ ] 新测试在随机顺序下通过（如已引入 `pytest-randomly`）
- [ ] 不依赖固定时间、网络、执行顺序
- [ ] 使用唯一用户名/邮箱/主键
- [ ] 临时文件写入 `tmp_path` 并自动清理
- [ ] 失败信息包含期望值与实际值
- [ ] 未新增无理由的 `skip`/`xfail`
- [ ] 修复缺陷时，先有失败测试，再有实现修改

## 16. 验收标准

本测试方案完成的定义：

**基础设施**

- [ ] `tests/e2e/`、`tests/performance/` 目录建立
- [ ] markers 注册，默认运行排除 performance/browser
- [ ] `mail_outbox`、`db_setup`、`user_factory`、`admin_user`、`authenticated_client` 可用
- [ ] `query_counter`、`seeded_db`、`tmp_upload_dir` 可用
- [x] 覆盖率命令可重复执行，基线已记录

**测试覆盖**

- [ ] 验收清单中已确认需修复的 P0/P1 缺陷均有回归测试；View/Admin 与安全问题分别参照 `spec.md` 第 10.16 节和 `security.md` 第 11 节
- [ ] 关键路径 100% 覆盖（第 10 节清单）
- [ ] 覆盖率达到第 13 节目标，并基于已测基线设置门槛
- [ ] HTTP E2E 达到第 13 节目标并覆盖核心旅程
- [ ] 性能测试达到第 13 节目标并记录可复现基线
- [ ] TC-DATA-019～TC-DATA-027：事务、级联、外键、唯一约束
- [ ] TC-ERROR-001～TC-ERROR-008：错误页与异常路径
- [ ] TC-SIGNAL-001～TC-SIGNAL-006：邮件/信号载荷契约
- [ ] TC-I18N-001～TC-I18N-006：语言、时区、复数、回退
- [ ] PostgreSQL 夜间矩阵至少覆盖计数、外键、大小写搜索

**质量门禁**

- [ ] Python 3.11–3.13 全绿
- [ ] `ruff`、`sphinx -W`、`djlint` 通过
- [ ] 无新增无理由 `skip`/`xfail`
- [ ] CI 运行 unit/integration/coverage/docs/E2E
- [ ] 夜间 performance/browser 任务（可选）

**文档**

- [ ] 顶部“文档版本/最后更新/数据快照”与实际一致
- [ ] 1.5 统计脚本可重复执行，数字与仓库一致
- [ ] 关键契约的验收字段均有明确映射或待补说明，并已核对其测试设计与证据
- [ ] 所有示例标注“现有/待补/目标”，不把规划写成现状
- [ ] 新增 fixture/测试模式有示例
- [ ] 目标对照表更新
- [ ] 测试债务清单持续维护

**v1.0 判定**

满足以下条件后，本文可从当前工作稿状态升级为可执行规范：

1. Phase 0 完成，基础设施与基线可用；
2. 第 7 节 P0 用例全部落地并通过；
3. 关键路径覆盖率 100%，整体覆盖率达标；
4. CI 绿灯，质量门禁生效；
5. 本文所有“待补”示例至少有 1 个可运行版本。

## 17. 文档维护与更新

### 17.1 更新触发条件

出现以下任一变化时，必须同步更新本文：

- 新增/删除测试目录、fixture、marker 或测试依赖
- 覆盖率基线、性能基线变化
- CI 门禁或 Python 版本矩阵调整
- `requirements.md` 中的契约，或 `spec.md` 中的模块边界、公开 API 变化
- 修复已知缺陷或新增缺陷，包括 `spec.md` 第 10.16 节及 `security.md` 第 11 节中的问题
- 测试策略、分层或验收标准变化

### 17.2 更新步骤

1. 运行 1.5 的统计脚本，更新 1.1/1.2 数字与顶部“数据快照”日期。
2. 更新 6.1 模块覆盖矩阵；按需更新 6.2 章节导航，并在各契约“验收”字段维护具体追溯映射。
3. 更新 7.x 用例状态（现有/待补/待修），新增缺陷对应用例。
4. 更新 10.5 覆盖率基线、9.7 性能基线。
5. 更新 14 测试债务、16 验收标准。
6. 若章节结构变化，同步更新目录与 `spec.md` 的互链。

### 17.3 相关文档

| 文档 | 用途 |
| --- | --- |
| [`requirements.md`](./requirements.md) | 行为契约与验收依据 |
| [`spec.md`](./spec.md) | 项目设计背景和 View/Admin 领域说明 |
| `testing.md`（本文） | 测试驱动：策略、用例、执行、门禁 |
| `flask-exts/AGENTS.md` | 开发规范、变更边界、命令 |
| `flask-exts/docs/testing.rst` | 项目内英文测试说明（与本文互补） |
