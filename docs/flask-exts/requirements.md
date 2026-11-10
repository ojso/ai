# Flask-Exts 行为契约与需求目录（Requirements & Contracts）

> 本文是 Flask-Exts 的**行为契约单一事实源**：用稳定的 `REQ-*` 编号描述“系统应该怎样”，并给出前置条件、输入、行为、输出/副作用、错误、不变量与验收依据。
>
> | 项目 | 内容 |
> | --- | --- |
> | 文档版本 | v0.1（首批 49 条） |
> | 状态 | 可用 |
> | 最后更新 | 2026-11-10 |
> | 数据快照 | 2026-11-10（源码版本 `0.4.0`；HEAD `171b40968f309c04ae3ad423696227c2767b0055`） |
> | 适用仓库 | `flask-exts` |
> | 配套文档 | `architecture.md`（架构）、`spec.md`（设计/实现）、`testing.md`（测试）、`demo.md`（示例）、`security.md`（安全）；View/Admin 见 `spec.md` 第 10 章 |
>
> **使用规则**
>
> - 测试从本文的 `REQ-*` 推导，而不是从实现反推。
> - 适用契约应有可追溯的验收证据；无测试时按第 2 节区分测试缺口与已证实的实现缺口，不得仅凭缺少测试认定代码不满足契约。
> - 本文描述“应该怎样”；`spec.md` 描述“为什么这样设计/当前怎么实现”；两者冲突时按本文第 2.4 节处理。
> - 安全边界、威胁模型和运营检查仍以 `security.md` 为准；本文只登记可验证的安全行为契约。

## 目录

- [0. 快速使用](#0-快速使用)
- [1. 契约格式与编号](#1-契约格式与编号)
- [2. 状态、追溯与冲突处理](#2-状态追溯与冲突处理)
- [3. 扩展生命周期](#3-扩展生命周期)
- [4. 数据库与查询](#4-数据库与查询)
- [5. 认证与会话](#5-认证与会话)
- [6. 授权](#6-授权)
- [7. 注册与邮箱验证](#7-注册与邮箱验证)
- [8. 密码重置](#8-密码重置)
- [9. 令牌](#9-令牌)
- [10. CSRF](#10-csrf)
- [11. Admin / View](#11-admin--view)
- [12. 追溯与状态导航](#12-追溯与状态导航)

## 0. 快速使用

### 0.1 写测试时

1. 找到要验证的 `REQ-*`。
2. 阅读“行为 / 输出 / 错误 / 不变量”。
3. 在测试的 docstring、测试名或注释中标注实际契约编号；以下为历史格式示例，仍然有效：

```python
def test_login_success_creates_session(app, client, user_factory):
    """REQ-AUTH-001: valid credentials establish a session."""
    ...
```

4. 在本契约的“验收”字段维护用例 ID 与实际测试入口；`testing.md` 维护相应用例设计。测试或路径尚未核实时标“待补”或“待确认”。

### 0.2 改行为时

按 [`AGENTS.md` 第 3 节](./AGENTS.md#3-事实源与冲突处理)处理契约与实现冲突；修改契约时保留已批准基线及历史，不以代码现状替代预期行为。

## 1. 契约格式与编号

### 1.1 编号规则

契约编号格式：

```text
REQ-<领域>-<序号>
```

例如 `REQ-AUTH-001` 中，`REQ` 表示行为契约，`AUTH` 表示领域，`001` 是该领域内的序号。能力名称可用于描述或检索，不放入编号。

- 领域使用 `glossary.md` 第 1.1 节登记的词表；由大写英文字母开头，后续只能使用大写字母或数字，不含分隔符。无法确定归类时先标“待确认”，不得自行猜测或创建缩写。
- 序号按领域独立分配：`001`～`999` 使用三位，超过 `999` 使用自然位数；不使用 `000`。完整编号全局唯一。
- 分配前先查现有契约，避免同一行为重复登记；再检查本文契约、已登记的历史别名和废弃编号，取该领域已分配的最大序号加一，无已分配编号时从 `001` 开始。并行变更合并前检查并解决冲突。
- 编号一经分配永不复用；领域重组不自动改变现有编号。契约弃用或取代时，按第 2.1 节保留编号、适用范围和替代关系。
- 一个新增 `REQ` 只描述一个可验证行为；契约描述可观察结果，不绑定内部类名/函数名，除非行为依赖它。实现细节链接相关领域文档。

**编号调整**：此前曾说明带能力段的格式，其文档示例未分配；若仓库或其他外部记录已使用该格式，应先核实实际指向并保留历史引用，不推定它与本文某条契约等价。后续确需迁移或拆分时，先评估关联测试、风险、文档和外部引用，在契约条目记录新旧编号及对应关系；单纯换号不是废弃契约，一对多拆分须分别核对验收。仓库不可见时不得声称已同步。

历史条目可能包含多个行为，例如 `REQ-DATA-002`；只有在明确需要拆分时才处理，不为符合编号格式擅自改变原契约。

### 1.2 条目模板

每条契约需包含下表所列信息。状态字段默认值为 `lifecycle=unknown`、`implementation=unknown`、`verification=unverified`；条目可省略默认状态，非默认状态必须显式记录。

| 字段 | 要求 |
| --- | --- |
| `lifecycle` | 契约的生命周期；取值见第 2.1 节 |
| `implementation` | 实现完成程度；取值见第 2.1 节 |
| `verification` | 对指定版本和范围的验收结果；取值见第 2.1 节 |
| 前置 | 触发行为前必须成立的条件 |
| 输入 | 请求参数、表单、令牌、配置等 |
| 行为 | 系统必须做什么 |
| 输出/副作用 | 响应、状态码、重定向、数据库变化、邮件、session |
| 错误 | 必须返回的错误类型/状态/提示 |
| 不变量 | 任何情况下都不能发生的事 |
| 验收 | 用例 ID、实际测试入口和验证证据；未完成或未核实时说明原因 |
| 关联 | 架构/安全/示例文档与已知问题链接；被取代时包含 `superseded-by` |

## 2. 状态、追溯与冲突处理

### 2.1 状态定义

每条契约分别记录生命周期、实现完成程度和验收结果三个相互独立的状态；缺陷与风险放在“关联”字段，不增加状态维度。状态字段名和枚举值使用小写英文及 kebab-case。

**`lifecycle`：契约生命周期**

| 状态 | 含义 |
| --- | --- |
| `draft` | 草拟中，尚未作为批准的基线 |
| `in-review` | 已提交评审，检查完整性、可验证性和冲突 |
| `approved` | 已由有权维护者确认并纳入适用基线；记录批准依据、日期及契约修订 |
| `deprecated` | 不推荐用于新用途；既有版本是否仍适用须明确记录 |
| `superseded` | 已有替代契约；通过 `superseded-by` 关联一个或多个 `REQ-*`，注明旧契约的适用和兼容范围 |
| `unknown` | 审批或适用范围尚未确认；不代表契约无效 |

通常由 `draft` 经 `in-review` 到 `approved`，再按需要弃用或取代；修订有效契约时保留已批准基线，不用未批准草稿静默覆盖。已废弃或被取代的编号不复用。

**`implementation`：实现完成程度**

| 状态 | 含义 |
| --- | --- |
| `not-started` | 已确认适用范围内尚未开始实现；不能仅凭缺少测试推断 |
| `in-progress` | 已开始但尚未完成适用范围的实现，注明未完成部分；暂停工作仍属于此状态 |
| `implemented` | 已有证据表明实现工作按计划完成，不等于验收通过或不存在缺陷 |
| `unknown` | 未获得足够证据判断当前实现 |

开发任务是否正在进行由任务记录跟踪；测试未补齐不自动意味着实现尚未完成。

**`verification`：验收结果**

| 状态 | 含义 |
| --- | --- |
| `unverified` | 当前版本尚无足够证据确认全部适用验收通过，不代表从未运行测试 |
| `passed` | 指定契约修订、实现版本、环境和范围内，所有适用验收均通过并留有证据 |
| `failed` | 有证据表明当前范围内的验收未通过；记录失败范围和结果 |
| `blocked` | 验收因环境、权限等障碍无法完成；记录阻塞原因和已有结果，不把阻塞当作通过或抹去已知失败 |

`failed` 可以发生在实现完成前。测试文件或用例 ID 存在不等于执行通过；部分通过不等于整条契约 `passed`。代码、契约、依赖或环境变化可能使结果失效，应评估影响并重新验证；若不再有充分证据证明通过，按实际情况标 `unverified`、`failed` 或 `blocked`。

**问题关联与风险**

- 在“关联”字段登记已确认的契约实现缺口：`security.md` 的 `SEC-*`、`spec.md` 第 10.16 节的 `C*`/`V-*`，或项目认可的问题跟踪记录；问题详情、处置状态和风险接受由对应问题来源维护。
- 未核实的写“待核实”；未记录缺口不等于没有缺口。已排查且没有已确认缺口时，注明排查版本、范围与日期，不能推断绝对无缺陷。未实现的规划功能不自动等同于已确认缺陷。
- 影响契约验收的缺口未解决时，不能因为风险被接受而标 `passed`；发布例外仍须按 `release.md` 的门禁和审批处理。`V-01` 与 `SEC-19` 是同一问题的不同记录，不按两个独立缺陷计数。

现有契约的审批和源码/验收证据尚未逐条核实，生命周期和实现状态标 `unknown`，验证状态标 `unverified`。这不等于契约失效或未排除风险已关闭；在维护者确认适用性前，应按既有契约和未排除风险进行影响评估，不得据此静默放行。

**记录示例（仅演示字段，不代表实际项目状态）：**

```markdown
- **lifecycle**：`approved`（批准依据、日期及契约修订）
- **implementation**：`implemented`（实现依据及代码版本）
- **verification**：`failed`（验收范围、执行时间和失败证据）
- **关联**：已登记的问题编号及其权威记录
```

此例表示契约已经批准、实现工作已完成，但验收失败；修复并通过全部适用验收后，才能按证据更新验证状态。

### 2.2 追溯规则

- `REQ` → `TC`（`testing.md` 测试用例编号）→ 测试文件/函数；用例编号与历史映射见 `testing.md` 第 6.3 节。
- `REQ` → `demo.md` 场景（如果用户可见）。
- `REQ` → `spec.md` 第 10 章 / `security.md`（如果涉及领域细节）。
- 已知缺口通过“关联”字段指向对应问题记录；其中 `SEC-*` 见 `security.md` 第 11 节，`C*`/`V-*` 见 `spec.md` 第 10.16 节。

单条契约的“验收”字段是 `REQ → TC → 测试入口` 的唯一维护入口；第 12 节仅提供导航，不复制映射。新增或修改契约时，记录测试设计 ID、实际测试文件/函数和执行结果；不存在或尚未核实的项目写“待补”或“待确认”，不要虚构路径。用户可见变更按适用性关联 demo；demo 不能替代自动化断言。

判定 `passed` 时，验收记录须能追溯契约修订、代码版本或 commit（工作树有改动时记录差异）、环境、验收范围、执行时间、测试命令或人工验收方式及结果。仅有用例 ID、文件名或 `REQ` 字符串不证明断言覆盖契约，更不证明测试执行成功。无法查看源码、测试或审批记录时，按第 2.1 节标 `unknown` 或 `unverified`；不能仅凭缺少证据认定代码不满足契约。

### 2.3 当前首版范围

本版覆盖首批核心契约：

- 扩展生命周期
- 数据库/查询
- 登录/会话/TFA
- 授权
- 注册/邮箱验证/改邮箱
- 密码重置
- 令牌
- CSRF
- Admin 列表/搜索/筛选/排序/计数/CRUD/Inline/AJAX/导出/权限
- 自定义 View

### 2.4 冲突处理

按 [`AGENTS.md` 第 3 节](./AGENTS.md#3-事实源与冲突处理)处理。契约的生命周期、实现与验证状态仍以本节前述状态定义为准；未核实事实标“待核实”。

## 3. 扩展生命周期

### REQ-EXT-001 扩展注册与名称校验

- **前置**：无
- **输入**：`Extension` 子类
- **行为**：注册扩展；名称必须唯一、非空、ASCII 合法；重复名称拒绝
- **输出/副作用**：注册表新增实例；可被 `get_extension` 查询
- **错误**：重复名称/非 `Extension`/非法名称抛 `ExtensionError`
- **不变量**：同一注册表内名称唯一；失败注册不改变已有扩展
- **验收**：`testing.md` TC-EXT-001～TC-EXT-004；`tests/unit/extension_core/test_registry.py`
- **关联**：`spec.md` 第 11.1～11.3 节

### REQ-EXT-002 依赖顺序与依赖错误

- **前置**：扩展声明 `dependencies`
- **输入**：扩展注册顺序、依赖图
- **行为**：若扩展 A 依赖扩展 B，则 B 先于 A 初始化；无依赖扩展保持注册顺序；缺失依赖/循环依赖/自依赖拒绝
- **输出/副作用**：初始化顺序稳定
- **错误**：缺失依赖抛 `ExtensionNotFoundError`；循环/自依赖抛 `ExtensionDependencyError`
- **不变量**：任何扩展都不会在依赖之前初始化
- **验收**：`testing.md` TC-EXT-005～TC-EXT-010；`tests/unit/extension_core/test_registry.py`
- **关联**：`spec.md` 第 11.2/11.5 节

### REQ-EXT-003 两阶段初始化幂等与顺序

- **前置**：扩展已注册
- **输入**：`init_app` / `post_init`
- **行为**：`init_app` 先于 `post_init`；两阶段各自幂等；`post_init` 按依赖顺序执行
- **输出/副作用**：每个扩展的 `init_app`/`post_init` 最多执行一次
- **错误**：`post_init` 前未 `init` 抛 `ExtensionInitError`
- **不变量**：重复调用不产生重复注册/重复副作用
- **验收**：`testing.md` TC-EXT-011～TC-EXT-014；`tests/unit/extension_core/test_registry.py`
- **关联**：`spec.md` 第 11.4 节

### REQ-EXT-004 关闭顺序与异常隔离

- **前置**：扩展已初始化
- **输入**：`shutdown`
- **行为**：按初始化逆序关闭；单个扩展关闭异常不阻止其他扩展关闭
- **输出/副作用**：资源释放；产生 warning
- **错误**：单扩展异常被隔离
- **不变量**：关闭后不残留已绑定资源
- **implementation**：`in-progress`（当前 Registry 仅捕获 `ExtensionError`，其他普通异常会中断关闭循环）
- **verification**：`failed`（HEAD `171b40968f309c04ae3ad423696227c2767b0055`；现有 `test_shutdown_exception` 断言 `ValueError` 传播，与本契约相反；完整套件运行结果见 `testing.md` 第 1.1 节）
- **本轮实现观察**：源码位于 `src/flask_exts/extension_core/registry.py::ExtensionRegistry.shutdown_all`；测试入口为 `tests/unit/extension_core/test_registry.py::test_shutdown_exception`，问题关联 C11。
- **验收**：`testing.md` TC-EXT-015/TC-EXT-016；`tests/unit/extension_core/test_manager.py`
- **关联**：`spec.md` 第 11.4.3 节 C11；`testing.md` TC-EXT-016 现有断言与契约冲突

## 4. 数据库与查询

### REQ-DATA-001 单例绑定、会话与释放

- **前置**：Flask app 配置 `SQLALCHEMY_DATABASE_URI`
- **输入**：`db.init_app(app)` / `db.dispose()` / app context
- **行为**：默认导出的模块级 `db` 是一个 `SqlaDb` 实例；每个实例同一时刻绑定一个 app，绑定后 `db.session` 在 app context 内复用；未 dispose 时重复绑定抛错，dispose 后允许重新绑定；`reset_all()` 删表重建
- **输出/副作用**：engine/session 绑定到当前 app
- **错误**：缺少 URI/重复绑定抛 `RuntimeError`
- **不变量**：一个 `db` 实例同一时刻只绑定一个 app；上下文结束后 session 被移除
- **验收**：`testing.md` TC-DATA-001～TC-DATA-008；`tests/unit/datastore/sqla/test_db.py`
- **关联**：`spec.md` 第 12.3 节；`flask-exts/docs/advanced/database.rst`

### REQ-DATA-002 Query 的 JOIN、搜索、筛选与排序

- **前置**：SQLAlchemy 模型与关系
- **输入**：列路径、搜索词、过滤操作符、排序字段
- **行为**：关系路径自动 JOIN 并复用 alias；`=` 精确、`^` 前缀、`$` 后缀、否则包含；过滤支持 `==`/`!=`/`>`/`<`/`like`/`in`/`between`/`is_null` 等；排序支持单列/多列
- **输出/副作用**：生成可执行的 `Select`
- **错误**：无效关系路径抛 `ValueError`/`AttributeError`
- **不变量**：相同 JOIN 路径不重复生成 alias
- **验收**：`testing.md` TC-DATA-009～TC-DATA-018；`tests/unit/datastore/sqla/test_query.py`（部分）
- **关联**：`spec.md` 第 12.5 节；Admin 计数契约见 `REQ-ADMIN-005`

## 5. 认证与会话

### REQ-AUTH-001 登录成功建立会话

- **前置**：用户存在、密码正确、账号可登录、CSRF 通过
- **输入**：`username`、`password`、可选 `next`
- **行为**：校验密码哈希；`tfa_enabled=False` 时调用 `login_user(force=True)`；渲染/重定向到 `next` 或 `/user/index/`
- **输出/副作用**：session 中存在 `_user_id`；HTTP 302
- **错误**：无（失败见 `REQ-AUTH-002`）
- **不变量**：密码明文不落库、不进日志；`next` 必须经过安全重定向
- **验收**：`testing.md` TC-AUTH-003；实测入口为 `tests/integration/usercenter/test_user_view.py::TestUserView.register_and_login_user` 夹具，明确断言登录后 `session` 包含 `_user_id`。
- **关联**：`spec.md` 4.4；`security.md` 3.1

### REQ-AUTH-002 登录失败统一提示

- **前置**：无
- **输入**：不存在的用户名 / 错误密码
- **行为**：不区分“用户不存在/密码错误”；不存在用户也执行 dummy scrypt 校验；不建立 session
- **输出/副作用**：统一提示 `Invalid username or password.`
- **错误**：`InvalidCredentialsError` 被表单捕获
- **不变量**：响应不泄露用户是否存在；失败不产生 `_user_id`
- **验收**：`testing.md` TC-AUTH-004；`tests/integration/usercenter/test_user_view.py`
- **关联**：`security.md` 3.1/5.1

### REQ-AUTH-003 TFA 未完成不得建立会话

- **前置**：用户 `tfa_enabled=True`，密码正确
- **输入**：登录表单
- **行为**：只写 `pending_tfa_user_id`（及 remember 标记），**不调用** `login_user`；重定向 `/user/verify_tfa/?next=...`
- **输出/副作用**：session 无 `_user_id`；有 pending 标记
- **错误**：无
- **不变量**：TFA 完成前任何登录保护页不可访问
- **验收**：`testing.md` TC-SEC-018；`test_tfa`、`test_tfa_cannot_be_bypassed_after_password_login`
- **关联**：`security.md` 8.3

### REQ-AUTH-004 TFA 验证成功完成登录

- **前置**：session 中有有效 pending user，用户仍启用 TFA
- **输入**：正确 TOTP 或恢复码
- **行为**：验证第二因子；成功后 `login_user(force=True)`；清理 pending；设置 `tfa_verified`；重定向 `next`
- **输出/副作用**：session 中有 `_user_id` 与 `tfa_verified`；恢复码登录消耗一个恢复码
- **错误**：错误验证码不建立 session，提示 `Invalid code`
- **不变量**：第二因子失败不改变登录状态；恢复码只能使用一次
- **验收**：`testing.md` TC-SEC-016/TC-SEC-017；`test_tfa`、`test_recovery`
- **关联**：`security.md` 8.3

### REQ-AUTH-005 密码变更使旧会话失效

- **前置**：用户已登录
- **输入**：旧密码、新密码、重复新密码
- **行为**：校验旧密码；保存新哈希；`get_id()` 的密码指纹变化
- **输出/副作用**：旧 session 的 `_user_id` 失效；旧密码登录失败；新密码登录成功
- **错误**：旧密码错误/两次不一致时拒绝
- **不变量**：密码变更后旧会话不能继续访问受保护页
- **验收**：`testing.md` TC-SEC-019；`test_core.py::test_password_change_invalidates_existing_login_session`、`test_change_password`
- **关联**：`security.md` 5.3；JWT 例外见 `security.md` SEC-08

### REQ-AUTH-006 登出清理认证与 TFA 状态

- **前置**：用户已登录或处于 TFA pending
- **输入**：`GET /user/logout/`
- **行为**：调用 `logout_user`；清理 `_user_id`、`tfa_verified`、`tfa_recovery`、pending TFA、rebind pending、remember 标记
- **输出/副作用**：重定向登录页；session 无认证残留
- **错误**：无
- **不变量**：登出后不能恢复半完成 TFA 登录
- **验收**：`testing.md` TC-AUTH-006；`test_tfa` 的登出断言
- **关联**：`security.md` 3.4

### REQ-AUTH-007 未激活账号的访问边界

- **前置**：用户已认证但 `is_active=False`（非 admin）
- **输入**：访问资料/账号功能
- **行为**：`profile`/`index` 可访问；`change_password`、`email_change`、`enable_tfa`、`setup_tfa`、`recovery_codes` 被拒绝
- **输出/副作用**：拒绝时 403
- **错误**：`@requires_active` 拒绝
- **不变量**：未激活账号不能使用账号级功能
- **验收**：`testing.md` TC-AUTH-020；`test_inactive_account_blocked_from_account_features`
- **关联**：`security.md` 4.4；admin 例外见 `REQ-AUTHZ-005`

### REQ-AUTH-008 安全重定向

- **前置**：请求含 `next` / `url` 参数
- **输入**：任意重定向目标
- **行为**：只允许本地路径；拒绝绝对 URL、协议相对 URL、反斜杠、编码 `//`、畸形 URL、首字符空白
- **输出/副作用**：非法目标回退到安全默认 URL
- **错误**：不抛异常，直接使用 fallback
- **不变量**：不能重定向到外部域名
- **验收**：`testing.md` TC-SEC-020；`tests/unit/security/test_urls.py`
- **关联**：`security.md` 7.5

## 6. 授权

### REQ-AUTHZ-001 admin 角色允许访问 Admin

- **前置**：用户有 `admin` 角色
- **输入**：访问 Admin 视图
- **行为**：`SimpleAuthorizer` 放行
- **输出/副作用**：视图可渲染
- **错误**：无
- **不变量**：非 admin/非 super_admin 默认拒绝
- **验收**：`testing.md` TC-SEC-012；`tests/unit/security/test_authorizer.py::test_allow_admin_user`
- **关联**：`security.md` 4.2

### REQ-AUTHZ-002 默认拒绝与匿名访问

- **前置**：无认证或用户无角色
- **输入**：访问普通 Admin/ModelView
- **行为**：匿名 ModelView 返回 403；`@login_required` 先重定向登录；无角色普通用户拒绝
- **输出/副作用**：403 或登录重定向
- **错误**：默认拒绝
- **不变量**：未授权用户不能访问 Admin 模型数据
- **验收**：`testing.md` TC-ADMIN-025/TC-ADMIN-026、TC-SEC-013；`test_authorizer.py`
- **关联**：`security.md` 4.2/4.5

### REQ-AUTHZ-003 allow_access 公开视图

- **前置**：视图设置 `allow_access=True`
- **输入**：匿名/已登录请求
- **行为**：允许访问；不再要求 admin/super_admin；`@requires_active` 的方法仍检查 active
- **输出/副作用**：公开页面可访问
- **错误**：无
- **不变量**：公开视图不能泄露受保护数据
- **验收**：`testing.md` TC-SEC-014；`test_authorizer.py::test_view_allow_access_precedes_authentication_gates`
- **关联**：`security.md` 4.2

### REQ-AUTHZ-004 requires_active 保护账号功能

- **前置**：方法标记 `@requires_active`
- **输入**：已登录用户请求
- **行为**：`is_active=False` 时拒绝；`is_active=True` 时继续后续授权
- **输出/副作用**：403
- **错误**：拒绝
- **不变量**：未激活账号不能使用标记为 active-only 的功能
- **验收**：`testing.md` TC-SEC-015；`test_inactive_account_blocked_from_account_features`
- **关联**：`security.md` 4.2

### REQ-AUTHZ-005 禁用 admin 必须失去 Admin 权限

- **前置**：用户有 `admin` 角色且 `is_active=False`
- **输入**：访问 Admin/账号功能
- **行为**：**必须拒绝**；禁用账号不能继续使用高权限
- **输出/副作用**：403/拒绝
- **错误**：拒绝
- **不变量**：`is_active=False` 必须覆盖 `admin` 角色
- **implementation**：`in-progress`（`SimpleAuthorizer.allow` 在 `is_active` 检查前放行 `admin`，禁用管理员仍可访问）
- **verification**：`failed`（HEAD `171b40968f309c04ae3ad423696227c2767b0055` 源码判定逻辑存在确证缺陷；问题关联 SEC-01）
- **本轮实现观察**：静态源码确认短路分支存在；待补针对该场景的自动化拒绝测试。
- **验收**：待补（新增测试将先失败）；关联 `security.md` SEC-01
- **关联**：`security.md` 4.3；`spec.md` 第 7 章；风险关联 `SEC-01`（本轮 HEAD 静态核对，未专项测试）

### REQ-AUTHZ-006 role_need 与 super_admin

- **前置**：用户 active
- **输入**：`role_need` 或 `super_admin` 角色
- **行为**：`role_need` 匹配放行；`super_admin` 放行；inactive 的非 admin 用户拒绝
- **输出/副作用**：允许/拒绝
- **错误**：无匹配时拒绝
- **不变量**：inactive 用户不能靠 `role_need`/`super_admin` 绕过 active 检查
- **验收**：`testing.md` TC-SEC-013；`test_authorizer.py::test_authorize_without_view_uses_permission_context`
- **关联**：`security.md` 4.2

## 7. 注册与邮箱验证

### REQ-REG-001 注册创建激活但未验证邮箱的用户

- **前置**：用户名/邮箱未被占用
- **输入**：`username`、`password`、`email`、CSRF
- **行为**：创建用户；密码哈希；`is_active=True`；`email_verified=False`；不自动登录；发送 `user_registered` 信号
- **输出/副作用**：用户落库；重定向登录；验证邮件（若配置 sender）
- **错误**：重复用户名/邮箱提示
- **不变量**：密码明文不落库；邮箱验证状态不改变 active
- **验收**：`testing.md` TC-AUTH-001；`test_register`
- **关联**：`security.md` 3.5

### REQ-REG-002 重复用户名/邮箱拒绝

- **前置**：用户名或邮箱已存在
- **输入**：注册表单
- **行为**：拒绝创建；提示重复字段；不产生新用户
- **输出/副作用**：错误提示；数据库无新记录
- **错误**：`UserAlreadyExistsError` / 表单错误
- **不变量**：用户名/邮箱唯一
- **验收**：`testing.md` TC-AUTH-002；实测入口为 `tests/integration/usercenter/test_user_view.py::TestUserView.test_register_rejects_duplicate_email`（断言 `Email already exists.`）；注册时用户名重复路径当前缺少自动化用例（测试缺口，待补）。
- **关联**：`security.md` 5.2

### REQ-REG-003 邮箱验证令牌

- **前置**：用户有邮箱且未验证
- **输入**：验证令牌
- **行为**：校验签名/时间/邮箱哈希/密码哈希；标记 `email_verified=True`、`email_verified_at`；不修改 `is_active`；重复使用返回 `already_verified`
- **输出/副作用**：用户邮箱状态更新
- **错误**：过期/无效/用户不存在分别返回错误状态
- **不变量**：验证邮箱不改变账号 active 状态
- **验收**：`testing.md` TC-SEC-008；实测入口为 `tests/integration/security/test_core.py::TestSecurityCore.test_verify_email`（断言返回 `verified`、标记 `email_verified=True` 且保持 `is_active=True`，无效令牌抛 `InvalidTokenError`）；HTTP 路由级过期边界待补自动化用例。
- **关联**：`security.md` 6.3

### REQ-REG-004 重发验证邮件

- **前置**：用户已登录
- **输入**：POST `/user/resend_verification/`
- **行为**：已验证提示；未验证且有邮箱则发送新令牌；无邮箱提示错误
- **输出/副作用**：邮件；重定向 profile
- **错误**：表单失败 400
- **不变量**：不改变 active/email_verified
- **验收**：`testing.md` TC-AUTH-009；`test_resend_email_verification`
- **关联**：`security.md` 6.3

### REQ-REG-005 改邮箱需要密码与新邮箱确认

- **前置**：用户已登录且 active
- **输入**：新邮箱、当前密码、CSRF
- **行为**：校验当前密码；新邮箱格式合法；发送确认链接到新邮箱；确认前旧邮箱继续有效；确认后更新邮箱并标记已验证；重复邮箱拒绝
- **输出/副作用**：确认邮件；确认后用户邮箱变化
- **错误**：密码错误/邮箱非法/重复邮箱拒绝
- **不变量**：未确认前不切换邮箱；旧令牌在邮箱/密码变化后失效
- **验收**：`testing.md` TC-AUTH-010～TC-AUTH-012、TC-SEC-009；`test_change_email_*`
- **关联**：`security.md` 6.4

### REQ-REG-006 注册邮箱必须是合法邮箱格式

- **前置**：注册表单提交
- **输入**：`email`
- **行为**：必须是合法邮箱格式；非法格式拒绝
- **输出/副作用**：表单错误
- **错误**：邮箱格式错误
- **本轮实现观察**（HEAD `171b40968f309c04ae3ad423696227c2767b0055`）：静态源码显示 `RegisterForm.email` 只有 `DataRequired()`、没有 `Email()`（`security.md` SEC-05）；未运行无效邮箱注册复现
- **验收**：待补（新增无效邮箱注册测试）
- **关联**：`security.md` SEC-05（本轮 HEAD 静态核对，未专项测试）

## 8. 密码重置

### REQ-RESET-001 找回密码不泄露邮箱是否存在

- **前置**：无（未登录）
- **输入**：邮箱
- **行为**：无论邮箱是否存在都显示同一提示；仅对存在且 `email_verified=True` 的用户发送重置令牌
- **输出/副作用**：统一提示；可能发送邮件
- **错误**：无（不暴露存在性）
- **不变量**：响应内容/时序不应明显区分邮箱是否存在（时序为尽力而为）
- **验收**：`testing.md` TC-AUTH-014；`test_forgot_password`
- **关联**：`security.md` 6.5

### REQ-RESET-002 重置令牌校验与密码更新

- **前置**：用户 `email_verified=True`
- **输入**：重置令牌、新密码、重复密码、CSRF
- **行为**：校验令牌；要求邮箱已验证；设置新密码哈希；成功后重定向登录
- **输出/副作用**：密码更新；旧密码失效
- **错误**：过期/无效/未验证/缺少密码分别拒绝
- **不变量**：未验证邮箱不能重置；令牌不可跨密码/邮箱变化复用
- **验收**：`testing.md` TC-SEC-010；实测入口为 `tests/integration/security/test_core.py::TestSecurityCore.test_verify_email`（插件级重置密码与二次使用抛 `InvalidTokenError`）与 `tests/integration/usercenter/test_user_view.py::TestUserView.test_forgot_password`（端到端表单提交）；HTTP 级令牌过期场景待补用例。
- **关联**：`security.md` 6.5

### REQ-RESET-003 重置后旧密码/旧令牌/旧会话失效

- **前置**：重置成功
- **输入**：旧密码/旧令牌/旧 session
- **行为**：旧密码登录失败；旧令牌因密码哈希变化失效；旧 session 因密码指纹变化失效
- **输出/副作用**：新密码可登录
- **错误**：旧密码/旧令牌拒绝
- **不变量**：重置后旧凭据不可继续使用
- **验收**：`testing.md` TC-SEC-019；`test_core.py`、`test_change_password`
- **关联**：`security.md` 5.3/6.5；JWT 例外见 SEC-08

## 9. 令牌

### REQ-TOKEN-001 令牌载荷包含用户与凭据指纹

- **前置**：用户存在
- **输入**：用户、动作类型
- **行为**：生成载荷 `(user_id, email_hash, password_hash)`；改邮箱额外包含 `new_email`
- **输出/副作用**：签名令牌
- **错误**：用户/邮箱缺失时不生成
- **不变量**：令牌不能伪造；载荷长度/类型必须校验
- **验收**：`testing.md` TC-SEC-001/TC-SEC-005/TC-SEC-009；`test_core.py`
- **关联**：`security.md` 6.2

### REQ-TOKEN-002 令牌有效期与配置

- **前置**：无
- **输入**：`RESET_PASSWORD_MAX_AGE` / `VERIFY_EMAIL_MAX_AGE` / `CHANGE_EMAIL_MAX_AGE`
- **行为**：重置默认 1800 秒；验证/改邮箱默认 7 天；超过有效期返回 `expired`
- **输出/副作用**：过期令牌被拒绝
- **错误**：`ExpiredTokenError`
- **不变量**：过期令牌不能执行动作
- **验收**：`testing.md` TC-SEC-006；`tests/integration/security/test_core.py::test_serializer` 中第 51-57 行关于 `max_age=2` 的过期断言代码被注释，未形成有效自动化验收（测试缺口，待补）。
- **关联**：`security.md` 6.1

### REQ-TOKEN-003 无效/篡改/用户不存在令牌被拒绝

- **前置**：无
- **输入**：随机/篡改/错误 salt/未知用户令牌
- **行为**：签名无效/载荷错误 → `invalid`；用户不存在 → `no_user`
- **输出/副作用**：不执行动作
- **错误**：`InvalidTokenError` / `TokenUserNotFoundError`
- **不变量**：无效令牌不能修改任何用户状态
- **验收**：`testing.md` TC-SEC-007/TC-SEC-011；`test_core.py::test_verify_email`（部分）
- **关联**：`security.md` 6.2

### REQ-TOKEN-004 邮箱/密码变化使旧令牌失效

- **前置**：令牌已签发
- **输入**：邮箱或密码发生变化后的旧令牌
- **行为**：邮箱哈希/密码哈希不匹配 → 拒绝；重置/改邮箱令牌一次性；邮箱验证重复使用返回 `already_verified`
- **输出/副作用**：旧令牌不可用
- **错误**：`InvalidTokenError`
- **不变量**：旧令牌不能在新凭据状态下执行动作
- **验收**：`testing.md` TC-SEC-009/TC-SEC-010；`test_core.py`（改邮箱令牌在密码变更后失效待补）
- **关联**：`security.md` 6.2

## 10. CSRF

### REQ-CSRF-001 令牌按会话生成并使用派生密钥

- **前置**：`CSRF_ENABLED=True`
- **输入**：表单/请求
- **行为**：session 中生成随机 token；用 `CSRF_SECRET_KEY` 或从 `SECRET_KEY` 派生的 CSRF 密钥签名；同一请求内 `g` 缓存
- **输出/副作用**：表单包含 `csrf_token`
- **错误**：无
- **不变量**：CSRF 密钥与主密钥/其他用途密钥隔离
- **验收**：`testing.md` TC-FORM-008/TC-FORM-011；实测入口为 `tests/unit/forms/form/test_form.py::test_csrf_token_uses_derived_key`，明确断言 CSRF 令牌由派生子密钥签名且旧主密钥解密抛 `BadSignature`。
- **关联**：`security.md` 7.1；`spec.md` 4.4

### REQ-CSRF-002 缺失/无效/过期令牌被拒绝

- **前置**：`CSRF_ENABLED=True`
- **输入**：缺失/篡改/过期/不匹配 token
- **行为**：分别返回缺失、无效、过期、不匹配错误；不执行写操作
- **输出/副作用**：表单校验失败
- **错误**：`ValidationError`
- **不变量**：无有效 token 的写请求不能成功
- **验收**：`testing.md` TC-FORM-010；实测入口为 `tests/unit/forms/form/test_form.py::test_csrf_form`（断言无 token 时 `validate() is False`，带有效 token 时通过）；HTTP 路由级篡改/过期用例待补。
- **关联**：`security.md` 7.1

### REQ-CSRF-003 默认开启，显式配置才关闭

- **前置**：无
- **输入**：`CSRF_ENABLED`
- **行为**：默认 `True`；只有显式 `False` 才禁用；禁用时不生成/不校验 token
- **输出/副作用**：表单字段存在/不存在
- **错误**：无
- **不变量**：生产默认不能静默关闭
- **验收**：`testing.md` TC-FORM-009；实测入口为 `tests/unit/forms/form/test_form.py::test_nocsrf_form`，断言 `CSRF_ENABLED=False` 时表单不包含 `csrf_token` 字段且校验通过。
- **关联**：`security.md` 7.2

## 11. Admin / View

### REQ-ADMIN-001 列表分页

- **前置**：已授权访问 ModelView
- **输入**：`page`、`page_size`
- **行为**：`page` 从 0 开始；`page_size` 必须在白名单内，否则回退默认；返回当前页数据与总数
- **输出/副作用**：列表模板渲染
- **错误**：非法参数回退默认
- **不变量**：分页不能越界导致 500；总数与页数一致
- **验收**：`testing.md` TC-ADMIN-002～TC-ADMIN-004；`test_pagination.py`
- **关联**：`spec.md` 10.12

### REQ-ADMIN-002 搜索

- **前置**：`column_searchable_list` 配置
- **输入**：`search`
- **行为**：在配置列/关联列搜索；`=` 精确、`^` 前缀、`$` 后缀、否则包含；多词 AND、列间 OR
- **输出/副作用**：过滤后的列表与总数
- **错误**：无
- **不变量**：搜索不改变未匹配记录
- **验收**：`testing.md` TC-ADMIN-007/TC-ADMIN-008；`test_search.py`
- **关联**：`spec.md` 10.7.6

### REQ-ADMIN-003 筛选

- **前置**：`column_filters` 配置
- **输入**：`flt*` 参数
- **行为**：按列类型生成操作符；支持关联列；保留 active filters
- **输出/副作用**：过滤后的列表
- **错误**：非法值按过滤器 clean 处理
- **不变量**：筛选不会绕过授权
- **验收**：`testing.md` TC-ADMIN-009/TC-ADMIN-010；`test_views.py`/`test_search.py`
- **关联**：`spec.md` 10.7.4

### REQ-ADMIN-004 排序

- **前置**：`column_sortable_list` / `column_default_sort`
- **输入**：`sort`（列索引）、`desc`
- **行为**：按指定列排序；支持多列；无参数时使用默认排序
- **输出/副作用**：有序列表
- **错误**：非法索引回退默认
- **不变量**：排序不改变结果集
- **验收**：`testing.md` TC-ADMIN-005/TC-ADMIN-006；`test_sorting.py`
- **关联**：`spec.md` 10.7.5

### REQ-ADMIN-005 一对多搜索/筛选的计数正确

- **前置**：根模型与子模型是一对多关系；搜索/筛选涉及子表
- **输入**：搜索/筛选请求
- **行为**：分页总数必须等于**去重后的根记录数**，不能按 JOIN 行数计数
- **输出/副作用**：`count` 与根记录数一致
- **错误**：无
- **不变量**：计数不随子记录数量放大
- **implementation**：`in-progress`（`build_count()` 应用 JOIN 未对根模型去重，一对多关联搜索/筛选时计数虚高）
- **verification**：`failed`（HEAD `171b40968f309c04ae3ad423696227c2767b0055` 源码证实未去重；问题关联 C2）
- **本轮实现观察**：静态源码确认计数逻辑应用了连接表但未生成 `distinct`；需补一对多关联查询的计数回归测试。
- **验收**：`testing.md` TC-ADMIN-031（待补）；关联 `spec.md` 第 10.16 节 C2
- **关联**：`spec.md` 第 10.16 节 C2 与第 12.5.2 节（HEAD 静态核对，未专项测试）

### REQ-ADMIN-006 CRUD 与最终数据库状态

- **前置**：已授权；`can_create/edit/delete` 允许
- **输入**：创建/编辑/删除表单
- **行为**：创建/更新/删除记录；成功 flash；失败回滚；删除仅 POST
- **输出/副作用**：数据库最终状态符合提交
- **错误**：校验失败/数据库错误返回错误提示
- **不变量**：失败不留下部分写入
- **验收**：`testing.md` TC-ADMIN-011/TC-ADMIN-017；`test_views.py`/`test_actions.py`
- **关联**：`spec.md` 10.13

### REQ-ADMIN-007 Inline 父子记录

- **前置**：父模型与子模型存在关系；`inline_models` 配置
- **输入**：父表单 + Inline 子表单
- **行为**：支持一对多/一对一/多对多；保存父记录后处理子记录新增/修改/删除；失败抛 `InlineModelError`
- **输出/副作用**：父子记录最终状态正确
- **错误**：关系找不到/子表单无效时拒绝
- **不变量**：子记录必须属于该父记录
- **验收**：`testing.md` TC-ADMIN-018～TC-ADMIN-021；`test_inline_forms.py`/`test_inline_views.py`
- **关联**：`spec.md` 10.9 / C1（本轮 HEAD 静态核对，未专项测试）

### REQ-ADMIN-008 AJAX 外键查询与内联更新

- **前置**：`ajax_refs` 或 `column_editable_list` 配置
- **输入**：`/ajax/lookup/`、`/ajax/update/` JSON 请求
- **行为**：按 term 搜索关联记录并返回 `(id, text)`；内联更新校验 CSRF 后保存
- **输出/副作用**：JSON 响应；数据库更新
- **错误**：无权限/CSRF/校验失败拒绝
- **不变量**：不能通过 AJAX 绕过授权/CSRF
- **验收**：`testing.md` TC-ADMIN-022；`test_ajax.py`/`test_inline_ajax.py`
- **关联**：`spec.md` 10.10 / C1（本轮 HEAD 静态核对，未专项测试）

### REQ-ADMIN-009 导出

- **前置**：`can_export=True`
- **输入**：导出类型、当前搜索/筛选/排序
- **行为**：按 `column_export_list` 导出；CSV 流式；tablib 格式；`export_max_rows` 限制；不支持的格式提示并重定向
- **输出/副作用**：文件下载
- **错误**：不支持的格式/宏格式化器拒绝
- **不变量**：导出不能绕过授权；不能导出超过上限
- **验收**：`testing.md` TC-ADMIN-013～TC-ADMIN-015；`test_export.py`
- **关联**：`spec.md` 10.11

### REQ-ADMIN-010 视图级权限开关

- **前置**：`can_create`/`can_edit`/`can_delete`
- **输入**：创建/编辑/删除/内联更新请求
- **行为**：开关为 `False` 时对应路由必须拒绝（重定向或 403），包括 `/ajax/update/`
- **输出/副作用**：不执行写操作
- **错误**：拒绝
- **implementation**：`in-progress`（`ajax_update` 仅校验 `column_editable_list`，未检查视图开关 `can_edit`）
- **verification**：`failed`（HEAD `171b40968f309c04ae3ad423696227c2767b0055` 源码证实存在绕过；问题关联 V-01 / SEC-19）
- **本轮实现观察**：静态源码确认内联编辑路径缺少 `can_edit` 判断；需补当 `can_edit=False` 时 AJAX 更新返回 403 的测试。
- **验收**：待补；关联 `spec.md` 第 10.16 节 V-01、`security.md` SEC-19
- **关联**：`spec.md` 10.4.4；`V-01` / `SEC-19`（本轮 HEAD 静态核对，未专项测试）

### REQ-ADMIN-011 列表 URL 正确编码

- **前置**：搜索词/筛选值含空格、`&`、`#`、中文等
- **输入**：分页/排序/搜索/筛选参数
- **行为**：生成的列表 URL 必须正确编码并可回放
- **输出/副作用**：URL 可访问且结果一致
- **错误**：无
- **implementation**：`in-progress`（`get_list_url` 手写查询字符串未 URL 编码；且 `hasattr(self, "get_url")` 死分支永远为假）
- **verification**：`failed`（HEAD `171b40968f309c04ae3ad423696227c2767b0055` 源码证实存在编码缺陷与死分支；问题关联 C5、C6）
- **本轮实现观察**：静态源码确认特殊字符查询串未转义；需补含空格、`&`、中文的列表 URL 回放测试。
- **验收**：`testing.md` TC-ADMIN-032（待补）；关联 `spec.md` 第 10.16 节 C5/C6
- **关联**：`spec.md` 10.12；`C5` / `C6`（本轮 HEAD 静态核对，未专项测试）

### REQ-ADMIN-012 复合主键与字符串主键

- **前置**：模型有复合主键或字符串主键
- **输入**：列表/编辑/删除/导出
- **行为**：主键正确编码/解析；记录可定位与删除
- **输出/副作用**：CRUD 正常
- **错误**：不存在记录提示
- **不变量**：主键值不丢失/不串记录
- **验收**：`testing.md` TC-ADMIN-023/TC-ADMIN-024；`test_primary_keys.py`
- **关联**：`spec.md` 10.6.1

### REQ-VIEW-001 自定义页面与模板

- **前置**：自定义 `View` 或 `list_template`
- **输入**：`expose_url`、`allow_access`、`login_required`、`requires_active`
- **行为**：路由可访问；`render`/`render_string` 渲染；模板可 `extends` 内置模板并传自定义参数
- **输出/副作用**：HTML 响应
- **错误**：未授权 403/登录重定向
- **不变量**：模板覆盖不丢失列表/分页/筛选 UI
- **验收**：`demo.md` TreeView；`tests/unit/admin/test_view.py::test_view` 仅覆盖 `View` 暴露的路由与端点元数据，未断言真实模板覆盖渲染（测试缺口，待补自动化用例）。
- **关联**：`spec.md` 10.14

## 12. 追溯与状态导航

<a id="12-追溯矩阵"></a>

### 12.1 按域汇总

本表只提供领域导航；具体契约、测试映射及待核实事项以各契约的“验收”和“关联”字段为准。测试章节的存在不代表相关契约已被覆盖或通过。

| 域 | 契约入口 | 相关测试入口 |
| --- | --- | --- |
| EXT | [扩展生命周期](#3-扩展生命周期) | [扩展测试](./testing.md#71-extension-系统) |
| DATA | [数据库与查询](#4-数据库与查询) | [数据测试](./testing.md#72-datastore--query) |
| AUTH | [认证与会话](#5-认证与会话) | [安全测试](./testing.md#75-security)、[用户中心测试](./testing.md#77-usercenter) |
| AUTHZ | [授权](#6-授权) | [Admin 测试](./testing.md#73-admin)、[安全测试](./testing.md#75-security) |
| REG | [注册与邮箱验证](#7-注册与邮箱验证) | [用户中心测试](./testing.md#77-usercenter)、[安全测试](./testing.md#75-security) |
| RESET | [密码重置](#8-密码重置) | [用户中心测试](./testing.md#77-usercenter)、[安全测试](./testing.md#75-security) |
| TOKEN | [令牌](#9-令牌) | [安全测试](./testing.md#75-security) |
| CSRF | [CSRF](#10-csrf) | [表单测试](./testing.md#74-forms) |
| ADMIN | [Admin / View](#11-admin--view) | [Admin 测试](./testing.md#73-admin) |
| VIEW | [Admin / View](#11-admin--view) | [Admin 测试](./testing.md#73-admin)、[demo 示例](./demo.md) |

<a id="121a-关键-req--test-映射"></a>
<a id="121a-关键-req--tst-映射"></a>

<a id="121a-关键-req--tc-映射"></a>

### 12.1a 关键契约索引

以下只保留重点阅读导航；每条契约的测试映射、待补项及示例限定以相应条目的“验收”和“关联”字段为准，索引不代表测试覆盖或通过。

- [扩展生命周期](#3-扩展生命周期)：`REQ-EXT-003`、`REQ-EXT-004`
- [数据库与查询](#4-数据库与查询)：`REQ-DATA-001`、`REQ-DATA-002`
- [认证与会话](#5-认证与会话)：`REQ-AUTH-001`、`REQ-AUTH-003`、`REQ-AUTH-004`
- [授权](#6-授权)：`REQ-AUTHZ-005`
- [注册与邮箱验证](#7-注册与邮箱验证)：`REQ-REG-001`、`REQ-REG-006`
- [密码重置](#8-密码重置)：`REQ-RESET-001`、`REQ-RESET-002`
- [Admin / View](#11-admin--view)：`REQ-ADMIN-005`、`REQ-VIEW-001`

### 12.2 状态汇总

截至 2026-11-09，49 条契约的 `lifecycle` 和 `implementation` 均为 `unknown`，`verification` 均为 `unverified`。这些状态不代表契约无效、实现未开始、测试从未运行或没有缺口；后续以各条目和实际证据为准。

> 第 12.1a 节的关键契约索引只用于导航，不是当前实现率、通过率或覆盖率。

### 12.3 下一步补齐顺序

以下为历史快照中的建议顺序；执行前须复核当前实现、问题状态和优先级。

1. `REQ-AUTHZ-005`（inactive admin）→ 先写失败测试，修授权顺序。
2. `REQ-ADMIN-005`（一对多计数）→ 聚合/子查询修复，补 `TC-ADMIN-031`。
3. `REQ-ADMIN-010`（can_edit）→ `ajax_update` 加检查，补 `V-01` 测试。
4. `REQ-ADMIN-011`（URL 编码）→ `url_for` + `urlencode`，补 `TC-ADMIN-032`。
5. `REQ-REG-006`（邮箱格式）→ 补 `Email()`，补无效邮箱测试。
6. 补令牌过期/篡改、CSRF 过期/篡改、SMTP 证书/日志等边界测试。
