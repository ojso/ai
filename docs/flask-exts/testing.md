# 测试方案（Test-Driven）

> 本文是 [`spec.md`](./spec.md) 的**测试驱动文档**，独立维护。
>
> 更新时间：2026-11-19 08:12:16 +08:00
>
> **文档状态说明**：本文的测试目录与数量以 2026-11-18 的 HEAD `ca9f325fa2d43f53eaf14ca71a77ee75b1471406`（`0.5.0`）为基线。当前仓库没有 `tests/e2e/`、`tests/performance/`；`mail_outbox` 已在 `tests/integration/usercenter/test_user_view.py` 中落地。凡标“待补”“待修”“目标”“规划”的内容，均需按第 12 节分阶段实施后再视为已落地。重新统计现状的方法见 1.5。
>
> **使用方式**：修改代码前先对照 `requirements.md` 确认行为契约，再查相关架构/安全/领域约束；按变更设计测试并尽可能先验证失败，修改后运行实际可用的项目检查。缺陷修复优先复现并先写失败测试。本文中标记为目标的规划不代表已实现；当前 CI 实现范围见第 11 节。

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

- **第一次接触项目**：0 → 1 → 2 → 3 → 4
- **要写新测试**：4 → 5 → 6 → 7 → 15
- **要补 E2E / 性能**：8 → 9 → 11 → 12
- **要做质量门禁**：10 → 11 → 16
- **要修缺陷**：相关契约与问题清单（`spec.md` 第 10.16 节 / `security.md` 第 11 节）→ 本文 7 → 12

### 0.4 状态图例

- **现有**：当前仓库已有测试
- **待补**：尚无测试，需要新增
- **待修**：已有测试但断言不足或未触发缺陷
- **目标**：目标结构，当前未落地
- **规划**：尚未进入执行计划

## 1. 测试现状盘点

### 1.1 当前规模

- **测试文件**
  - 当前值：52 个 `test_*.py`
  - 说明：全部位于 `tests/unit/` 与 `tests/integration/`

- **测试函数**
  - 当前值：341 个
  - 说明：以 `def test_...` 统计（2026-11-18 `0.5.0`，HEAD `ca9f325`）

- **断言**
  - 当前值：约 1197 处
  - 说明：按 `\bassert\b` 全文匹配统计（复现脚本见第 1.5 节），不含 `pytest.raises`

- **测试框架**
  - 当前值：pytest
  - 说明：`pyproject.toml` 配置

- **覆盖率工具**
  - 当前值：`pytest-cov` / `coverage`
  - 说明：已列入 `dev` 组；`[tool.coverage.run] source = ["src/flask_exts"]` 只统计库代码；已测定基线，CI 每轮报告覆盖率，尚无 `fail-under` 门槛

- **E2E 目录**
  - 当前值：无
  - 说明：`tests/e2e/` 尚未创建

- **性能目录**
  - 当前值：无
  - 说明：`tests/performance/` 尚未创建

- **浏览器测试**
  - 当前值：无
  - 说明：未引入 Selenium/Playwright

- **基准工具**
  - 当前值：无
  - 说明：未引入 `pytest-benchmark`

- **数据工厂**
  - 当前值：无
  - 说明：未引入 `factory-boy` / `faker`

- **最近完整测试运行**
  - 当前值：330 passed
  - 说明：2026-11-16 复跑；Python 3.13.5；提交 `134929564791b2d5bc843685650ee8ccd13d1bc6`；0 跳过；31.79s；命令 `.venv/bin/python -m pytest -q`；`ruff check` 与 `ruff format --check` 通过

`pyproject.toml` 当前 pytest 配置：

```toml
[tool.pytest.ini_options]
minversion = "8.0"
testpaths = ["tests"]
addopts = "-ra --strict-markers --strict-config"
filterwarnings = ["error::DeprecationWarning"]
```

注意 `--strict-markers`：**新增 marker 必须注册**，否则测试会直接报错。

### 1.2 现有测试分布

按 2026-11-18 `0.5.0`（HEAD `ca9f325`）统计，各区域合计与第 1.1 节的 341 个测试函数一致。

- `integration/admin`
  - 测试函数数：57
  - 主要文件：完整入口见 1.2.1
  - 评价：历史快照覆盖 CRUD、Inline、搜索、排序、分页、批量操作、导出、复合主键、inactive admin、can_edit 边界；本轮补充负 offset 场景

- `unit/forms`
  - 测试函数数：38
  - 主要文件：`test_json.py`、`test_datetime.py`、`test_filefield.py`、`test_uploadfile.py`、`test_select.py`、`test_wtforms.py`、`tests/unit/forms/form/test_form.py`、`tests/unit/forms/validators/test_file.py`
  - 评价：覆盖字段、文件、选择字段、CSRF 生成/校验、派生密钥和关闭配置；本轮补充 `FileSize` 基于 `Content-Length`/seek 且不读取整份文件的用例；边界与错误路径仍可补

- `unit/extension_core`
  - 测试函数数：32
  - 主要文件：`test_registry.py`、`test_manager.py`
  - 评价：覆盖依赖排序、循环依赖、幂等、关闭、异常隔离、内置扩展装配

- `unit/admin`
  - 测试函数数：29
  - 主要文件：`test_mockview.py`、`test_pagination.py`、`test_type_formatters.py`、`test_admin.py`、`test_view.py`
  - 评价：覆盖视图元数据、格式化、分页 URL 编码、负页码夹取、页码链接、默认视图选择与布尔格式化转义、`login_required_functions` 声明与非法名称校验，偏“配置读取”

- `integration/usercenter`
  - 测试函数数：22
  - 主要文件：`tests/integration/usercenter/test_user_view.py`
  - 评价：覆盖注册、重复/非法邮箱、改邮箱确认/密码/非法地址、重发验证、登录前置返回 403、禁用账号拒绝登录/拒绝完成 pending TFA/旧会话即时失效、TFA 启用/关闭/登录/防绕过、失败登录与失败 TFA 锁定/解锁、改密码、找回/重置、恢复码

- `unit/datastore`
  - 测试函数数：14
  - 主要文件：`test_db.py`、`test_query.py`
  - 评价：覆盖单例、重绑定、内存 SQLite、JOIN 复用、类型推断；计数正确性未覆盖

- `unit/security`
  - 测试函数数：70
  - 主要文件：`tests/unit/security/test_authorizer.py`、`tests/unit/security/test_simple_authorizer.py`、`tests/unit/security/test_rbac_authorizer.py`、`tests/unit/security/test_tfa.py`、`tests/unit/security/test_urls.py`
  - 评价：`test_authorizer.py` 覆盖基类 `check_view_access()`（含 active `admin` 直接放行与 inactive admin 不走捷径）、`requires_login()`、`allow_by_roles()` 与 `authorize()`；`test_simple_authorizer.py` 覆盖 admin、inactive admin、普通用户、无角色/无用户、`allow_access` 方法级登录限制、非公开视图、`role_need` 与 `login_required_functions`；`test_rbac_authorizer.py` 覆盖 `Role`/`Permission`/`Predicate`/`All`/`Any`/`Not`/`Authenticated`、视图声明优先级、loader 优先级、查询 API、配置选择、共用登录门与既有规则兼容；TFA 涉及 URI、生成/校验；URL 涉及外部/畸形拒绝和本地路径放行

- `unit/frontend`
  - 测试函数数：9
  - 主要文件：`test_plugin_manager.py`、`test_base.py`、宏测试
  - 评价：覆盖注册、排序、循环依赖、资源拼接

- `integration/builtin_extensions`
  - 测试函数数：25
  - 主要文件：`test_login.py`、`test_admin_views.py`
  - 评价：覆盖 JWT 签发/校验（`pwd`、`amr`、算法白名单、密钥校验、`iat` 必填/leeway、Bearer 大小写、`id`/`amr` 严格解析）、蓝图、默认视图

- `integration/userstore`
  - 测试函数数：10
  - 主要文件：`test_sqla_userstore.py`
  - 评价：覆盖模型注册、基础 CRUD、角色与账号锁定（失败计数、成功登录清零、锁定过期、退避上限、非法策略）、时间戳 aware UTC、TOTP secret 只 flush 不提交；`get_users`/`remove_user` 未覆盖

- `unit/builtin_extensions`
  - 测试函数数：8
  - 主要文件：`test_babel.py`、`test_exts.py`、`test_frontend.py`
  - 评价：覆盖 Babel、扩展注册、Jinja 全局

- `integration/security`
  - 测试函数数：23
  - 主要文件：`tests/integration/security/test_core.py`、`test_security_headers.py`
  - 评价：覆盖密钥派生、哈希、序列化、邮箱验证、重置密码、密码变更使 session 失效、`SECRET_KEY` 初始化校验、未知 serializer 保守默认值，以及安全 Cookie/响应头默认值、HTTPS 校验、默认值开关与反向代理下的 HSTS

- `unit/emailer`
  - 测试函数数：4
  - 主要文件：`test_base.py`、`test_smtp.py`
  - 评价：基础信号路径、缺失 sender 的日志脱敏、校验证书/主机名的 context、发送头字段与 TLS 错误包装

- `commands`
  - 测试函数数：0
  - 主要文件：无
  - 评价：CLI 完全未测试

#### 1.2.1 Admin 测试文件清单

以下文件路径已与 2026-11-13 的仓库 HEAD `445b03d` 核对；各文件的断言覆盖未逐项审计。文件名不证明相关断言存在或测试通过。

- `tests/integration/admin/test_admin.py`
- `tests/integration/admin/model/test_mockview.py`
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

- **无 HTTP 级 E2E 流程测试**
  - 影响：跨模块流程（注册→验证→登录→TFA）只能靠零散集成测试拼接
  - 对应目标：目标见第 13 节

- **无性能基准**
  - 影响：无法量化列表查询、搜索、渲染、认证的退化
  - 对应目标：目标见第 13 节

- **覆盖率无 CI 门槛**
  - 影响：覆盖率回退无法自动阻断
  - 对应目标：基线见第 10.5 节；`ci.yml` 已报告覆盖率，门槛见第 10.3 节

- **CI 未检查本套 Markdown 与 demo smoke**
  - 影响：外部文档死链、demo 启动问题不会被现有 CI 捕获
  - 对应目标：仓库 Sphinx 构建与测试 CI 已在 `docs.yml` / `ci.yml`；本套文档的链接检查与 demo smoke 仍待接入

- **一对多搜索计数未断言**
  - 影响：`build_count` 重复计数风险可能潜伏
  - 对应目标：新增

- **Inline + AJAX 外键未覆盖**
  - 影响：`create_ajax_loader` 参数缺陷可能未被触发
  - 对应目标：新增

- `UserStore.get_users` / `remove_user` 未覆盖
  - 影响：接口契约与实现不一致
  - 对应目标：新增

- **CLI 未覆盖**
  - 影响：建表/建用户命令回归无保护
  - 对应目标：新增

- **安全令牌过期测试被注释**
  - 影响：过期路径没有自动化保护
  - 对应目标：新增

- **无浏览器/JS 测试**
  - 影响：前端插件、Tom Select、模态框等只能人工验证
  - 对应目标：可选

### 1.4 与目标基线的差距

目标、当前状态与差距统一见第 13 节，本节不重复指标。当前优先事项为 E2E、性能基线，以及覆盖率门槛（`ci.yml` 已报告覆盖率，尚未设置 `fail-under`）；阶段行动见第 12 节。

### 1.5 统计口径与重新统计

本文的 52 / 341 / 1197 已按 2026-11-18 `0.5.0`（HEAD `ca9f325fa2d43f53eaf14ca71a77ee75b1471406`）重新统计。统计是文本近似值；代码更新后应重新运行以下脚本：

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

更新本文时，同步修改 1.1、1.2 的数字；发布状态快照只在 `release.md` 第 1 节维护。

**统计口径**：

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

- **Unit**
  - 建议占比：~55%
  - 运行时间：< 5s
  - 依赖：无 Flask 或最小 app

- **Integration**
  - 建议占比：~30%
  - 运行时间：< 60s
  - 依赖：Flask app + 内存 SQLite

- **HTTP E2E**
  - 建议占比：~10%
  - 运行时间：< 60s
  - 依赖：Flask test client + 邮件捕获

- **Browser E2E**
  - 建议占比：~3%
  - 运行时间：分钟级
  - 依赖：浏览器 + 运行中的服务

- **Performance**
  - 建议占比：~2%
  - 运行时间：分钟级
  - 依赖：大数据集 + benchmark

### 2.2 各层职责

- **Unit**
  - 测什么：纯函数、Query 构造、格式化器、插件排序、Registry 状态机、密钥/哈希/序列化
  - 不测什么：路由、模板、数据库提交

- **Integration**
  - 测什么：视图 + 表单 + DB + 扩展协作；HTTP 状态码与页面关键内容
  - 不测什么：真实浏览器、外部 SMTP、跨进程

- **HTTP E2E**
  - 测什么：完整用户旅程：注册→验证→登录→TFA→资料→登出；Admin CRUD
  - 不测什么：像素级 UI、JS 交互

- **Browser E2E**
  - 测什么：JS 插件、Tom Select、模态框、日期选择器、响应式布局
  - 不测什么：业务规则（已由下层覆盖）

- **Performance**
  - 测什么：查询次数、查询耗时、渲染耗时、内存增长
  - 不测什么：正确性（由功能测试覆盖）

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

当前测试默认串行执行；原模块级 `mail_data` 已由 function-scope `mail_outbox` fixture 取代。目标状态：

- **并行执行**
  - 工具：`pytest-xdist`
  - 是否已有：否
  - 建议：可选；模块级可变状态已消除

- **随机顺序**
  - 工具：`pytest-randomly`
  - 是否已有：否
  - 建议：可选；用于暴露顺序依赖

- **超时保护**
  - 工具：`pytest-timeout`
  - 是否已有：否
  - 建议：可选；防止挂起

- **失败重试**
  - 工具：`pytest-rerunfailures`
  - 是否已有：否
  - 建议：**不推荐**作为常规手段

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

- **文件名**：`test_<主题>.py`；一个文件聚焦一个模块或一个流程
- **测试函数**：`test_<条件>_<行为>_<期望>`
- **类**：只在需要共享 fixture/参数化时使用 `TestXxx`，不要用它隐藏测试
- **放置**：纯逻辑放 `unit/`；涉及 Flask app/DB/路由放 `integration/`；跨模块旅程放 `e2e/`；基准放 `performance/`
- **测试模型**：放对应目录的 `models/` 或 `tests/fixtures/models.py`，不要在生产模块中定义
- **静态数据**：上传/导出素材放 `tests/integration/data/`；运行时产物放 `tests/tmp/` 或 `tmp_path`
- **翻译**：i18n 测试用 `tests/translations/`，不要复用生产翻译目录

### 3.5 数据库与运行环境矩阵

当前所有测试使用内存 SQLite（`sqlite://`）。这对速度有利，但不能覆盖生产数据库差异：

- **大小写敏感**
  - SQLite（当前）：默认不敏感
  - PostgreSQL：敏感
  - MySQL/MariaDB：取决于 collation

- `LIKE` 行为
  - SQLite（当前）：默认不区分大小写
  - PostgreSQL：区分大小写
  - MySQL/MariaDB：取决于 collation

- **外键约束**
  - SQLite（当前）：默认关闭，需 `PRAGMA foreign_keys=ON`
  - PostgreSQL：默认开启
  - MySQL/MariaDB：默认开启

- **并发/锁**
  - SQLite（当前）：单写者
  - PostgreSQL：MVCC
  - MySQL/MariaDB：MVCC/表锁

- `count` + JOIN
  - SQLite（当前）：同样会重复计数
  - PostgreSQL：同
  - MySQL/MariaDB：同

- **日期/时区**
  - SQLite（当前）：文本存储
  - PostgreSQL：原生类型
  - MySQL/MariaDB：原生类型

建议：

1. **日常开发**：继续用 SQLite，保持测试快速。
2. **合并前/夜间**：至少用 PostgreSQL 跑一遍 `integration/`，重点覆盖 CR-002（一对多计数）、外键、大小写搜索。
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

- `app`
  - 作用域：function
  - 状态：现有
  - 作用：每个测试独立 app

- `client`
  - 作用域：function
  - 状态：现有
  - 作用：`app.test_client()`

- `admin`
  - 作用域：function
  - 状态：现有
  - 作用：`integration/admin/conftest.py`，返回 Admin 实例

- `login_as_admin`
  - 作用域：function
  - 状态：现有
  - 作用：可调用 fixture，在 `db.reset_all()` 后创建并登录 admin

- `sqla_view_factory`
  - 作用域：function
  - 状态：现有
  - 作用：构造 `MockSqlaView`

- `db_setup`
  - 作用域：function
  - 状态：待补
  - 作用：在 app context 内 `db.reset_all()`，结束时 `db.session.remove()`

- `user_factory`
  - 作用域：function
  - 状态：待补
  - 作用：创建用户，支持 `username/password/email/is_active/roles`

- `admin_user`
  - 作用域：function
  - 状态：待补
  - 作用：创建激活的 admin 角色用户

- `authenticated_client`
  - 作用域：function
  - 状态：待补
  - 作用：已登录的 `client`（session 注入或走登录路由）

- `admin_client`
  - 作用域：function
  - 状态：待补
  - 作用：已登录且具备 admin 角色的 client

- `mail_outbox`
  - 作用域：function
  - 状态：现有
  - 作用：每个测试独立的邮件列表；`setup` 用 `EmailSender(mail_outbox)` 注册 sender

- `csrf_client`
  - 作用域：function
  - 状态：待补
  - 作用：开启 CSRF 的 client，并提供取 token 的辅助

- `query_counter`
  - 作用域：function
  - 状态：待补
  - 作用：统计当前 app 引擎的 SQL 次数，用于 N+1 检测

- `seeded_db`
  - 作用域：function
  - 状态：待补
  - 作用：预置 100/1000/10000 条数据，供性能测试

- `app_factory`
  - 作用域：function
  - 状态：待补
  - 作用：创建独立 app，用于多 app/重绑定测试

- `tmp_upload_dir`
  - 作用域：function
  - 状态：待补
  - 作用：基于 `tmp_path` 的上传目录，测试后自动清理

> “待补”表示本文给出设计，但仓库尚未实现。落地顺序见第 12 节 Phase 0。

### 4.3 `mail_outbox`（已实现）

`tests/integration/usercenter/test_user_view.py` 现使用 function-scope fixture：

```python
@pytest.fixture
def mail_outbox():
    """Per-test mailbox for messages captured by EmailSender."""
    return []

class EmailSender(Sender):
    def __init__(self, outbox):
        self.outbox = outbox

    def send(self, data):
        self.outbox.append(data)
```

`setup` fixture 注册该 sender：

```python
@pytest.fixture
def setup(self, app, client, mail_outbox):
    ...
    email_sender = EmailSender(mail_outbox)
    email.register_sender("verify_email", email_sender)
    email.register_sender("reset_password", email_sender)
```

测试通过 `mail_outbox` 参数读取邮件，不再共享模块级列表：

```python
def test_signup_sends_verification(app, client, mail_outbox):
    ...
    email = mail_outbox[-1]
    assert email["email"] == "user@example.com"
    assert "verification_link" in email
```

优点：每个测试独立 outbox，可重排、可并行、失败信息更清晰。

> 邮件 `data` 的字段契约见 7.12。`verify_email` 用 `verification_link` + `verification_token`，`reset_password` 用 `reset_password_link` + `reset_password_token`；两者都带 `email` 和 `type`。

### 4.4 `authenticated_client` 设计

两种方式：

**方式 A**：直接写 session（快，适合大多数测试）

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

**方式 B**：走真实登录路由（慢，适合 E2E）

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

- `function`
  - 适用：绝大多数测试
  - 风险：安全，推荐默认

- `module`
  - 适用：只读、不可变数据
  - 风险：状态泄漏

- `session`
  - 适用：极少数昂贵资源（浏览器驱动）
  - 风险：必须显式清理

- `class`
  - 适用：同类测试共享
  - 风险：谨慎

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
- **外部输入**：搜索词、文件名、URL 参数用表驱动覆盖边界（空串、空格、`&`、非 ASCII、超长）。
- **上传/导出**：一律写 `tmp_path`，不提交二进制产物。
- **网络**：不访问真实 SMTP、HTTP、DNS；在边界处 mock。

## 6. 测试覆盖矩阵

### 6.1 模块覆盖矩阵

图例：✅ 已有较好覆盖；⏳ 部分覆盖/需补强；❌ 基本没有。

- **Extension 系统**
  - Unit：✅
  - Integration：⏳
  - HTTP E2E：❌
  - Performance：❌
  - 主要缺口：晚注册待补；shutdown 异常隔离与现有测试行为冲突（CR-011）；E2E 不需要

- **Datastore / Query**
  - Unit：✅
  - Integration：⏳
  - HTTP E2E：❌
  - Performance：⏳
  - 主要缺口：计数正确性、N+1、复杂过滤

- **Admin 基础**
  - Unit：✅
  - Integration：✅
  - HTTP E2E：⏳
  - Performance：❌
  - 主要缺口：权限矩阵、导出类型、URL 特殊字符

- **Admin Inline**
  - Unit：⏳
  - Integration：✅
  - HTTP E2E：⏳
  - Performance：❌
  - 主要缺口：Inline + AJAX 外键、复杂关系

- **Forms**
  - Unit：✅
  - Integration：✅
  - HTTP E2E：⏳
  - Performance：❌
  - 主要缺口：CSRF 过期/篡改、文件边界、Recaptcha

- **Security**
  - Unit：✅
  - Integration：✅
  - HTTP E2E：⏳
  - Performance：❌
  - 主要缺口：令牌过期、加密篡改、TFA 恢复码

- **UserStore**
  - Unit：❌
  - Integration：⏳
  - HTTP E2E：⏳
  - Performance：❌
  - 主要缺口：`get_users`、`remove_user`、profile

- **UserCenter**
  - Unit：⏳
  - Integration：✅
  - HTTP E2E：⏳
  - Performance：❌
  - 主要缺口：完整旅程、并发/重复提交、错误页

- **Emailer**
  - Unit：✅
  - Integration：⏳
  - HTTP E2E：⏳
  - Performance：❌
  - 主要缺口：SMTP 错误、默认发送器、未知类型

- **Frontend**
  - Unit：✅
  - Integration：⏳
  - HTTP E2E：❌
  - Performance：❌
  - 主要缺口：插件资源顺序、模板集成

- **Commands**
  - Unit：❌
  - Integration：❌
  - HTTP E2E：❌
  - Performance：❌
  - 主要缺口：建表、建用户、错误处理

- **Babel / i18n**
  - Unit：✅
  - Integration：⏳
  - HTTP E2E：⏳
  - Performance：❌
  - 主要缺口：语言切换、时区、复数

**关键路径**（必须 100% 覆盖）：

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

### 6.2 需求追溯与用例导航

`requirements.md` 定义 `REQ-*` 契约，本文维护测试设计。具体 `REQ → TC → 测试入口` 唯一维护在 [`requirements.md`](./requirements.md) 各契约的“验收”字段；`TC` 的编号规则和历史别名见第 6.3 节。下文只按能力导航，不推断契约关联、层级或覆盖情况；用例层级、状态及断言以各用例条目为准。

- **扩展生命周期、依赖、关闭**：[扩展测试](#71-extension-系统)
- **数据库绑定、会话、Query、事务**：[数据测试](#72-datastore--query)、[事务与约束](#711-数据库事务与约束)
- **Admin 列表、CRUD、Inline、导出、权限**：[Admin 测试](#73-admin)
- **表单、CSRF、上传**：[表单测试](#74-forms)
- **授权、令牌、加密、TFA**：[安全测试](#75-security)、[用户中心测试](#77-usercenter)
- **用户存储**：[UserStore 测试](#76-userstore)
- **注册、邮箱、密码**：[用户中心测试](#77-usercenter)
- **邮件与信号**：[邮件测试](#78-emailer)、[信号测试](#712-错误处理与信号契约)
- **前端插件与模板**：[前端测试](#79-frontend)
- **CLI**：[命令测试](#710-commands)
- **i18n / 时区**：[国际化测试](#713-i18n时区与复数)
- **错误处理**：[错误处理测试](#712-错误处理与信号契约)
- **端到端流程**：[HTTP E2E 流程](#82-http-e2e-流程清单)

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

**历史用例迁移（2026-11-09）**：本目录已有用例按下文一对一迁移，范围内从起始编号按顺序对应。旧 `TST-*` 编号保留为历史别名；更早的不带 `TST-` 的编号仍可先补上 `TST-` 再查下文。仅适用于下文所列范围，不能据此前缀或相同序号猜测其他映射。

- `TST-E-01`～`TST-E-20`：`TC-EXT-001`～`TC-EXT-020`
- `TST-D-01`～`TST-D-18`：`TC-DATA-001`～`TC-DATA-018`
- `TST-A-01`～`TST-A-33`：`TC-ADMIN-001`～`TC-ADMIN-033`
- `TST-F-01`～`TST-F-17`：`TC-FORM-001`～`TC-FORM-017`
- `TST-S-01`～`TST-S-21`：`TC-SEC-001`～`TC-SEC-021`
- `TST-U-01`～`TST-U-15`：`TC-USER-001`～`TC-USER-015`
- `TST-UC-01`～`TST-UC-22`：`TC-AUTH-001`～`TC-AUTH-022`
- `TST-M-01`～`TST-M-09`：`TC-EMAIL-001`～`TC-EMAIL-009`
- `TST-FE-01`～`TST-FE-10`：`TC-FRONTEND-001`～`TC-FRONTEND-010`
- `TST-CLI-01`～`TST-CLI-06`：`TC-CLI-001`～`TC-CLI-006`
- `TST-TX-01`～`TST-TX-09`：`TC-DATA-019`～`TC-DATA-027`
- `TST-ERR-01`～`TST-ERR-08`：`TC-ERROR-001`～`TC-ERROR-008`
- `TST-SIG-01`～`TST-SIG-06`：`TC-SIGNAL-001`～`TC-SIGNAL-006`
- `TST-I18N-01`～`TST-I18N-06`：`TC-I18N-001`～`TC-I18N-006`
- `TST-E2E-AUTH-01`～`TST-E2E-AUTH-06`：`TC-AUTH-023`～`TC-AUTH-028`
- `TST-E2E-ADMIN-01`～`TST-E2E-ADMIN-06`：`TC-ADMIN-034`～`TC-ADMIN-039`
- `TST-E2E-ERR-01`：`TC-ERROR-009`
- `TST-E2E-I18N-01`：`TC-I18N-007`

迁移仅改变本文档集的编号和引用，不改变用例内容、状态或执行结果。此前带能力段的 `TST-*` 和 `TEST-*` 文档示例未分配；如仓库或外部记录已使用，应先核实实际指向，保留历史引用，不推定与某条 `TC-*` 等价。后续变更或拆分编号时先核实关联并记录映射，按授权同步受影响的文档、测试代码和工具；仓库不可见时记录未核验。

## 7. 详细测试用例设计

> 说明：
>
> - **类型**：U=Unit，I=Integration，E=HTTP E2E，P=Performance。
> - **优先级**：P0=必须，P1=应该，P2=可选。
> - **状态**：现有=已有测试；待补=建议新增；待修=已有测试但断言不足。

### 7.1 Extension 系统

- `TC-EXT-001`
  - 场景：注册合法扩展
  - 类型：U
  - 优先级：P0
  - 状态：现有
  - 关键断言：返回实例，name 正确

- `TC-EXT-002`
  - 场景：重复名称注册
  - 类型：U
  - 优先级：P0
  - 状态：现有
  - 关键断言：抛 `ExtensionError`，消息含名称

- `TC-EXT-003`
  - 场景：非 Extension 类注册
  - 类型：U
  - 优先级：P0
  - 状态：现有
  - 关键断言：抛 `ExtensionError`

- `TC-EXT-004`
  - 场景：非法名称（空/非 ASCII/特殊字符）
  - 类型：U
  - 优先级：P0
  - 状态：现有
  - 关键断言：抛 `ExtensionError`

- `TC-EXT-005`
  - 场景：依赖项先于依赖者初始化
  - 类型：U
  - 优先级：P0
  - 状态：现有
  - 关键断言：依赖项在记录顺序中先于依赖者

- `TC-EXT-006`
  - 场景：无依赖扩展保持注册顺序
  - 类型：U
  - 优先级：P1
  - 状态：现有
  - 关键断言：顺序稳定

- `TC-EXT-007`
  - 场景：深链依赖 A→B→C
  - 类型：U
  - 优先级：P1
  - 状态：现有
  - 关键断言：C→B→A

- `TC-EXT-008`
  - 场景：缺失依赖
  - 类型：U
  - 优先级：P0
  - 状态：现有
  - 关键断言：抛 `ExtensionNotFoundError`

- `TC-EXT-009`
  - 场景：循环依赖
  - 类型：U
  - 优先级：P0
  - 状态：现有
  - 关键断言：抛 `ExtensionDependencyError`，消息含环

- `TC-EXT-010`
  - 场景：自依赖
  - 类型：U
  - 优先级：P1
  - 状态：现有
  - 关键断言：抛 `ExtensionDependencyError`

- `TC-EXT-011`
  - 场景：`init` 幂等
  - 类型：U
  - 优先级：P0
  - 状态：现有
  - 关键断言：第二次不重复调用

- `TC-EXT-012`
  - 场景：`post_init` 前必须 `init`
  - 类型：U
  - 优先级：P0
  - 状态：现有
  - 关键断言：抛 `ExtensionInitError`

- `TC-EXT-013`
  - 场景：`post_init` 幂等
  - 类型：U
  - 优先级：P0
  - 状态：现有
  - 关键断言：第二次不重复调用

- `TC-EXT-014`
  - 场景：`post_init` 按依赖顺序
  - 类型：U
  - 优先级：P1
  - 状态：现有
  - 关键断言：顺序正确

- `TC-EXT-015`
  - 场景：`shutdown` 逆序
  - 类型：U
  - 优先级：P0
  - 状态：现有
  - 关键断言：与初始化相反

- `TC-EXT-016`
  - 场景：`shutdown` 单扩展异常隔离
  - 类型：U
  - 优先级：P1
  - 状态：现有
  - 关键断言：继续关闭其他扩展并产生 warning；`BaseException` 不被吞掉；`test_shutdown_exception_is_isolated`

- `TC-EXT-017`
  - 场景：内置扩展图可初始化
  - 类型：I
  - 优先级：P0
  - 状态：现有
  - 关键断言：所有内置扩展初始化成功

- `TC-EXT-018`
  - 场景：Admin 收集 Portal/UserCenter 视图
  - 类型：I
  - 优先级：P0
  - 状态：现有
  - 关键断言：视图注册到 admin

- `TC-EXT-019`
  - 场景：晚注册扩展
  - 类型：U
  - 优先级：P2
  - 状态：待补
  - 关键断言：文档化行为：不回溯扫描

- `TC-EXT-020`
  - 场景：`has_extension` 语义
  - 类型：U
  - 优先级：P2
  - 状态：待补
  - 关键断言：明确“已注册”还是“已初始化”

### 7.2 Datastore / Query

- `TC-DATA-001`
  - 场景：缺少 `SQLALCHEMY_DATABASE_URI`
  - 类型：U
  - 优先级：P0
  - 状态：现有
  - 关键断言：抛 `RuntimeError`

- `TC-DATA-002`
  - 场景：扩展 key 与 Flask-SQLAlchemy 区分
  - 类型：U
  - 优先级：P0
  - 状态：现有
  - 关键断言：使用 `flask_exts_sqla`

- `TC-DATA-003`
  - 场景：内存 SQLite 共享连接
  - 类型：U
  - 优先级：P0
  - 状态：现有
  - 关键断言：`StaticPool` + `check_same_thread=False`

- `TC-DATA-004`
  - 场景：未 dispose 重复绑定
  - 类型：U
  - 优先级：P0
  - 状态：现有
  - 关键断言：抛 `RuntimeError`

- `TC-DATA-005`
  - 场景：dispose 后可重绑定
  - 类型：U
  - 优先级：P0
  - 状态：现有
  - 关键断言：新 app 可用

- `TC-DATA-006`
  - 场景：无 app context dispose
  - 类型：U
  - 优先级：P1
  - 状态：现有
  - 关键断言：不抛异常

- `TC-DATA-007`
  - 场景：scoped session 按 app context
  - 类型：U
  - 优先级：P0
  - 状态：现有
  - 关键断言：同 context 同 session

- `TC-DATA-008`
  - 场景：`reset_all` 删表重建
  - 类型：U
  - 优先级：P1
  - 状态：现有
  - 关键断言：表存在且为空

- `TC-DATA-009`
  - 场景：JOIN 路径复用
  - 类型：U
  - 优先级：P0
  - 状态：现有
  - 关键断言：相同路径返回同一 alias

- `TC-DATA-010`
  - 场景：前缀路径复用
  - 类型：U
  - 优先级：P1
  - 状态：现有
  - 关键断言：扩展路径复用前缀

- `TC-DATA-011`
  - 场景：不同关系生成不同 alias
  - 类型：U
  - 优先级：P0
  - 状态：现有
  - 关键断言：多路径不串

- `TC-DATA-012`
  - 场景：搜索 `^`/`$`/`=` 语义
  - 类型：U
  - 优先级：P1
  - 状态：待补
  - 关键断言：前缀/后缀/精确

- `TC-DATA-013`
  - 场景：过滤操作符
  - 类型：U
  - 优先级：P1
  - 状态：待补
  - 关键断言：`==`/`!=`/`>`/`<`/`like`/`in`/`between`/`is_null`

- `TC-DATA-014`
  - 场景：一对多 JOIN 计数
  - 类型：U
  - 优先级：P0
  - 状态：待补
  - 关键断言：`count` 等于根记录数，不重复

- `TC-DATA-015`
  - 场景：eager load 配置
  - 类型：U
  - 优先级：P2
  - 状态：现有（弱）
  - 关键断言：`joinedload`/`selectinload` 生效

- `TC-DATA-016`
  - 场景：复合主键删除
  - 类型：I
  - 优先级：P1
  - 状态：现有
  - 关键断言：正确删除

- `TC-DATA-017`
  - 场景：无效关系路径
  - 类型：U
  - 优先级：P1
  - 状态：待补
  - 关键断言：抛 `ValueError`/`AttributeError`

- `TC-DATA-018`
  - 场景：类型推断
  - 类型：U
  - 优先级：P1
  - 状态：现有
  - 关键断言：常见列类型正确

### 7.3 Admin

> View/ModelView/SqlaModelView 的实现与配置见 [`spec.md` 第 10 章](./spec.md#10-view-与-admin-专题)。本节只定义 Admin 测试用例；CR-001/CR-002/CR-005/CR-006 的问题说明见 `spec.md` 第 10.16 节，CR-001/CR-002/CR-006 的相关用例为 TC-ADMIN-021/TC-ADMIN-031/TC-ADMIN-032，状态以用例表为准。

- `TC-ADMIN-001`
  - 场景：列表列渲染
  - 类型：I
  - 优先级：P0
  - 状态：现有
  - 关键断言：列名/值正确

- `TC-ADMIN-002`
  - 场景：默认分页
  - 类型：I
  - 优先级：P0
  - 状态：现有
  - 关键断言：页大小、页数、记录数

- `TC-ADMIN-003`
  - 场景：可配置页大小白名单
  - 类型：I
  - 优先级：P0
  - 状态：现有
  - 关键断言：非白名单回退默认

- `TC-ADMIN-004`
  - 场景：无分页（page_size=0）
  - 类型：I
  - 优先级：P1
  - 状态：现有
  - 关键断言：返回全部

- `TC-ADMIN-005`
  - 场景：排序（升/降/关联）
  - 类型：I
  - 优先级：P0
  - 状态：现有
  - 关键断言：顺序正确

- `TC-ADMIN-006`
  - 场景：默认排序
  - 类型：I
  - 优先级：P1
  - 状态：现有
  - 关键断言：无参数时按默认

- `TC-ADMIN-007`
  - 场景：搜索（普通/关联/无关联行）
  - 类型：I
  - 优先级：P0
  - 状态：现有
  - 关键断言：命中/不命中

- `TC-ADMIN-008`
  - 场景：搜索保留额外参数
  - 类型：I
  - 优先级：P1
  - 状态：现有
  - 关键断言：隐藏字段保留

- `TC-ADMIN-009`
  - 场景：筛选操作符
  - 类型：I
  - 优先级：P0
  - 状态：现有
  - 关键断言：7 种文本操作、数值/日期/布尔

- `TC-ADMIN-010`
  - 场景：关联列筛选
  - 类型：I
  - 优先级：P1
  - 状态：现有
  - 关键断言：关联表过滤正确

- `TC-ADMIN-011`
  - 场景：CRUD
  - 类型：I
  - 优先级：P0
  - 状态：现有
  - 关键断言：创建/编辑/删除 + DB 状态

- `TC-ADMIN-012`
  - 场景：详情页
  - 类型：I
  - 优先级：P1
  - 状态：现有
  - 关键断言：字段值正确

- `TC-ADMIN-013`
  - 场景：CSV 导出
  - 类型：I
  - 优先级：P1
  - 状态：现有
  - 关键断言：内容/表头

- `TC-ADMIN-014`
  - 场景：导出最大行数
  - 类型：I
  - 优先级：P2
  - 状态：待补
  - 关键断言：超限行为

- `TC-ADMIN-015`
  - 场景：其他导出类型
  - 类型：I
  - 优先级：P2
  - 状态：待补
  - 关键断言：tablib 支持类型

- `TC-ADMIN-016`
  - 场景：行内编辑
  - 类型：I
  - 优先级：P1
  - 状态：现有
  - 关键断言：列表页保存

- `TC-ADMIN-017`
  - 场景：批量删除
  - 类型：I
  - 优先级：P0
  - 状态：现有
  - 关键断言：选中记录删除

- `TC-ADMIN-018`
  - 场景：Inline 创建/编辑/删除
  - 类型：I
  - 优先级：P0
  - 状态：现有
  - 关键断言：父子记录最终状态

- `TC-ADMIN-019`
  - 场景：Inline 一对多/多对多/一对一
  - 类型：I
  - 优先级：P1
  - 状态：现有
  - 关键断言：关系正确

- `TC-ADMIN-020`
  - 场景：Inline 多外键
  - 类型：I
  - 优先级：P1
  - 状态：现有
  - 关键断言：关系映射正确

- `TC-ADMIN-021`
  - 场景：Inline + AJAX 外键
  - 类型：I
  - 优先级：P0
  - 状态：待补
  - 关键断言：页面 200，能搜索/保存（对应 CR-001）

- `TC-ADMIN-022`
  - 场景：AJAX 外键/多对多
  - 类型：I
  - 优先级：P1
  - 状态：现有
  - 关键断言：返回 JSON 正确

- `TC-ADMIN-023`
  - 场景：复合主键
  - 类型：I
  - 优先级：P1
  - 状态：现有
  - 关键断言：列表/删除正确

- `TC-ADMIN-024`
  - 场景：字符串主键
  - 类型：I
  - 优先级：P1
  - 状态：现有
  - 关键断言：列表/删除正确

- `TC-ADMIN-025`
  - 场景：权限：匿名
  - 类型：I
  - 优先级：P0
  - 状态：待补/部分
  - 关键断言：默认 403；`login_required_functions` 也是 403（不重定向）

- `TC-ADMIN-026`
  - 场景：权限：普通用户
  - 类型：I
  - 优先级：P0
  - 状态：待补/部分
  - 关键断言：403

- `TC-ADMIN-027`
  - 场景：权限：admin
  - 类型：I
  - 优先级：P0
  - 状态：现有
  - 关键断言：200

- `TC-ADMIN-028`
  - 场景：权限：未激活账号
  - 类型：I
  - 优先级：P0
  - 状态：待补
  - 关键断言：拒绝账号功能

- `TC-ADMIN-029`
  - 场景：动态翻译
  - 类型：I
  - 优先级：P1
  - 状态：现有
  - 关键断言：语言切换后文本变化

- `TC-ADMIN-030`
  - 场景：表单额外字段/自定义基类
  - 类型：I
  - 优先级：P1
  - 状态：现有
  - 关键断言：字段存在/渲染

- `TC-ADMIN-031`
  - 场景：一对多搜索计数
  - 类型：I
  - 优先级：P0
  - 状态：现有
  - 关键断言：分页总数与列表实际行数一致（含重复根行）；`test_related_search_count_matches_list_rows`（对应 CR-002）

- `TC-ADMIN-032`
  - 场景：URL 特殊字符
  - 类型：I
  - 优先级：P1
  - 状态：现有
  - 关键断言：搜索词含 `&`/空格/非 ASCII 时 URL 编码正确并可回放；`test_get_list_url_encodes_special_characters`、`test_search_url_encodes_special_characters`

- `TC-ADMIN-033`
  - 场景：列表空结果/越界页
  - 类型：I
  - 优先级：P1
  - 状态：待补
  - 关键断言：200，空列表，页数合理

- `TC-ADMIN-040`
  - 场景：AJAX 更新受 can_edit 约束
  - 类型：I
  - 优先级：P0
  - 状态：现有
  - 关键断言：`can_edit=False` 时 `/ajax/update/` 返回 403 且记录不变；`test_ajax_update_requires_can_edit`（对应 SEC-19）

补充测试缺口（2026-11-07 快照，现状待核实）：

- 自定义 `DataBackend` 缺少单元测试。
- CR-012 涉及的单行操作与批量操作渲染/执行缺少专门测试；`test_actions.py` 的历史记录以行内编辑和批量删除为主。
- 视图编辑开关 `can_edit=False` 的 AJAX 更新边界另见第 7.5 节 SEC-19；不能把普通行内编辑用例当成该边界已覆盖。

### 7.4 Forms

- `TC-FORM-001`
  - 场景：JSON 合法/非法/空
  - 类型：U
  - 优先级：P0
  - 状态：现有
  - 关键断言：解析/错误

- `TC-FORM-002`
  - 场景：日期/时间/日期时间字段
  - 类型：U
  - 优先级：P0
  - 状态：现有
  - 关键断言：解析/格式化

- `TC-FORM-003`
  - 场景：文件字段无输入
  - 类型：U
  - 优先级：P0
  - 状态：现有
  - 关键断言：不报错/None

- `TC-FORM-004`
  - 场景：文件上传/多文件
  - 类型：U
  - 优先级：P0
  - 状态：现有
  - 关键断言：保存/读取

- `TC-FORM-005`
  - 场景：图片上传
  - 类型：U
  - 优先级：P1
  - 状态：现有
  - 关键断言：类型/尺寸

- `TC-FORM-006`
  - 场景：必填文件
  - 类型：U
  - 优先级：P1
  - 状态：现有
  - 关键断言：缺失报错

- `TC-FORM-007`
  - 场景：FieldList / FormField
  - 类型：U
  - 优先级：P1
  - 状态：现有
  - 关键断言：子表单数据

- `TC-FORM-008`
  - 场景：CSRF 开启
  - 类型：U
  - 优先级：P0
  - 状态：现有
  - 关键断言：token 存在/校验通过

- `TC-FORM-009`
  - 场景：CSRF 关闭
  - 类型：U
  - 优先级：P1
  - 状态：现有
  - 关键断言：不生成/不校验

- `TC-FORM-010`
  - 场景：CSRF 缺失/篡改/过期
  - 类型：U
  - 优先级：P0
  - 状态：待补
  - 关键断言：分别报错

- `TC-FORM-011`
  - 场景：CSRF 独立派生密钥
  - 类型：U
  - 优先级：P1
  - 状态：现有
  - 关键断言：不等于主密钥

- `TC-FORM-012`
  - 场景：`wrap_formdata` JSON/files
  - 类型：U
  - 优先级：P1
  - 状态：待补
  - 关键断言：正确合并

- `TC-FORM-013`
  - 场景：Unique 校验器
  - 类型：I
  - 优先级：P1
  - 状态：现有（间接）
  - 关键断言：重复值报错

- `TC-FORM-014`
  - 场景：Recaptcha（mock）
  - 类型：U
  - 优先级：P2
  - 状态：待补
  - 关键断言：成功/失败

- `TC-FORM-015`
  - 场景：InlineModelField
  - 类型：U
  - 优先级：P1
  - 状态：待补
  - 关键断言：子表单渲染/取值

- `TC-FORM-016`
  - 场景：Widget 渲染
  - 类型：U
  - 优先级：P2
  - 状态：待补
  - 关键断言：Bootstrap 类/属性

- `TC-FORM-017`
  - 场景：i18n 标签/错误
  - 类型：I
  - 优先级：P2
  - 状态：部分
  - 关键断言：语言切换

`TC-FORM-010` 另需覆盖 HTTP 请求中缺失、篡改和过期 token 的边界；该层级待补，不能以基础表单测试代替。

### 7.5 Security

> 安全威胁模型、控制措施、配置基线与风险清单见 [`security.md`](./security.md)。本节只定义测试用例；若实现行为与安全预期冲突，先在 `security.md` 登记风险，再补失败测试。

- `TC-SEC-001`
  - 场景：不同 purpose 派生不同 key
  - 类型：U
  - 优先级：P0
  - 状态：现有
  - 关键断言：key 不相等且不等于主密钥

- `TC-SEC-002`
  - 场景：哈希正确/错误
  - 类型：U
  - 优先级：P0
  - 状态：现有
  - 关键断言：verify True/False

- `TC-SEC-003`
  - 场景：AES-GCM 加解密
  - 类型：U
  - 优先级：P0
  - 状态：待补
  - 关键断言：往返一致

- `TC-SEC-004`
  - 场景：密文篡改
  - 类型：U
  - 优先级：P0
  - 状态：待补
  - 关键断言：解密失败

- `TC-SEC-005`
  - 场景：序列化有效
  - 类型：U
  - 优先级：P0
  - 状态：现有
  - 关键断言：数据一致

- `TC-SEC-006`
  - 场景：序列化过期
  - 类型：U
  - 优先级：P0
  - 状态：待补（现有注释）
  - 关键断言：`expired=True`

- `TC-SEC-007`
  - 场景：序列化篡改/错误 salt
  - 类型：U
  - 优先级：P0
  - 状态：待补
  - 关键断言：`invalid=True`

- `TC-SEC-008`
  - 场景：邮箱验证令牌
  - 类型：I
  - 优先级：P0
  - 状态：现有
  - 关键断言：验证成功/重复失败

- `TC-SEC-009`
  - 场景：改邮箱令牌
  - 类型：I
  - 优先级：P0
  - 状态：现有（部分）
  - 关键断言：旧邮箱/密码变化后失效；密码变更后令牌失效待补

- `TC-SEC-010`
  - 场景：重置密码令牌
  - 类型：I
  - 优先级：P0
  - 状态：现有（间接）
  - 关键断言：成功/过期/无效

- `TC-SEC-011`
  - 场景：令牌用户不存在
  - 类型：U
  - 优先级：P1
  - 状态：待补
  - 关键断言：`TokenUserNotFoundError`

- `TC-SEC-012`
  - 场景：授权：admin
  - 类型：U
  - 优先级：P0
  - 状态：现有
  - 关键断言：允许

- `TC-SEC-013`
  - 场景：授权：普通用户/无角色
  - 类型：U
  - 优先级：P0
  - 状态：现有
  - 关键断言：拒绝

- `TC-SEC-014`
  - 场景：`allow_access` 公开视图
  - 类型：U
  - 优先级：P0
  - 状态：现有
  - 关键断言：未列入 `login_required_functions` 的方法允许匿名访问；公开视图跳过 RBAC requirement

- `TC-SEC-016`
  - 场景：TFA 生成/校验
  - 类型：U
  - 优先级：P0
  - 状态：现有（弱）
  - 关键断言：正确码通过，错误码失败

- `TC-SEC-017`
  - 场景：TFA 恢复码
  - 类型：I
  - 优先级：P0
  - 状态：现有
  - 关键断言：只存哈希、一次性使用、明文值被拒绝；禁用/重绑后旧码失效；`test_plaintext_recovery_codes_are_rejected`（对应 SEC-13/SEC-16）

- `TC-SEC-018`
  - 场景：TFA 待验证不能访问
  - 类型：I
  - 优先级：P0
  - 状态：现有
  - 关键断言：重定向/401

- `TC-SEC-019`
  - 场景：密码变更使会话失效
  - 类型：I
  - 优先级：P0
  - 状态：现有
  - 关键断言：旧 session 失效

- `TC-SEC-020`
  - 场景：安全重定向
  - 类型：U
  - 优先级：P0
  - 状态：现有
  - 关键断言：外部/畸形 URL 拒绝

- `TC-SEC-021`
  - 场景：JWT 编解码/过期/畸形
  - 类型：I
  - 优先级：P1
  - 状态：现有
  - 关键断言：正确/异常

- `TC-SEC-022`
  - 场景：授权：inactive admin
  - 类型：U/I
  - 优先级：P0
  - 状态：现有
  - 关键断言：访问 Admin 返回 403；`test_deny_inactive_admin_user`、`test_inactive_admin_is_denied`

- `TC-SEC-023`
  - 场景：RBAC requirement 组合判定
  - 类型：U
  - 优先级：P0
  - 状态：现有
  - 关键断言：`Role` 默认 any、`Permission` 默认 all；`All`/`Any`/`Not` 与 `&`/`|` 组合；`Predicate` 收到 `BuildContext`；空声明与非法类型报错

- `TC-SEC-024`
  - 场景：RBAC 视图声明、loader 与查询 API
  - 类型：U
  - 优先级：P0
  - 状态：现有
  - 关键断言：`permissions[fn]` 优先于 `permission` 与 `roles`；字符串等价 `Role`；loader 优先级与用户 getter 回退；`can`/`has_role`/`has_permission` 查询

- `TC-SEC-025`
  - 场景：RBAC 授权器选择与既有规则兼容
  - 类型：U
  - 优先级：P0
  - 状态：现有
  - 关键断言：默认 `SimpleAuthorizer`、`"rbac"` 选择 RBAC、未知值 `ValueError`；公开视图跳过 requirement；inactive 拒绝；未声明或 `view=None` 回退角色规则；active `admin` 在登录门直接放行

补充场景与测试建议（2026-11-07 快照，现状待核实；风险编号不是测试编号）：

- `AesGcmEncryptor` 除往返和篡改外还需验证错误密钥；序列化过期/篡改可使用可控时间或短 `max_age`。
- `TC-SEC-009` 的历史测试主要覆盖确认成功和密码校验；密码变化后旧改邮箱令牌失效的边界待补。
- SEC-01：构造 `admin` 且 `is_active=False`，断言受保护操作被拒；旧快照预期该测试先失败。
- SEC-02：启用 TFA 的用户使用 Bearer token 访问受保护资源时，验证不能绕过第二因子。
- SEC-03：限流/锁定须先明确由应用或反向代理负责，再设计对应测试；可添加集成测试桩。
- SEC-07：设计密钥轮换及 TOTP 数据迁移测试；快照中迁移实现待补。
- SEC-12：已覆盖——`tests/integration/security/test_security_headers.py` 断言 HTTPS 下 `Set-Cookie` 含 `Secure`/`HttpOnly`/`SameSite=Lax`、HTTP 下仍可用，并覆盖安全响应头、HSTS、`SECURITY_REQUIRE_HTTPS` 校验、`SECURITY_COOKIE_DEFAULTS_ENABLED=False`、字符串 `"None"`、`ProxyFix` 下的 HSTS，以及非法 `SECURITY_HEADERS`/`SECURITY_HSTS` 的启动失败。
- SEC-16：已覆盖——禁用 TFA 与重绑 authenticator 后 `recovery_codes` 被清空，旧码无法使用；重新生成后为全新哈希（`test_tfa`、`test_recovery`）。
- SEC-17：已覆盖——断言 `SmtpSSL` 传给 `SMTP_SSL` 的 context 为 `CERT_REQUIRED` 且 `check_hostname=True`，并验证 TLS 错误包装为 `SmtpError`、消息头字段与返回值（`tests/unit/emailer/test_smtp.py`）。
- SEC-18：模拟 logger，断言 warning 不含令牌和链接（已实现：`test_missing_sender_warning_redacts_payload`）。
- SEC-19（旧别名 `V-01` 已废止）：`can_edit=False` 且配置 `column_editable_list` 时，断言 `ajax_update` 被拒；主记录见 `security.md` 第 11 节。

上述风险场景尚未在此单独分配 TC 编号；不能凭风险编号或已有文件推断测试实现和执行结果。

### 7.6 UserStore

- `TC-USER-001`
  - 场景：创建用户
  - 类型：I
  - 优先级：P0
  - 状态：现有
  - 关键断言：id/username/email

- `TC-USER-002`
  - 场景：重复用户名
  - 类型：I
  - 优先级：P0
  - 状态：现有
  - 关键断言：`UserAlreadyExistsError`

- `TC-USER-003`
  - 场景：重复邮箱
  - 类型：I
  - 优先级：P0
  - 状态：现有
  - 关键断言：`UserAlreadyExistsError`

- `TC-USER-004`
  - 场景：登录成功
  - 类型：I
  - 优先级：P0
  - 状态：现有
  - 关键断言：返回用户

- `TC-USER-005`
  - 场景：登录失败（用户不存在/密码错）
  - 类型：I
  - 优先级：P0
  - 状态：现有
  - 关键断言：`InvalidCredentialsError`

- `TC-USER-006`
  - 场景：dummy hash 抗枚举
  - 类型：I
  - 优先级：P1
  - 状态：待补
  - 关键断言：不存在用户也执行校验

- `TC-USER-007`
  - 场景：按 id/identity/username 查询
  - 类型：I
  - 优先级：P0
  - 状态：现有
  - 关键断言：正确用户

- `TC-USER-008`
  - 场景：`identity_name` 切换
  - 类型：I
  - 优先级：P1
  - 状态：现有
  - 关键断言：按 username 查

- `TC-USER-009`
  - 场景：角色创建/关联
  - 类型：I
  - 优先级：P0
  - 状态：现有
  - 关键断言：角色列表

- `TC-USER-010`
  - 场景：`user_set` 更新
  - 类型：I
  - 优先级：P1
  - 状态：待补
  - 关键断言：属性持久化

- `TC-USER-011`
  - 场景：`save_user`
  - 类型：I
  - 优先级：P1
  - 状态：待补
  - 关键断言：更新持久化

- `TC-USER-012`
  - 场景：`get_users` 过滤
  - 类型：I
  - 优先级：P1
  - 状态：待补
  - 关键断言：按条件筛选（问题编号待核实）

- `TC-USER-013`
  - 场景：`remove_user`
  - 类型：I
  - 优先级：P1
  - 状态：待补
  - 关键断言：删除或明确抛错（问题编号待核实）

- `TC-USER-014`
  - 场景：profile 一对一
  - 类型：I
  - 优先级：P1
  - 状态：待补
  - 关键断言：关联正确

- `TC-USER-015`
  - 场景：密码哈希
  - 类型：I
  - 优先级：P0
  - 状态：现有
  - 关键断言：明文不落库

### 7.7 UserCenter

- `TC-AUTH-001`
  - 场景：注册成功
  - 类型：I/E
  - 优先级：P0
  - 状态：现有
  - 关键断言：用户创建 + 发验证邮件

- `TC-AUTH-002`
  - 场景：重复邮箱/用户名
  - 类型：I
  - 优先级：P0
  - 状态：现有
  - 关键断言：错误提示

- `TC-AUTH-003`
  - 场景：登录成功
  - 类型：I/E
  - 优先级：P0
  - 状态：现有
  - 关键断言：重定向/会话

- `TC-AUTH-004`
  - 场景：登录失败
  - 类型：I
  - 优先级：P0
  - 状态：现有
  - 关键断言：统一错误，不枚举

- `TC-AUTH-005`
  - 场景：禁用账号登录
  - 类型：I
  - 优先级：P0
  - 状态：现有
  - 关键断言：`is_active=False` 正确密码也拒绝；未验证邮箱（`is_active=True`）可登录

- `TC-AUTH-006`
  - 场景：登出
  - 类型：I/E
  - 优先级：P0
  - 状态：现有
  - 关键断言：会话清理

- `TC-AUTH-007`
  - 场景：资料页需登录
  - 类型：I
  - 优先级：P0
  - 状态：现有
  - 关键断言：重定向登录

- `TC-AUTH-008`
  - 场景：邮箱验证
  - 类型：I/E
  - 优先级：P0
  - 状态：现有
  - 关键断言：`email_verified=True`

- `TC-AUTH-009`
  - 场景：重发验证邮件
  - 类型：I
  - 优先级：P1
  - 状态：现有
  - 关键断言：发送一次

- `TC-AUTH-010`
  - 场景：改邮箱需密码
  - 类型：I
  - 优先级：P0
  - 状态：现有
  - 关键断言：密码错拒绝

- `TC-AUTH-011`
  - 场景：改邮箱需确认
  - 类型：I/E
  - 优先级：P0
  - 状态：现有
  - 关键断言：点击链接后生效

- `TC-AUTH-012`
  - 场景：改邮箱重复
  - 类型：I
  - 优先级：P1
  - 状态：现有
  - 关键断言：拒绝

- `TC-AUTH-013`
  - 场景：改密码
  - 类型：I/E
  - 优先级：P0
  - 状态：现有
  - 关键断言：新密码可登录，旧密码失败

- `TC-AUTH-014`
  - 场景：找回密码
  - 类型：I/E
  - 优先级：P0
  - 状态：现有
  - 关键断言：发邮件

- `TC-AUTH-015`
  - 场景：重置密码
  - 类型：I/E
  - 优先级：P0
  - 状态：现有
  - 关键断言：新密码生效

- `TC-AUTH-016`
  - 场景：恢复码
  - 类型：I
  - 优先级：P0
  - 状态：现有
  - 关键断言：登录成功/码失效

- `TC-AUTH-017`
  - 场景：TFA 启用/关闭
  - 类型：I
  - 优先级：P0
  - 状态：现有
  - 关键断言：`tfa_enabled` 变化；关闭时清空 `totp_secret` 与 `recovery_codes`

- `TC-AUTH-018`
  - 场景：TFA 登录完整流程
  - 类型：E
  - 优先级：P0
  - 状态：待补
  - 关键断言：密码→验证码→登录

- `TC-AUTH-019`
  - 场景：TFA 待验证不能绕过
  - 类型：I
  - 优先级：P0
  - 状态：现有
  - 关键断言：受保护页拒绝

- `TC-AUTH-020`
  - 场景：禁用账号旧会话即时失效
  - 类型：I
  - 优先级：P0
  - 状态：现有
  - 关键断言：下一次请求 `user_loader` 返回 None、清除 `_user_id`；受保护页 302；重新启用后仍需登录

- `TC-AUTH-021`
  - 场景：开放重定向
  - 类型：I
  - 优先级：P0
  - 状态：待补
  - 关键断言：`next` 外部 URL 被拒

- `TC-AUTH-022`
  - 场景：重复提交/并发注册
  - 类型：I
  - 优先级：P2
  - 状态：待补
  - 关键断言：唯一约束生效

- `TC-AUTH-029`
  - 场景：禁用账号拒绝登录
  - 类型：I
  - 优先级：P0
  - 状态：现有
  - 关键断言：正确密码但不建立 `_user_id`；提示账号已禁用

- `TC-AUTH-030`
  - 场景：禁用账号不能完成 pending TFA
  - 类型：I
  - 优先级：P1
  - 状态：现有
  - 关键断言：pending 被清理，重定向登录

- `TC-AUTH-031`
  - 场景：连续密码失败触发锁定
  - 类型：I
  - 优先级：P0
  - 状态：现有
  - 关键断言：第 N 次失败后 `failed_login_count`/`locked_until` 写入；锁定期内正确密码也被拒；错误提示含剩余时间

- `TC-AUTH-032`
  - 场景：第二因子失败计入同一锁定
  - 类型：I
  - 优先级：P0
  - 状态：现有
  - 关键断言：TFA 连续错误后账号锁定，pending 被清理，GET 校验页重定向登录

- `TC-AUTH-033`
  - 场景：锁定过期与成功登录清零
  - 类型：U/I
  - 优先级：P0
  - 状态：现有
  - 关键断言：过期后可登录；成功登录、成功重置密码把两列清零；退避按 2 的幂增长并被上限截断

### 7.8 Emailer

- `TC-EMAIL-001`
  - 场景：信号触发发送
  - 类型：U
  - 优先级：P0
  - 状态：现有
  - 关键断言：sender 收到 data

- `TC-EMAIL-002`
  - 场景：缺少 `type`
  - 类型：U
  - 优先级：P1
  - 状态：待补
  - 关键断言：warning，不发送

- `TC-EMAIL-003`
  - 场景：未知 sender
  - 类型：U
  - 优先级：P1
  - 状态：现有
  - 关键断言：warning 不抛；记录 type + 脱敏收件人，不含令牌/链接

- `TC-EMAIL-004`
  - 场景：SMTP 成功（mock）
  - 类型：U
  - 优先级：P1
  - 状态：现有（基础）
  - 关键断言：调用成功

- `TC-EMAIL-005`
  - 场景：SMTP 异常
  - 类型：U
  - 优先级：P1
  - 状态：现有
  - 关键断言：`SMTP_SSL` 抛出证书校验错误时包装为 `SmtpError`，`__cause__` 保留原异常

- `TC-EMAIL-006`
  - 场景：重复注册 sender
  - 类型：U
  - 优先级：P1
  - 状态：待补
  - 关键断言：`ValueError`

- `TC-EMAIL-007`
  - 场景：默认 sender 配置存在/缺失
  - 类型：U
  - 优先级：P1
  - 状态：待补
  - 关键断言：注册/不注册

- `TC-EMAIL-008`
  - 场景：验证邮件/重置邮件内容
  - 类型：I
  - 优先级：P1
  - 状态：待补
  - 关键断言：主题/链接/收件人

- `TC-EMAIL-009`
  - 场景：`email_change` 复用 `verify_email` sender
  - 类型：I
  - 优先级：P0
  - 状态：待补
  - 关键断言：收件人为新邮箱，链接指向 `confirm_email_change`

### 7.9 Frontend

- `TC-FRONTEND-001`
  - 场景：插件自动发现
  - 类型：U
  - 优先级：P0
  - 状态：现有（间接）
  - 关键断言：注册表包含内置插件

- `TC-FRONTEND-002`
  - 场景：重复插件名
  - 类型：U
  - 优先级：P0
  - 状态：现有
  - 关键断言：`ValueError`

- `TC-FRONTEND-003`
  - 场景：默认插件顺序
  - 类型：U
  - 优先级：P0
  - 状态：现有
  - 关键断言：输入顺序保留

- `TC-FRONTEND-004`
  - 场景：请求插件依赖排序
  - 类型：U
  - 优先级：P0
  - 状态：现有
  - 关键断言：依赖在前

- `TC-FRONTEND-005`
  - 场景：循环依赖
  - 类型：U
  - 优先级：P0
  - 状态：现有
  - 关键断言：`PluginCycleError`

- `TC-FRONTEND-006`
  - 场景：未知插件
  - 类型：U
  - 优先级：P1
  - 状态：待补
  - 关键断言：`ValueError`

- `TC-FRONTEND-007`
  - 场景：样式/脚本拼接顺序
  - 类型：U
  - 优先级：P1
  - 状态：现有
  - 关键断言：依赖顺序 + `Markup`

- `TC-FRONTEND-008`
  - 场景：Jinja 全局变量
  - 类型：I
  - 优先级：P0
  - 状态：现有
  - 关键断言：`_template`/`csrf_token`

- `TC-FRONTEND-009`
  - 场景：模板集成
  - 类型：I
  - 优先级：P1
  - 状态：待补
  - 关键断言：页面包含插件资源

- `TC-FRONTEND-010`
  - 场景：vendor 资源存在
  - 类型：U
  - 优先级：P2
  - 状态：待补
  - 关键断言：关键文件存在

### 7.10 Commands

- `TC-CLI-001`
  - 场景：`datastore create_all`
  - 类型：I
  - 优先级：P1
  - 状态：待补
  - 关键断言：表创建

- `TC-CLI-002`
  - 场景：`datastore drop_all`
  - 类型：I
  - 优先级：P1
  - 状态：待补
  - 关键断言：表删除

- `TC-CLI-003`
  - 场景：`security create_user`
  - 类型：I
  - 优先级：P1
  - 状态：待补
  - 关键断言：用户创建

- `TC-CLI-004`
  - 场景：重复用户
  - 类型：I
  - 优先级：P1
  - 状态：待补
  - 关键断言：错误提示

- `TC-CLI-005`
  - 场景：`--active` / `--email`
  - 类型：I
  - 优先级：P1
  - 状态：待补
  - 关键断言：属性正确

- `TC-CLI-006`
  - 场景：命令注册/帮助
  - 类型：I
  - 优先级：P2
  - 状态：待补
  - 关键断言：命令可见

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

- `TC-DATA-019`
  - 场景：正常提交后数据持久化
  - 类型：I
  - 优先级：P0
  - 状态：待补
  - 关键断言：重新查询可见

- `TC-DATA-020`
  - 场景：视图异常时回滚
  - 类型：I
  - 优先级：P0
  - 状态：待补
  - 关键断言：无部分写入

- `TC-DATA-021`
  - 场景：`IntegrityError` 后 session 可复用
  - 类型：I
  - 优先级：P0
  - 状态：待补
  - 关键断言：`rollback()` 后可继续查询/写入

- `TC-DATA-022`
  - 场景：级联删除（`cascade="all, delete-orphan"`）
  - 类型：I
  - 优先级：P1
  - 状态：待补
  - 关键断言：子记录一并删除

- `TC-DATA-023`
  - 场景：受限删除（无级联）
  - 类型：I
  - 优先级：P1
  - 状态：待补
  - 关键断言：抛 `IntegrityError` 或按设计拒绝

- `TC-DATA-024`
  - 场景：外键完整性
  - 类型：I
  - 优先级：P0
  - 状态：待补
  - 关键断言：非法外键被拒绝（SQLite 需 `PRAGMA foreign_keys=ON`）

- `TC-DATA-025`
  - 场景：唯一约束
  - 类型：I
  - 优先级：P0
  - 状态：待补
  - 关键断言：重复用户名/邮箱被拒绝

- `TC-DATA-026`
  - 场景：并发更新/丢失更新
  - 类型：I
  - 优先级：P2
  - 状态：待补
  - 关键断言：记录当前行为，不假设乐观锁

- `TC-DATA-027`
  - 场景：一对多增删后计数一致
  - 类型：I
  - 优先级：P0
  - 状态：待补
  - 关键断言：`count` 与根记录数一致（对应 CR-002）

> SQLite 默认不启用外键约束。测试 TC-DATA-024 前必须显式执行 `PRAGMA foreign_keys=ON`，否则会“假通过”。

### 7.12 错误处理与信号契约

- `TC-ERROR-001`
  - 场景：未知路由 404
  - 类型：I
  - 优先级：P1
  - 状态：待补
  - 关键断言：状态码 404，模板可渲染

- `TC-ERROR-002`
  - 场景：无权限 403
  - 类型：I
  - 优先级：P0
  - 状态：待补
  - 关键断言：普通用户访问 admin 被拒

- `TC-ERROR-003`
  - 场景：方法不允许 405
  - 类型：I
  - 优先级：P2
  - 状态：待补
  - 关键断言：状态码 405

- `TC-ERROR-004`
  - 场景：未捕获异常
  - 类型：I
  - 优先级：P2
  - 状态：待补
  - 关键断言：`TESTING=True` 下异常上抛；生产配置下 500 页

- `TC-ERROR-005`
  - 场景：无效/过期令牌页
  - 类型：I
  - 优先级：P0
  - 状态：待补
  - 关键断言：友好错误，不泄露用户信息

- `TC-ERROR-006`
  - 场景：畸形表单数据
  - 类型：I
  - 优先级：P1
  - 状态：待补
  - 关键断言：400/表单错误，不 500

- `TC-ERROR-007`
  - 场景：未知导出类型
  - 类型：I
  - 优先级：P2
  - 状态：待补
  - 关键断言：明确错误，不崩溃

- `TC-ERROR-008`
  - 场景：CSRF 校验失败
  - 类型：I
  - 优先级：P0
  - 状态：待补
  - 关键断言：拒绝提交，提示可理解

信号契约：

- `TC-SIGNAL-001`
  - 场景：`user_registered` 载荷
  - 类型：U
  - 优先级：P0
  - 状态：待补
  - 关键断言：`user` 为刚创建用户

- `TC-SIGNAL-002`
  - 场景：`verify_email` 邮件字段
  - 类型：U
  - 优先级：P0
  - 状态：待补
  - 关键断言：`type=verify_email`、`email`、`verification_token`、`verification_link`

- `TC-SIGNAL-003`
  - 场景：`reset_password` 邮件字段
  - 类型：U
  - 优先级：P0
  - 状态：待补
  - 关键断言：`type=reset_password`、`email`、`reset_password_token`、`reset_password_link`

- `TC-SIGNAL-004`
  - 场景：`email_change` 邮件字段
  - 类型：U
  - 优先级：P0
  - 状态：待补
  - 关键断言：`type=verify_email`、`email`（新邮箱）、`verification_token`、`verification_link`

- `TC-SIGNAL-005`
  - 场景：未注册 sender
  - 类型：U
  - 优先级：P1
  - 状态：待补
  - 关键断言：warning，不抛异常

- `TC-SIGNAL-006`
  - 场景：sender 抛 `SmtpError`
  - 类型：U
  - 优先级：P1
  - 状态：待补
  - 关键断言：被捕获，返回提示

> `email_change` 复用 `type=verify_email`，但收件人是新邮箱；断言时结合 `email` 或 token 键区分，不能只按 `type` 判断。

### 7.13 i18n、时区与复数

- `TC-I18N-001`
  - 场景：默认语言
  - 类型：I
  - 优先级：P1
  - 状态：待补
  - 关键断言：按 `BABEL_DEFAULT_LOCALE` 渲染

- `TC-I18N-002`
  - 场景：`?lang=zh` 切换
  - 类型：I
  - 优先级：P1
  - 状态：待补
  - 关键断言：文本变为中文，cookie/session 生效

- `TC-I18N-003`
  - 场景：不支持语言回退
  - 类型：I
  - 优先级：P1
  - 状态：待补
  - 关键断言：回退默认语言，不报错

- `TC-I18N-004`
  - 场景：时区渲染
  - 类型：I
  - 优先级：P2
  - 状态：待补
  - 关键断言：按 `BABEL_DEFAULT_TIMEZONE` 输出

- `TC-I18N-005`
  - 场景：复数形式
  - 类型：U
  - 优先级：P2
  - 状态：待补
  - 关键断言：单复数选择正确

- `TC-I18N-006`
  - 场景：缺失翻译回退
  - 类型：U
  - 优先级：P2
  - 状态：待补
  - 关键断言：回退 msgid，不抛异常

## 8. 端到端测试方案

> **状态声明**：本章为目标设计/规划草案。当前仓库不存在 `tests/e2e/` 目录或端到端测试用例；本章用例在落地并接入运行前仅作为测试设计参考。

### 8.1 两种 E2E

- **HTTP 级 E2E**
  - 工具：Flask `test_client`
  - 优点：快、稳定、无浏览器依赖
  - 缺点：不验证 JS/CSS
  - 建议：**默认采用**

- **浏览器 E2E**
  - 工具：Selenium/Playwright
  - 优点：验证真实 UI/JS
  - 缺点：慢、脆弱、需环境
  - 建议：可选、夜间运行

Selenium/Playwright 属于第二种。建议先用 HTTP 级 E2E 覆盖业务旅程，再对少数 JS 交互补浏览器测试。

### 8.2 HTTP E2E 流程清单

- `TC-AUTH-023`
  - 流程：注册 → 验证 → 登录
  - 步骤：注册 → 捕获邮件 → 访问验证链接 → 登录
  - 关键断言：用户激活、登录成功、资料页可访问

- `TC-AUTH-024`
  - 流程：登录 → TFA → 访问
  - 步骤：登录（密码）→ 跳转 TFA → 输入 TOTP → 访问受保护页
  - 关键断言：TFA 前拒绝、TFA 后 200

- `TC-AUTH-025`
  - 流程：找回 → 重置 → 登录
  - 步骤：提交邮箱 → 捕获链接 → 设置新密码 → 登录
  - 关键断言：新密码成功、旧密码失败

- `TC-AUTH-026`
  - 流程：改邮箱
  - 步骤：登录 → 改邮箱 → 捕获确认链接 → 访问 → 用新邮箱登录
  - 关键断言：旧邮箱失效、新邮箱生效

- `TC-AUTH-027`
  - 流程：恢复码登录
  - 步骤：启用 TFA → 登出 → 用恢复码登录
  - 关键断言：成功、恢复码失效

- `TC-ADMIN-034`
  - 流程：Admin CRUD
  - 步骤：登录 admin → 创建 → 编辑 → 删除
  - 关键断言：列表/DB 状态

- `TC-ADMIN-035`
  - 流程：搜索/筛选/排序/分页
  - 步骤：造数据 → 访问带参数 URL
  - 关键断言：结果正确、计数正确

- `TC-ADMIN-036`
  - 流程：Inline
  - 步骤：创建父+子 → 编辑 → 删除子
  - 关键断言：父子状态

- `TC-ADMIN-037`
  - 流程：导出
  - 步骤：访问导出 URL
  - 关键断言：CSV 内容/表头

- `TC-ADMIN-038`
  - 流程：权限
  - 步骤：匿名/普通/admin/未激活
  - 关键断言：重定向/403/200

- `TC-ADMIN-039`
  - 流程：Inline + AJAX 外键
  - 步骤：配置子模型 `ajax_refs` → 打开创建页 → 搜索 → 保存
  - 关键断言：页面 200、JSON 正确、父子落库（对应 CR-001）

- `TC-AUTH-028`
  - 流程：令牌重复/过期
  - 步骤：使用已验证/已过期链接再次访问
  - 关键断言：友好提示，不重复生效

- `TC-ERROR-009`
  - 流程：错误页
  - 步骤：访问不存在路由、无权限路由
  - 关键断言：404/403 页面可渲染

- `TC-I18N-007`
  - 流程：语言切换
  - 步骤：带 `?lang=zh` 访问
  - 关键断言：文本语言变化

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

- `pytest-benchmark`
  - 用途：查询/渲染耗时基准
  - 是否已有依赖：否，需新增（需询问）

- **SQLAlchemy `event`**
  - 用途：统计查询次数，检测 N+1
  - 是否已有依赖：是（SQLAlchemy 自带）

- `tracemalloc`
  - 用途：内存快照
  - 是否已有依赖：是（标准库）

- `cProfile` / `py-spy`
  - 用途：性能剖析
  - 是否已有依赖：可选

如果不引入 `pytest-benchmark`，也可以先用 `time.perf_counter()` + `pytest.mark.performance` 做简单阈值断言。但基准工具更适合统计波动。

### 9.3 基准指标

结合本项目实际确定基准指标：

- **Admin 列表查询**
  - 数据量：1,000
  - 目标：< 500ms
  - 说明：不含模板渲染

- **Admin 搜索**
  - 数据量：10,000
  - 目标：< 1000ms
  - 说明：单列/关联列分别测

- **Admin 筛选**
  - 数据量：10,000
  - 目标：< 1000ms
  - 说明：常用操作符

- **表单渲染**
  - 数据量：50 字段
  - 目标：< 100ms
  - 说明：不含 DB

- **列表模板渲染**
  - 数据量：100 行
  - 目标：< 500ms
  - 说明：含 Jinja

- **登录（含哈希）**
  - 数据量：1 用户
  - 目标：< 200ms
  - 说明：含密码校验

- **批量删除**
  - 数据量：1,000
  - 目标：< 5s
  - 说明：含提交

- **注册+发信**
  - 数据量：1 用户
  - 目标：< 300ms
  - 说明：邮件 mock

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

- **2026-11-07 · Admin 列表**
  - commit：未记录
  - 机器/CI：local
  - 场景：Admin 列表
  - 数据量：1,000
  - p50：—
  - p95：—
  - 查询数：—
  - 备注：初始基线待测

- **2026-11-07 · Admin 搜索**
  - commit：未记录
  - 机器/CI：local
  - 场景：Admin 搜索
  - 数据量：10,000
  - p50：—
  - p95：—
  - 查询数：—
  - 备注：单列/关联列分开

- **2026-11-07 · 列表渲染**
  - commit：未记录
  - 机器/CI：local
  - 场景：列表渲染
  - 数据量：100 行
  - p50：—
  - p95：—
  - 查询数：—
  - 备注：含 Jinja

- **2026-11-07 · 登录**
  - commit：未记录
  - 机器/CI：local
  - 场景：登录
  - 数据量：1 用户
  - p50：—
  - p95：—
  - 查询数：—
  - 备注：含哈希

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

或在 `pyproject.toml` 中配置（当前仓库已启用）：

```toml
[tool.coverage.run]
source = ["src/flask_exts"]

[tool.coverage.report]
show_missing = true
```

分支覆盖与 `omit` 目前未启用；需要时再补 `branch = true` 和静态资源/示例排除。

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

> **口径说明**：2026-11-12 之前的记录未限制 `source`，`coverage run -m pytest` 同时统计了 `tests/` 与库代码，且未计入未被导入的源码文件，因此与当前“仅 `src/flask_exts`”的口径不可直接比较。以下旧行保留作历史记录，自 2026-11-12 口径修正行起使用新口径。

- **2026-11-10 · 171b409**
  - commit：`171b40968f309c04ae3ad423696227c2767b0055`
  - 行覆盖：90%
  - 分支覆盖：待测（未启 branch）
  - 函数覆盖：待测
  - 命令：`coverage run -m pytest -q`
  - 备注：首次实测基线（229 passed, 1 skipped；全套 31.81s）

- **2026-11-11 · 171b409**
  - commit：`171b40968f309c04ae3ad423696227c2767b0055`（工作树含未提交改动）
  - 行覆盖：90%
  - 分支覆盖：待测（未启 branch）
  - 函数覆盖：待测
  - 命令：`coverage run -m pytest -q`
  - 备注：当前工作树复测（233 passed, 1 skipped；全套 32.79s；8601 statements, 866 missed）

- **2026-11-11 · 171b409**
  - commit：`171b40968f309c04ae3ad423696227c2767b0055`（工作树含未提交改动）
  - 行覆盖：90%
  - 分支覆盖：待测（未启 branch）
  - 函数覆盖：待测
  - 命令：`coverage run -m pytest -q`
  - 备注：修复 `ChoiceField` 后复测（245 passed, 1 skipped；全套 32.49s；8685 statements, 862 missed）

- **2026-11-11 · 0300602**
  - commit：`03006024d21167c0f6285a5724a3be5ef24d9a59`（v0.4.1）
  - 行覆盖：90%
  - 分支覆盖：待测（未启 branch）
  - 函数覆盖：待测
  - 命令：`coverage run -m pytest -q`
  - 备注：发布提交复测（245 passed, 1 skipped；全套 31.25s；8685 statements, 862 missed）

- **2026-11-12 · 0300602**
  - commit：`03006024d21167c0f6285a5724a3be5ef24d9a59` + 注册邮箱校验、CR-005/CR-006 修复
  - 行覆盖：90%
  - 分支覆盖：待测（未启 branch）
  - 函数覆盖：待测
  - 命令：`coverage run -m pytest -q`
  - 备注：251 passed, 1 skipped；全套 32.86s；8750 statements, 861 missed

- **2026-11-12 · 0300602**
  - commit：`03006024d21167c0f6285a5724a3be5ef24d9a59` + 上述改动与 EXT-004
  - 行覆盖：90%
  - 分支覆盖：待测（未启 branch）
  - 函数覆盖：待测
  - 命令：`coverage run -m pytest -q`
  - 备注：257 passed, 1 skipped；全套 32.31s；8815 statements, 858 missed

- **2026-11-12 · 0300602**
  - commit：`03006024d21167c0f6285a5724a3be5ef24d9a59` + 上述改动与 AUTH-009
  - 行覆盖：90%
  - 分支覆盖：待测（未启 branch）
  - 函数覆盖：待测
  - 命令：`coverage run -m pytest -q`
  - 备注：259 passed, 1 skipped；全套 34.25s；8837 statements, 855 missed

- **2026-11-12 · 0300602**
  - commit：`03006024d21167c0f6285a5724a3be5ef24d9a59` + 上述改动与 AUTH-010
  - 行覆盖：90%
  - 分支覆盖：待测（未启 branch）
  - 函数覆盖：待测
  - 命令：`coverage run -m pytest -q`
  - 备注：261 passed, 1 skipped；全套 34.32s；8865 statements, 857 missed

- **2026-11-12 · 0300602**
  - commit：`03006024d21167c0f6285a5724a3be5ef24d9a59` + 上述改动与 `requires_active` 移除
  - 行覆盖：90%
  - 分支覆盖：待测（未启 branch）
  - 函数覆盖：待测
  - 命令：`coverage run -m pytest -q`
  - 备注：259 passed, 1 skipped；全套 33.09s；8833 statements, 855 missed

- **2026-11-12 · 0300602**
  - commit：`03006024d21167c0f6285a5724a3be5ef24d9a59` + 上述改动与覆盖率口径修正
  - 行覆盖：83%
  - 分支覆盖：待测（未启 branch）
  - 函数覆盖：待测
  - 命令：`coverage run -m pytest -q`（`source = ["src/flask_exts"]`）
  - 备注：259 passed, 1 skipped；全套 36.72s；5276 statements, 905 missed

- **2026-11-13 · 445b03d**
  - commit：`445b03d1fe6c59cd53405c8187de968c687a2909`
  - 行覆盖：84%
  - 分支覆盖：待测（未启 branch）
  - 函数覆盖：待测
  - 命令：`coverage run -m pytest -q`（`source = ["src/flask_exts"]`）
  - 备注：274 passed；全套 49.16s；5361 statements, 884 missed

- **2026-11-13 · 445b03d**
  - commit：`445b03d1fe6c59cd53405c8187de968c687a2909`（同提交复跑）
  - 行覆盖：未采集
  - 分支覆盖：待测
  - 函数覆盖：待测
  - 命令：`uv run pytest -q -p no:cacheprovider`
  - 备注：274 passed、0 跳过；10.02s；Python 3.13.5；逐条判定契约 `verification` 所用证据

- **2026-11-14 · 445b03d + 工作树**
  - commit：`445b03d1fe6c59cd53405c8187de968c687a2909` 加未提交工作树差异（JWT `pwd`/`amr` 校验）
  - 行覆盖：未采集
  - 分支覆盖：待测
  - 函数覆盖：待测
  - 命令：`.venv/bin/python -m pytest -q`
  - 备注：277 passed、0 跳过；10.19s；Python 3.13.5；`REQ-AUTH-012` 单独批准所用证据

- **2026-11-14 · 445b03d + 工作树（JWT 硬化）**
  - commit：`445b03d1fe6c59cd53405c8187de968c687a2909` 加未提交工作树差异（算法白名单、密钥校验、`iat`/`JWT_LEEWAY`、Bearer 大小写、`id`/`amr` 严格解析）
  - 行覆盖：未采集
  - 分支覆盖：待测
  - 函数覆盖：待测
  - 命令：`.venv/bin/python -m pytest -q`
  - 备注：301 passed、0 跳过；11.18s；Python 3.13.5；新增 24 个 JWT 回归用例；`ruff check` 通过

- **2026-11-14 · 445b03d + 工作树（SEC-12）**
  - commit：`445b03d1fe6c59cd53405c8187de968c687a2909` 加未提交工作树差异（安全 Cookie 默认值、安全响应头、`SECURITY_REQUIRE_HTTPS` 校验）
  - 行覆盖：未采集
  - 分支覆盖：待测
  - 函数覆盖：待测
  - 命令：`.venv/bin/python -m pytest -q`
  - 备注：311 passed、0 跳过；11.18s；Python 3.13.5；新增 10 个 SEC-12 回归用例

- **2026-11-15 · 445b03d + 工作树（SEC-12 补充）**
  - commit：`445b03d1fe6c59cd53405c8187de968c687a2909` 加未提交工作树差异（`SECURITY_COOKIE_DEFAULTS_ENABLED`、显式 `SameSite=None`、`ProxyFix` 场景、启动阶段类型校验）
  - 行覆盖：未采集
  - 分支覆盖：待测
  - 函数覆盖：待测
  - 命令：`.venv/bin/python -m pytest -q`
  - 备注：319 passed、0 跳过；11.31s；Python 3.13.5；`ruff check` 通过；SEC-12 用例增至 18 个

- **2026-11-16 · 1349295（代码审查修复）**
  - commit：`134929564791b2d5bc843685650ee8ccd13d1bc6`（`FileSize` 不读取整份文件、负 `page`/`offset` 夹取、页码链接修复、默认视图选择、布尔格式化转义、JWT 强制 `iat`、CSRF token 改用 `secrets`、TOTP flush 加服务层提交、未知 serializer 30 分钟默认值、用户时间戳 aware UTC）
  - 行覆盖：未采集
  - 分支覆盖：待测
  - 函数覆盖：待测
  - 命令：`.venv/bin/python -m pytest -q`
  - 备注：330 passed、0 跳过；31.79s；Python 3.13.5；`ruff check` 与 `ruff format --check` 通过

- **2026-11-17 · 1349295 + 工作树（login_required_functions）**
  - commit：`134929564791b2d5bc843685650ee8ccd13d1bc6` 加未提交工作树差异（`View.login_required_functions` 取代 `flask_exts.admin.login_required`；匿名访问受限方法返回 403；非法方法名在视图构造时失败；Simple/RBAC 授权器一致性；删除 `usercenter/auth_requires.py`）
  - 行覆盖：未采集
  - 分支覆盖：待测
  - 函数覆盖：待测
  - 命令：`.venv/bin/python -m pytest -q`
  - 备注：338 passed、0 跳过；31.45s；Python 3.13.5；`ruff check` 与 `ruff format --check` 通过

- **2026-11-18 · 1349295 + 工作树（共用登录门与 RBAC）**
  - commit：`134929564791b2d5bc843685650ee8ccd13d1bc6` 加未提交工作树差异（登录门抽到 `Authorizer.check_view_access()`，`SimpleAuthorizer` 与 `RBACAuthorizer` 共用；补齐 RBAC 公开视图、非公开视图与 requirement 用例；测试拆分为基类、Simple 与 RBAC 三个文件）
  - 行覆盖：未采集
  - 分支覆盖：待测
  - 函数覆盖：待测
  - 命令：`.venv/bin/python -m pytest -q`
  - 备注：389 passed、0 跳过；31.39s；Python 3.13.5；`ruff check` 与 `ruff format --check` 通过

- **2026-11-18 · 1349295 + 工作树（admin 登录门超级权限）**
  - commit：`134929564791b2d5bc843685650ee8ccd13d1bc6` 加未提交工作树差异（`Authorizer.check_view_access()` 对已登录且 active 的 `admin` 直接放行）
  - 行覆盖：未采集
  - 分支覆盖：待测
  - 函数覆盖：待测
  - 命令：`.venv/bin/python -m pytest -q`
  - 备注：394 passed、0 跳过；30.51s；Python 3.13.5；`ruff check` 与 `ruff format --check` 通过

- **2026-11-18 · ca9f325（0.5.0）**
  - commit：`ca9f325fa2d43f53eaf14ca71a77ee75b1471406`（`chore(release): v0.5.0`）
  - 行覆盖：未采集
  - 分支覆盖：待测
  - 函数覆盖：待测
  - 命令：`.venv/bin/python -m pytest -q`
  - 备注：393 passed、0 跳过；31.92s；Python 3.13.5；`ruff check`、`ruff format --check` 与 Sphinx `-W -n` 通过；与上一条 394 的差异未复现，以本轮 393 为准

规则：

- 基线必须与 commit 绑定；代码变化后重新测量。
- 目标改为“基线 + 新增代码 ≥ 80%”，避免整体数字掩盖新代码缺口。
- 覆盖率下降超过 1% 时，CI 给出 warning；下降超过 3% 时阻塞合并（阈值可按团队调整；当前尚未实现）。

### 10.6 排除项与理由

- `*/static/vendor/*`：第三方生成资源，不手改
- `*/examples/*`：示例应用，不是库代码
- `*/tests/*`：测试自身
- `*/migrations/*`：若未来引入，单独统计
- `__main__` / CLI 入口：薄封装，由 CLI 用例覆盖

不要为了让数字好看而排除业务模块；任何新增排除项都必须在本节登记。

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

- `tests`
  - 触发：push / PR / 手动
  - 内容：Python 3.11、3.12、3.13 矩阵；`uv sync --locked` 后运行 `uv run pytest -q`。3.11 验证最低支持，3.13 验证主力版本

- `coverage`
  - 触发：push / PR / 手动
  - 内容：Python 3.13；`uv run coverage run -m pytest -q` + `coverage report -m`；覆盖率输出到 CI 日志，不上传 artifact；未设置 `fail-under` 门槛

- `lint`
  - 触发：仅 PR
  - 内容：仅对变更文件运行 `ruff check`、`ruff format --check` 与 `djlint --check`，规避仓库历史格式问题

说明：

- Sphinx 依赖由 `pyproject.toml` 的 `docs` 依赖组维护（已包含在 `dev` 组中），`uv sync` 会一并安装，无需单独安装 `docs/requirements.txt`。
- `uv sync --locked` 要求 `uv.lock` 已提交且与 `pyproject.toml` 一致，否则 job 直接失败。
- 主力 Python 版本锚定 Debian stable（当前 3.13），最低支持保持 3.11；决策见 [`architecture.md` ADR-005](./architecture.md#adr-005-开发与主力验证-python-版本锚定-debian-stable)。
- 仓库存在历史 Ruff/模板格式问题，`ruff`/`djlint` 在 CI 中只检查**本次变更文件**，不要全量检查。
- 夜间任务可单独加 `browser` 与 `performance` job，允许失败但不阻塞主分支；当前尚未落地。
- 治理文档与 Demo 冒烟门禁（P0-3 / P0-4 目标）：后续在 CI 扩展时，推荐新增独立 job 执行 `FLASK_EXTS_REPO=. python check_docs.py`（核验契约引用、三维状态与缺陷编号规范）以及 Demo 基础路由导入与初始化冒烟，防止文档与示例在代码迭代中静默漂移。

### 11.4 产物

- 覆盖率报告：`coverage report -m` 输出到 CI 日志，不上传 artifact。
- 目标产物：`htmlcov/`、`benchmark.json`（pytest-benchmark）、浏览器失败截图/HTML、Sphinx 构建日志

### 11.5 本地与 CI 一致性

- **Lint**
  - 本地命令：`uv run python -m ruff check .`（全量；CI 只查变更文件）
  - CI 阶段：`lint` job（仅 PR）

- **模板**
  - 本地命令：`uv run python -m djlint <changed> --check`
  - CI 阶段：`lint` job（仅 PR，变更模板）

- **Unit**
  - 本地命令：`uv run python -m pytest -q tests/unit`
  - CI 阶段：`tests` job

- **Integration**
  - 本地命令：`uv run python -m pytest -q tests/integration`
  - CI 阶段：`tests` job

- **覆盖率**
  - 本地命令：`uv run coverage run -m pytest -q`
  - CI 阶段：`coverage` job（无门槛）

- **文档**
  - 本地命令：`uv run python -m sphinx -b html docs docs/_build/html -W -n --keep-going`
  - CI 阶段：独立 `docs.yml`

- **E2E**
  - 本地命令：`uv run python -m pytest -q tests/e2e -m e2e`
  - CI 阶段：未落地

- **性能**
  - 本地命令：`uv run python -m pytest -q tests/performance -m performance`
  - CI 阶段：未落地（Nightly）

仓库 `Makefile` 已提供 `coverage` / `coverage-report`，本地优先复用，避免命令漂移。

### 11.6 失败排查顺序

1. 先看**第一个失败**，不要被后续级联失败干扰。
2. 重跑单个文件，排除数据库/临时文件残留。
3. 单独运行该测试，排除顺序依赖（尤其是共享 fixture 或全局状态）。
4. 检查环境差异：Python 版本、依赖版本、SQLite 版本、时区。
5. 最后再怀疑实现；确认是缺陷后，先补失败测试，再修复。

## 12. 分阶段执行计划

> 四周计划按当前真实差距重排。集成测试已超额，不需要再“从 0 建”。

#### Phase 0：基线与清理（1–2 天）

- [x] 运行全量测试，记录通过数/耗时
- [ ] 运行 `coverage`，记录行/分支/函数覆盖率
- [ ] 注册 markers（unit/integration/e2e/browser/performance/slow）
- [x] 新增 `mail_outbox` fixture，替换 `mail_data`
- [ ] 新增 `db_setup`、`user_factory`、`admin_user`、`authenticated_client`
- [ ] 清理 `tests/tmp`、`tests/integration/tmp` 等临时产物（确认是否应被忽略）

**验收：** 全量测试通过；覆盖率基线记录在文档/CI。

#### Phase 1：Unit 补强（第 1 周）

- [ ] TC-DATA-012/TC-DATA-013/TC-DATA-014：Query 搜索语义、过滤操作符、一对多计数
- [ ] TC-SEC-003/TC-SEC-004/TC-SEC-006/TC-SEC-007：加密、序列化过期/篡改
- [ ] TC-USER-012/TC-USER-013：`get_users`、`remove_user`
- [ ] TC-EMAIL-002/TC-EMAIL-006/TC-EMAIL-007：Emailer 错误路径（TC-EMAIL-005 已由 SMTP 证书测试覆盖）
- [ ] TC-CLI-001～TC-CLI-006：Commands（含 `test_cli_runner` 示例）
- [ ] TC-FORM-010/TC-FORM-012/TC-FORM-015：CSRF 边界、formdata、InlineModelField
- [ ] TC-DATA-019～TC-DATA-027：事务、级联、外键、唯一约束
- [ ] TC-SIGNAL-001～TC-SIGNAL-006：信号载荷与 sender 错误
- [ ] TC-I18N-001～TC-I18N-006：语言、时区、复数、回退

**验收：** 新增 P0/P1 用例通过；关键路径 unit 覆盖补齐。

#### Phase 2：Integration 补强（第 2 周）

- [ ] TC-ADMIN-021：Inline + AJAX 外键（先写失败测试，修复 CR-001）
- [x] TC-ADMIN-031：一对多搜索计数（CR-002 按列表行数一致）
- [ ] TC-ADMIN-025/TC-ADMIN-026/TC-ADMIN-028：权限矩阵
- [ ] TC-ADMIN-014/TC-ADMIN-015：导出边界与类型
- [x] TC-ADMIN-032：URL 特殊字符（已补）
- [ ] TC-ADMIN-033：空结果/越界页
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

本节是测试目标与快照状态的唯一维护位置；当前状态引用前按第 1.5 节复核，阶段行动见第 12 节。

- **集成测试**
  - 目标：30+
  - 当前真实状态：132 个集成测试函数（57 + 24 + 22 + 21 + 8），已超额
  - 本方案动作：不再追求数量，补关键缺口

- **E2E 测试**
  - 目标：20+
  - 当前真实状态：0
  - 本方案动作：Phase 3 在 `tests/e2e/` 覆盖核心旅程；阶段验收见第 12 节

- **性能测试**
  - 目标：15+
  - 当前真实状态：0
  - 本方案动作：Phase 4 建 `tests/performance/` 并建立基线；阶段行动见第 12 节

- **覆盖率**
  - 目标：≥85%
  - 当前真实状态：84%（2026-11-13，仅 `src/flask_exts`）
  - 本方案动作：未达标；作为基线监控，补关键路径测试

- **分支覆盖**
  - 目标：≥75%
  - 当前真实状态：未测量
  - 本方案动作：同上

- **函数覆盖**
  - 目标：≥90%
  - 当前真实状态：未测量
  - 本方案动作：同上

- **关键路径**
  - 目标：100%
  - 当前真实状态：未系统定义
  - 本方案动作：第 6/10 节已列清单

- **测试框架**
  - 目标：pytest + 插件
  - 当前真实状态：pytest + pytest-cov
  - 本方案动作：按需引入 benchmark/browser

- **测试目录**
  - 目标：unit/integration/e2e/performance
  - 当前真实状态：unit/integration
  - 本方案动作：按 Phase 创建

- **Fixtures**
  - 目标：app/client/db/user/admin/auth
  - 当前真实状态：已有 app/client/admin/login_as_admin
  - 本方案动作：补 db_setup/user_factory

- **数据库事务**
  - 目标：有设计
  - 当前真实状态：0
  - 本方案动作：新增 TC-DATA-019～TC-DATA-027

- **错误处理**
  - 目标：未明确
  - 当前真实状态：0
  - 本方案动作：新增 TC-ERROR-001～TC-ERROR-008

- **CI/CD**
  - 目标：集成
  - 当前真实状态：`ci.yml` 已运行 Python 3.11–3.13 矩阵、覆盖率报告与 PR 变更文件 lint；`docs.yml` 构建文档；尚无 `fail-under` 门槛与 E2E
  - 本方案动作：Phase 4 补

- **测试文档**
  - 目标：完整
  - 当前真实状态：本文 v0.1
  - 本方案动作：已补齐；按 Phase 0 升 v1.0

**对历史“完成声明”的说明**：

- 历史规划文档曾声称“95% 完成”，但“集成测试 30+ / E2E 20+ / 性能 15+”在验收清单中标记为“计划”，不是“已实现”。
- 其中描述的 `tests/integration/conftest.py`、`tests/e2e/`、`tests/performance/` 在当前仓库中并不存在（当前只有各子目录的 `conftest.py`）。
- 因此，本方案只把它当作“设计参考”，而不是“完成证明”。

## 14. 测试债务与改进清单

- **T1**
  - 债务：模块级 `mail_data`（已修复）
  - 位置：`tests/integration/usercenter/test_user_view.py`
  - 影响：已改为 function-scope `mail_outbox` fixture
  - 建议：保持每个测试独立 outbox

- **T2**
  - 债务：序列化过期断言被注释
  - 位置：`tests/integration/security/test_core.py`
  - 影响：过期路径无保护
  - 建议：用可控时间/短 max_age 补测

- **T3**
  - 债务：`test_count_query` 只断言非空
  - 位置：`tests/unit/datastore/sqla/test_query.py`
  - 影响：计数错误无法发现
  - 建议：断言具体数值，加一对多用例

- **T4**
  - 债务：关联搜索未断言 count
  - 位置：`tests/integration/admin/sqla/test_search.py`
  - 影响：分页总数可能错
  - 建议：加 `count` 断言

- **T5**
  - 债务：Inline AJAX 未触发缺陷
  - 位置：`tests/integration/admin/sqla/test_inline_ajax.py`
  - 影响：CR-001 可能漏测
  - 建议：配置子模型 `ajax_refs` 并访问页面

- **T6**
  - 债务：`get_users`/`remove_user` 无测试
  - 位置：`tests/integration/userstore/`
  - 影响：接口不一致
  - 建议：补契约测试

- **T7**
  - 债务：CLI 无测试
  - 位置：无
  - 影响：命令回归无保护
  - 建议：新增 `test_commands.py`

- **T8**
  - 债务：无 E2E/性能基线
  - 位置：全局
  - 影响：跨模块流程与性能退化不可度量
  - 建议：按 Phase 3/4 落地；覆盖率基线已见 10.5

- **T9**
  - 债务：测试名偏泛
  - 位置：`test_base`、`test_from` 等
  - 影响：可读性差
  - 建议：改为行为描述

- **T10**
  - 债务：注释/print 残留
  - 位置：多个测试
  - 影响：噪音
  - 建议：清理，保留必要说明

- **T11**
  - 债务：临时目录
  - 位置：`tests/tmp`、`tests/integration/tmp`、`tests/integration/data`
  - 影响：可能污染仓库
  - 建议：确认用途，加入 `.gitignore` 或清理

- **T12**
  - 债务：无 marker
  - 位置：全局
  - 影响：无法快慢分离
  - 建议：注册并使用

- **T13**
  - 债务：未验证并行/随机顺序
  - 位置：全局
  - 影响：隐藏顺序依赖
  - 建议：引入 `pytest-xdist`/`pytest-randomly` 前先做隔离审计

- **T14**
  - 债务：仅 SQLite
  - 位置：全局
  - 影响：生产数据库差异未覆盖
  - 建议：夜间跑 PostgreSQL，重点覆盖 CR-002/外键/大小写

- **T15**
  - 债务：文档示例与仓库未对齐
  - 位置：第 4、8、9 节
  - 影响：复制示例无法直接运行
  - 建议：Phase 0 落地 fixture/marker，示例标注状态

- **T16**
  - 债务：统计数字易过期
  - 位置：1.1/1.2
  - 影响：文档失真
  - 建议：用 1.5 脚本定期重算

- **T17**
  - 债务：邮件/信号载荷契约未文档化
  - 位置：`security/token_action.py`
  - 影响：测试断言字段靠猜
  - 建议：在 7.12 固定字段表并加契约测试

- **T18**
  - 债务：覆盖率未设 CI 门槛
  - 位置：10.3/10.5
  - 影响：覆盖率回退无法自动阻断
  - 建议：以 10.5 基线设置阈值并接入 CI

- **T19**
  - 债务：上传/导出临时文件路径不统一
  - 位置：forms/admin 测试
  - 影响：残留或互相覆盖
  - 建议：统一用 `tmp_path`

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
- [ ] 测试代码保持英文（i18n 或非 ASCII 编码测试除外）
- [ ] 新增公共 fixture 有 docstring
- [ ] 变更缺陷时先写失败测试，再修复
- [ ] 不通过 `warnings.catch_warnings()` / `simplefilter()` 局部处理 `DeprecationWarning`；直接断言声明版本下的行为

### 15.4 反模式

- `assert rv.status_code == 200` 唯一断言
  - 问题：页面可能空白/错误
  - 替代：加内容/DB 断言

- `xfail(raises=Exception)`
  - 问题：掩盖未知异常
  - 替代：断言具体异常

- **注释掉断言**
  - 问题：失去保护
  - 替代：修复或删除测试

- **模块级 list 收集状态**
  - 问题：顺序/并行敏感
  - 替代：fixture

- **测试中复制生产逻辑**
  - 问题：双重维护
  - 替代：调用真实函数

- **过度 mock**
  - 问题：测不到集成问题
  - 替代：只 mock 外部边界

- **依赖当前时间**
  - 问题：间歇失败
  - 替代：固定时间/相对时间

- `catch_warnings()` + `simplefilter("error", DeprecationWarning)`
  - 问题：掩盖对旧 API 的依赖，升级后仍可能失效
  - 替代：直接使用并断言新 API；弃用告警交给项目级 pytest 配置

- `try: import ... except ImportError` 版本回退
  - 问题：兼容分支长期滞留，测试矩阵翻倍
  - 替代：只支持声明版本；无法支持时提升下限并记录变更

### 15.5 断言层次

- **HTTP**
  - 何时必须：所有请求
  - 示例：`status_code`、`Location`、`Content-Type`

- **页面内容**
  - 何时必须：渲染类测试
  - 示例：关键文本、表单错误、成功提示

- **数据库**
  - 何时必须：涉及写入/删除
  - 示例：重新查询最终状态

- **副作用**
  - 何时必须：涉及邮件/文件/信号
  - 示例：outbox、文件存在、信号收到

- **计数**
  - 何时必须：列表/分页/搜索
  - 示例：`count`、页数、总记录数

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

**基础设施**：

- [ ] `tests/e2e/`、`tests/performance/` 目录建立
- [ ] markers 注册，默认运行排除 performance/browser
- [x] `mail_outbox` 在 usercenter 测试模块可用
- [ ] `db_setup`、`user_factory`、`admin_user`、`authenticated_client` 可用
- [ ] `query_counter`、`seeded_db`、`tmp_upload_dir` 可用
- [x] 覆盖率命令可重复执行，基线已记录

**测试覆盖**：

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

**质量门禁**：

- [ ] Python 3.11–3.13 全绿
- [ ] `ruff`、`sphinx -W`、`djlint` 通过
- [ ] 无新增无理由 `skip`/`xfail`
- [ ] CI 运行 unit/integration/coverage/docs/E2E
- [ ] 夜间 performance/browser 任务（可选）

**文档**：

- [ ] 顶部 `更新时间` 与实际一致；文档版本与状态见 `README.md` 第 1 节
- [ ] 1.5 统计脚本可重复执行，数字与仓库一致
- [ ] 关键契约的验收字段均有明确映射或待补说明，并已核对其测试设计与证据
- [ ] 所有示例标注“现有/待补/目标”，不把规划写成现状
- [ ] 新增 fixture/测试模式有示例
- [ ] 目标对照清单更新
- [ ] 测试债务清单持续维护

**v1.0 判定**：

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

1. 运行 1.5 的统计脚本，更新 1.1/1.2 数字；发布状态变化时更新 `release.md` 第 1 节。
2. 更新 6.1 模块覆盖矩阵；按需更新 6.2 章节导航，并在各契约“验收”字段维护具体追溯映射。
3. 更新 7.x 用例状态（现有/待补/待修），新增缺陷对应用例。
4. 更新 10.5 覆盖率基线、9.7 性能基线。
5. 更新 14 测试债务、16 验收标准。
6. 若章节结构变化，同步更新目录与 `spec.md` 的互链。
