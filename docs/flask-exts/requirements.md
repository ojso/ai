# Flask-Exts 行为契约与需求目录（Requirements & Contracts）

> 本文是 Flask-Exts 的**行为契约单一事实源**：用稳定的 `REQ-*` 编号描述“系统应该怎样”，并给出前置条件、输入、行为、输出/副作用、错误、不变量与验收依据。
>
> | 项目 | 内容 |
> | --- | --- |
> | 文档版本 | v0.1 |
> | 状态 | 可用 |
> | 最后更新 | 2026-11-18 |
> | 数据快照 | 2026-11-13（发布版本 `0.4.2`；HEAD `445b03d1fe6c59cd53405c8187de968c687a2909`；内容核对基线 `171b40968f309c04ae3ad423696227c2767b0055`）；2026-11-16 提交 `134929564791b2d5bc843685650ee8ccd13d1bc6` 已按本轮代码审查修复同步契约：JWT 解码强制 `iat`、令牌未知 serializer 默认 30 分钟、负 `page`/`offset` 夹到 0、列表页码链接修复、用户与锁定时间统一 UTC；全量实跑 330 passed，尚未发布。2026-11-17 工作树以 `View.login_required_functions` 取代 `flask_exts.admin.login_required`，受限方法对匿名请求返回 403；全量实跑 338 passed。2026-11-18 登录门抽到 `Authorizer.check_view_access()`，补齐 RBAC 授权器共用门与 requirement 全量用例后全量实跑 389 passed。2026-11-18 新增并批准 `REQ-AUTHZ-007`～`REQ-AUTHZ-009`，记录 RBAC requirement 模型、视图声明与授权器选择；同日按用户要求在共用登录门 `Authorizer.check_view_access()` 为 active `admin` 增加超级权限，全量实跑 394 passed；2026-11-18 发布 `0.5.0`（HEAD `ca9f325fa2d43f53eaf14ca71a77ee75b1471406`，本地标签未推送），全量实跑 **393 passed**（此前 394 未复现，以 393 为准） |
> | 适用仓库 | `flask-exts` |
>
> **使用规则**：
>
> - 测试从本文的 `REQ-*` 推导，而不是从实现反推。
> - 适用契约应有可追溯的验收证据；无测试时按第 2 节区分测试缺口与已证实的实现缺口，不得仅凭缺少测试认定代码不满足契约。
> - 本文描述“应该怎样”；`spec.md` 描述“为什么这样设计/当前怎么实现”；两者冲突时按本文第 2.5 节处理。
> - 安全边界、威胁模型和运营检查仍以 `security.md` 为准；本文只登记可验证的安全行为契约。

## 契约进度

派生数据，由 `check_docs.py` 只读核验；判定标准、`passed` 的证明范围与免责见第 2.2 节。

- **契约总数**：58 条（活跃 56 条）
- **已批准且验证通过（approved + passed）**：40 条
- **未取证（默认 unknown / unverified）**：16 条
- **已停用（superseded / deprecated）**：2 条

## 0. 快速使用

### 0.1 写测试时

1. 找到要验证的 `REQ-*`。
2. 阅读“行为 / 输出 / 错误 / 不变量”。
3. 在本契约的“验收”字段维护用例 ID 与实际测试入口；`testing.md` 维护相应用例设计。测试或路径尚未核实时标“待补”或“待确认”。

> **不在测试代码中标注 `REQ-*`。** 追溯关系的唯一入口是契约“验收”字段。按 HEAD `445b03d1fe6c59cd53405c8187de968c687a2909` 核验，`tests/` 下 `REQ-` 命中 0 处、`TC-` 仅 1 处注释；代码内编号不构成覆盖或执行证据，理由见 `AGENTS.md` 第 5.3 节。

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

### 1.2 契约的定位方式

契约按领域分布在第 3–11 章；`REQ-<领域>-<序号>` 的前缀即领域（词表见 [`glossary.md` 第 1.1 节](./glossary.md#11-契约与测试编号的领域词表)），领域到章节是一一对应关系。各条目的编号与标题直接体现在文档大纲中，本文不再维护重复的条目清单；数量与状态见头部“契约进度”，未取证清单见第 12 章。

### 1.3 条目模板

每条契约需包含下文所列信息。状态字段默认值为 `lifecycle=unknown`、`implementation=unknown`、`verification=unverified`；条目可省略默认状态，非默认状态必须显式记录。

- `lifecycle`：契约的生命周期；取值见第 2.1 节
- `implementation`：实现完成程度；取值见第 2.1 节
- `verification`：对指定版本和范围的验收结果；取值见第 2.1 节
- **前置**：触发行为前必须成立的条件
- **输入**：请求参数、表单、令牌、配置等
- **行为**：系统必须做什么
- **输出/副作用**：响应、状态码、重定向、数据库变化、邮件、session
- **错误**：必须返回的错误类型/状态/提示
- **不变量**：任何情况下都不能发生的事
- **验收**：用例 ID、实际测试入口和验证证据；未完成或未核实时说明原因
- **关联**：架构/安全/示例文档与已知问题链接；被取代时包含 `superseded-by`

字段顺序为“**状态 → 要求 → 证据**”。状态前置，是因为读者（含 AI）打开一条契约时首先要判断“这条还生效吗、批准了吗、验过了吗”；已停用条目应在阅读正文前就被识别。这与本目录 ADR 条目“状态写在首行”的约定一致。已停用契约可省略要求部分，只保留 `lifecycle`、历史与现行机制说明、`关联`。

## 2. 状态、追溯与冲突处理

### 2.1 状态定义

每条契约分别记录生命周期、实现完成程度和验收结果三个相互独立的状态；缺陷与风险放在“关联”字段，不增加状态维度。状态字段名和枚举值使用小写英文及 kebab-case。

**`lifecycle`**：契约生命周期

- `draft`：草拟中，尚未作为批准的基线
- `in-review`：已提交评审，检查完整性、可验证性和冲突
- `approved`：已由有权维护者确认并纳入适用基线。同批次批准的共同属性（批准人、日期、基线、依据）集中记录在第 2.2 节，条目内只写状态值；单独批准时在括号内注明日期与差异
- `deprecated`：不推荐用于新用途；既有版本是否仍适用须明确记录
- `superseded`：已有替代契约；通过 `superseded-by` 关联一个或多个 `REQ-*`，注明旧契约的适用和兼容范围
- `unknown`：审批或适用范围尚未确认；不代表契约无效

通常由 `draft` 经 `in-review` 到 `approved`，再按需要弃用或取代；修订有效契约时保留已批准基线，不用未批准草稿静默覆盖。已废弃或被取代的编号不复用。

**`implementation`**：实现完成程度

- `not-started`：已确认适用范围内尚未开始实现；不能仅凭缺少测试推断
- `in-progress`：已开始但尚未完成适用范围的实现，注明未完成部分；暂停工作仍属于此状态
- `implemented`：已有证据表明实现工作按计划完成，不等于验收通过或不存在缺陷
- `unknown`：未获得足够证据判断当前实现

开发任务是否正在进行由任务记录跟踪；测试未补齐不自动意味着实现尚未完成。

**`verification`**：验收结果

- `unverified`：当前版本尚无足够证据确认全部适用验收通过，不代表从未运行测试
- `passed`：指定契约修订、实现版本、环境和范围内，所有适用验收均通过并留有证据
- `failed`：有证据表明当前范围内的验收未通过；记录失败范围和结果
- `blocked`：验收因环境、权限等障碍无法完成；记录阻塞原因和已有结果，不把阻塞当作通过或抹去已知失败

`failed` 可以发生在实现完成前。测试文件或用例 ID 存在不等于执行通过；部分通过不等于整条契约 `passed`。代码、契约、依赖或环境变化可能使结果失效，应评估影响并重新验证；若不再有充分证据证明通过，按实际情况标 `unverified`、`failed` 或 `blocked`。

**问题关联与风险**：

- 在“关联”字段登记已确认的契约实现缺口：`security.md` 的 `SEC-*`、`spec.md` 第 10.16 节的 `CR-*`，或项目认可的问题跟踪记录；问题详情、处置状态和风险接受由对应问题来源维护。
- 未核实的写“待核实”；未记录缺口不等于没有缺口。已排查且没有已确认缺口时，注明排查版本、范围与日期，不能推断绝对无缺陷。未实现的规划功能不自动等同于已确认缺陷。
- 影响契约验收的缺口未解决时，不能因为风险被接受而标 `passed`；发布例外仍须按 `release.md` 的门禁和审批处理。同一问题存在多个历史编号时，按 `glossary.md` 第 1.2 节的别名规则只计主记录；`V-01` 是主记录 `SEC-19` 的已废止别名。

现有契约的审批和源码/验收证据尚未逐条核实，生命周期和实现状态标 `unknown`，验证状态标 `unverified`。这不等于契约失效或未排除风险已关闭；在维护者确认适用性前，应按既有契约和未排除风险进行影响评估，不得据此静默放行。

**记录示例**（仅演示字段，不代表实际项目状态）：

```markdown
- **lifecycle**：`approved`（批准依据、日期及契约修订）
- **implementation**：`implemented`（实现依据及代码版本）
- **verification**：`failed`（验收范围、执行时间和失败证据）
- **关联**：已登记的问题编号及其权威记录
```

此例表示契约已经批准、实现工作已完成，但验收失败；修复并通过全部适用验收后，才能按证据更新验证状态。

### 2.2 状态口径、批准记录与免责

契约总数、三态分布与批准进度在本文头部“契约进度”清单集中维护，本节不复制数字。权威口径如下：

- **计数口径**：`REQ-*` 契约条目小节计数，编号无重复；已停用条目计入总数但不计入验收统计。
- **证据来源**：全量实跑的结果、耗时与环境登记在 `testing.md` 第 10.5 节基线记录；契约条目只记录 HEAD 与日期，不复制通过数量。
- **`passed` 的含义**：仅说明“该契约验收字段所列入口在该 HEAD、该环境下执行通过”，不说明断言已覆盖契约全部行为，也不构成对新版本的保证；代码、依赖或环境变化后需重新验证，证据不足时改标 `unverified`、`failed` 或 `blocked`。
- **未取证条目的共同缺口是测试入口映射**：验收字段只给 `TC-*` 编号而无具体测试入口时，执行结果无法对应到契约，因此不得标 `passed`，也不予批准；补齐入口后由 `check_docs.py` 的仓库交叉检查接管。
- **引用完整性与覆盖充分性是两件事**：脚本仓库交叉模式能证明引用是否存在，不能证明断言是否覆盖契约，两者不可互相替代。

**批准记录**（同批次共同属性集中记录，条目内只标状态值）：

- **批准人**：维护者 d.hua
- **批准日期**：2026-11-13
- **纳入基线**：文档基线 v0.1
- **批准范围**：34 条 `verification=passed` 的契约；未取得执行证据的契约不予批准
- **批准依据**：该日全量实跑（HEAD `445b03d`，Python 3.13.5，274 passed、0 跳过）；各契约的入口与结果记录在其 `verification` 字段，实跑登记见 `testing.md` 第 10.5 节
- **单独批准**：2026-11-14，`REQ-AUTH-012`（JWT 绑定凭据状态与 TFA 完成状态）；依据为当日工作树全量实跑（HEAD `445b03d` 加未提交差异，Python 3.13.5，277 passed）；批准人 d.hua
- **单独批准**：2026-11-14，`REQ-AUTH-013`（JWT 算法、密钥与声明校验硬化）；依据为当日工作树全量实跑（HEAD `445b03d` 加未提交差异，Python 3.13.5，301 passed），实现与测试提交为 `db1b35e`、`c8b45a8`；批准人 d.hua
- **单独批准**：2026-11-14，`REQ-SEC-001`（安全 Cookie 与响应头默认值）；依据为当日工作树全量实跑（HEAD `445b03d` 加未提交差异，Python 3.13.5，311 passed）；批准人 d.hua
- **重新批准**：2026-11-16，`REQ-AUTH-013`（JWT 解码新增 `iat` 必填）；依据为提交 `134929564791b2d5bc843685650ee8ccd13d1bc6` 的全量实跑（Python 3.13.5，330 passed），基线登记见 `testing.md` 第 10.5 节 2026-11-16 行；批准人 d.hua
- **重新批准**：2026-11-16，`REQ-TOKEN-002`（未知 serializer 默认 1800 秒）；依据同上；批准人 d.hua
- **重新批准**：2026-11-17，`REQ-AUTH-010`（登录受限端点的匿名响应改为 403）；依据为 2026-11-17 工作树全量实跑（Python 3.13.5，338 passed），基线登记见 `testing.md` 第 10.5 节 2026-11-17 行；批准人 d.hua
- **重新批准**：2026-11-17，`REQ-VIEW-001`（登录要求改用 `login_required_functions`）；依据同上；批准人 d.hua
- **单独批准**：2026-11-18，`REQ-AUTHZ-007`～`REQ-AUTHZ-009`（RBAC requirement 模型、视图声明/身份数据/查询 API、授权器选择与既有规则兼容）；依据为 2026-11-18 工作树全量实跑（HEAD `1349295` 加未提交差异，Python 3.13.5，389 passed），基线登记见 `testing.md` 第 10.5 节 2026-11-18 行；批准人 d.hua

后续若出现单独批准或重新批准，应在该条目 `lifecycle` 的括号内注明日期与差异，并在本节追加一条。批准记录不得由 AI 代填。

### 2.3 追溯规则

- `REQ` → `TC`（`testing.md` 测试用例编号）→ 测试文件/函数；用例编号与历史映射见 `testing.md` 第 6.3 节。
- `REQ` → `demo.md` 场景（如果用户可见）。
- `REQ` → `spec.md` 第 10 章 / `security.md`（如果涉及领域细节）。
- 已知缺口通过“关联”字段指向对应问题记录；其中 `SEC-*` 见 `security.md` 第 11 节，`CR-*` 见 `spec.md` 第 10.16 节。

单条契约的“验收”字段是 `REQ → TC → 测试入口` 的唯一维护入口；第 12 节仅提供导航，不复制映射。新增或修改契约时，记录测试设计 ID、实际测试文件/函数和执行结果；不存在或尚未核实的项目写“待补”或“待确认”，不要虚构路径。用户可见变更按适用性关联 demo；demo 不能替代自动化断言。

判定 `passed` 时，验收记录须能追溯契约修订、代码版本或 commit（工作树有改动时记录差异）、环境、验收范围、执行时间、测试命令或人工验收方式及结果。仅有用例 ID、文件名或 `REQ` 字符串不证明断言覆盖契约，更不证明测试执行成功。无法查看源码、测试或审批记录时，按第 2.1 节标 `unknown` 或 `unverified`；不能仅凭缺少证据认定代码不满足契约。

### 2.4 当前首版范围

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

### 2.5 冲突处理

按 [`AGENTS.md` 第 3 节](./AGENTS.md#3-事实源与冲突处理)处理。契约的生命周期、实现与验证状态仍以本节前述状态定义为准；未核实事实标“待核实”。

## 3. 扩展生命周期

### REQ-EXT-001 扩展注册与名称校验

- **lifecycle**：`approved`
- **implementation**：`implemented`（HEAD `445b03d` 静态核对，行为与下列验收入口一致）
- **verification**：`passed`（2026-11-13 实跑：HEAD `445b03d1fe6c59cd53405c8187de968c687a2909`，Python 3.13.5，本契约验收入口全部通过，基线登记见 `testing.md` 第 10.5 节）
- **前置**：无
- **输入**：`Extension` 子类
- **行为**：注册扩展；名称必须唯一、非空、ASCII 合法；重复名称拒绝
- **输出/副作用**：注册表新增实例；可被 `get_extension` 查询
- **错误**：重复名称/非 `Extension`/非法名称抛 `ExtensionError`
- **不变量**：同一注册表内名称唯一；失败注册不改变已有扩展
- **验收**：`testing.md` TC-EXT-001～TC-EXT-004；`tests/unit/extension_core/test_registry.py`
- **关联**：`spec.md` 第 11.1～11.3 节

### REQ-EXT-002 依赖顺序与依赖错误

- **lifecycle**：`approved`
- **implementation**：`implemented`（HEAD `445b03d` 静态核对，行为与下列验收入口一致）
- **verification**：`passed`（2026-11-13 实跑：HEAD `445b03d1fe6c59cd53405c8187de968c687a2909`，Python 3.13.5，本契约验收入口全部通过，基线登记见 `testing.md` 第 10.5 节）
- **前置**：扩展声明 `dependencies`
- **输入**：扩展注册顺序、依赖图
- **行为**：若扩展 A 依赖扩展 B，则 B 先于 A 初始化；无依赖扩展保持注册顺序；缺失依赖/循环依赖/自依赖拒绝
- **输出/副作用**：初始化顺序稳定
- **错误**：缺失依赖抛 `ExtensionNotFoundError`；循环/自依赖抛 `ExtensionDependencyError`
- **不变量**：任何扩展都不会在依赖之前初始化
- **验收**：`testing.md` TC-EXT-005～TC-EXT-010；`tests/unit/extension_core/test_registry.py`
- **关联**：`spec.md` 第 11.2/11.5 节

### REQ-EXT-003 两阶段初始化幂等与顺序

- **lifecycle**：`approved`
- **implementation**：`implemented`（HEAD `445b03d` 静态核对，行为与下列验收入口一致）
- **verification**：`passed`（2026-11-13 实跑：HEAD `445b03d1fe6c59cd53405c8187de968c687a2909`，Python 3.13.5，本契约验收入口全部通过，基线登记见 `testing.md` 第 10.5 节）
- **前置**：扩展已注册
- **输入**：`init_app` / `post_init`
- **行为**：`init_app` 先于 `post_init`；两阶段各自幂等；`post_init` 按依赖顺序执行
- **输出/副作用**：每个扩展的 `init_app`/`post_init` 最多执行一次
- **错误**：`post_init` 前未 `init` 抛 `ExtensionInitError`
- **不变量**：重复调用不产生重复注册/重复副作用
- **验收**：`testing.md` TC-EXT-011～TC-EXT-014；`tests/unit/extension_core/test_registry.py`
- **关联**：`spec.md` 第 11.4 节

### REQ-EXT-004 关闭顺序与异常隔离

- **lifecycle**：`approved`
- **implementation**：`implemented`（`shutdown_all` 逐扩展捕获普通 `Exception`，记录 warning 后继续逆序关闭；`BaseException` 不捕获；状态清理放入 `finally`）
- **verification**：`passed`（`test_shutdown_exception_is_isolated`、`test_extension_error_is_isolated`、`test_shutdown_does_not_catch_base_exception`；执行证据见 `testing.md` 第 10.5 节 2026-11-13 行（HEAD `445b03d`））
- **前置**：扩展已初始化
- **输入**：`shutdown`
- **行为**：按初始化逆序关闭；单个扩展关闭异常不阻止其他扩展关闭
- **输出/副作用**：资源释放；产生 warning
- **错误**：单扩展异常被隔离
- **不变量**：关闭后不残留已绑定资源
- **本轮实现观察**：中间扩展抛 `ValueError`/`ExtensionError` 时，其余扩展仍按逆序关闭并产生 warning；`KeyboardInterrupt` 继续向外传播。
- **验收**：`testing.md` TC-EXT-015/TC-EXT-016；`tests/unit/extension_core/test_registry.py`
- **关联**：`spec.md` 第 11.4.3 节 CR-011（已修复）；`testing.md` TC-EXT-016 已与新契约一致

## 4. 数据库与查询

### REQ-DATA-001 单例绑定、会话与释放

- **lifecycle**：`approved`
- **implementation**：`implemented`（HEAD `445b03d` 静态核对，行为与下列验收入口一致）
- **verification**：`passed`（2026-11-13 实跑：HEAD `445b03d1fe6c59cd53405c8187de968c687a2909`，Python 3.13.5，本契约验收入口全部通过，基线登记见 `testing.md` 第 10.5 节）
- **前置**：Flask app 配置 `SQLALCHEMY_DATABASE_URI`
- **输入**：`db.init_app(app)` / `db.dispose()` / app context
- **行为**：默认导出的模块级 `db` 是一个 `SqlaDb` 实例；每个实例同一时刻绑定一个 app，绑定后 `db.session` 在 app context 内复用；未 dispose 时重复绑定抛错，dispose 后允许重新绑定；`reset_all()` 删表重建
- **输出/副作用**：engine/session 绑定到当前 app
- **错误**：缺少 URI/重复绑定抛 `RuntimeError`
- **不变量**：一个 `db` 实例同一时刻只绑定一个 app；上下文结束后 session 被移除
- **验收**：`testing.md` TC-DATA-001～TC-DATA-008；`tests/unit/datastore/sqla/test_db.py`
- **关联**：`spec.md` 第 12.3 节；`flask-exts/docs/advanced/database.rst`

### REQ-DATA-002 Query 的 JOIN、搜索、筛选与排序

- **lifecycle**：`approved`
- **implementation**：`implemented`（HEAD `445b03d` 静态核对，行为与下列验收入口一致）
- **verification**：`passed`（2026-11-13 实跑：HEAD `445b03d1fe6c59cd53405c8187de968c687a2909`，Python 3.13.5，本契约验收入口全部通过，基线登记见 `testing.md` 第 10.5 节）
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

- **lifecycle**：`approved`
- **implementation**：`implemented`（HEAD `445b03d` 静态核对，行为与下列验收入口一致）
- **verification**：`passed`（2026-11-13 实跑：HEAD `445b03d1fe6c59cd53405c8187de968c687a2909`，Python 3.13.5，本契约验收入口全部通过，基线登记见 `testing.md` 第 10.5 节）
- **前置**：用户存在、密码正确、账号可登录、CSRF 通过
- **输入**：`username`、`password`、可选 `next`
- **行为**：校验密码哈希；`is_active=False` 时拒绝登录（见 `REQ-AUTH-009`）；`tfa_enabled=False` 时调用 `login_user()`（不设置 `force`）；渲染/重定向到 `next` 或 `/user/index/`
- **输出/副作用**：session 中存在 `_user_id`；HTTP 302
- **错误**：无（失败见 `REQ-AUTH-002`）
- **不变量**：密码明文不落库、不进日志；`next` 必须经过安全重定向
- **验收**：`testing.md` TC-AUTH-003；实测入口为 `tests/integration/usercenter/test_user_view.py::TestUserView.register_and_login_user` 夹具，明确断言登录后 `session` 包含 `_user_id`。
- **关联**：`spec.md` 4.4；`security.md` 3.1

### REQ-AUTH-002 登录失败统一提示

- **lifecycle**：`approved`
- **implementation**：`implemented`（HEAD `445b03d` 静态核对，行为与下列验收入口一致）
- **verification**：`passed`（2026-11-13 实跑：HEAD `445b03d1fe6c59cd53405c8187de968c687a2909`，Python 3.13.5，本契约验收入口全部通过，基线登记见 `testing.md` 第 10.5 节）
- **前置**：无
- **输入**：不存在的用户名 / 错误密码
- **行为**：不区分“用户不存在/密码错误”；不存在用户也执行 dummy scrypt 校验；不建立 session
- **输出/副作用**：统一提示 `Invalid username or password.`
- **错误**：`InvalidCredentialsError` 被表单捕获
- **不变量**：响应不泄露用户是否存在；失败不产生 `_user_id`
- **验收**：`testing.md` TC-AUTH-004；`tests/integration/usercenter/test_user_view.py`
- **关联**：`security.md` 3.1/5.1

### REQ-AUTH-003 TFA 未完成不得建立会话

- **lifecycle**：`approved`
- **implementation**：`implemented`（HEAD `445b03d` 静态核对，行为与下列验收入口一致）
- **verification**：`passed`（2026-11-13 实跑：HEAD `445b03d1fe6c59cd53405c8187de968c687a2909`，Python 3.13.5，本契约验收入口全部通过，基线登记见 `testing.md` 第 10.5 节）
- **前置**：用户 `tfa_enabled=True`，密码正确
- **输入**：登录表单
- **行为**：只写 `pending_tfa_user_id`（及 remember 标记），**不调用** `login_user`；重定向 `/user/verify_tfa/?next=...`
- **输出/副作用**：session 无 `_user_id`；有 pending 标记
- **错误**：无
- **不变量**：TFA 完成前任何登录保护页不可访问
- **验收**：`testing.md` TC-SEC-018；`test_tfa`、`test_tfa_cannot_be_bypassed_after_password_login`
- **关联**：`security.md` 8.3

### REQ-AUTH-004 TFA 验证成功完成登录

- **lifecycle**：`approved`
- **implementation**：`implemented`（HEAD `445b03d` 静态核对，行为与下列验收入口一致）
- **verification**：`passed`（2026-11-13 实跑：HEAD `445b03d1fe6c59cd53405c8187de968c687a2909`，Python 3.13.5，本契约验收入口全部通过，基线登记见 `testing.md` 第 10.5 节）
- **前置**：session 中有有效 pending user，用户仍启用 TFA
- **输入**：正确 TOTP 或恢复码
- **行为**：验证第二因子；成功后 `login_user()`（不设置 `force`）；清理 pending；设置 `tfa_verified`；重定向 `next`
- **输出/副作用**：session 中有 `_user_id` 与 `tfa_verified`；恢复码登录消耗一个恢复码
- **错误**：错误验证码不建立 session，提示 `Invalid code`
- **不变量**：第二因子失败不改变登录状态；恢复码只能使用一次；恢复码只接受哈希值，明文值必须被拒绝；禁用 TFA 或重绑 authenticator 时恢复码必须清空，旧码不得继续有效
- **验收**：`testing.md` TC-SEC-016/TC-SEC-017；`test_tfa`、`test_recovery`、`test_plaintext_recovery_codes_are_rejected`
- **关联**：`security.md` 8.3

### REQ-AUTH-005 密码变更使旧会话失效

- **lifecycle**：`approved`
- **implementation**：`implemented`（HEAD `445b03d` 静态核对，行为与下列验收入口一致）
- **verification**：`passed`（2026-11-13 实跑：HEAD `445b03d1fe6c59cd53405c8187de968c687a2909`，Python 3.13.5，本契约验收入口全部通过，基线登记见 `testing.md` 第 10.5 节）
- **前置**：用户已登录
- **输入**：旧密码、新密码、重复新密码
- **行为**：校验旧密码；保存新哈希；`get_id()` 的密码指纹变化
- **输出/副作用**：旧 session 的 `_user_id` 失效；旧密码登录失败；新密码登录成功
- **错误**：旧密码错误/两次不一致时拒绝
- **不变量**：密码变更后旧会话不能继续访问受保护页
- **验收**：`testing.md` TC-SEC-019；`test_core.py::test_password_change_invalidates_existing_login_session`、`test_change_password`
- **关联**：`security.md` 5.3；JWT 例外见 `security.md` SEC-08

### REQ-AUTH-006 登出清理认证与 TFA 状态

- **lifecycle**：`approved`
- **implementation**：`implemented`（HEAD `445b03d` 静态核对，行为与下列验收入口一致）
- **verification**：`passed`（2026-11-13 实跑：HEAD `445b03d1fe6c59cd53405c8187de968c687a2909`，Python 3.13.5，本契约验收入口全部通过，基线登记见 `testing.md` 第 10.5 节）
- **前置**：用户已登录或处于 TFA pending
- **输入**：`GET /user/logout/`
- **行为**：调用 `logout_user`；清理 `_user_id`、`tfa_verified`、`tfa_recovery`、pending TFA、rebind pending、remember 标记
- **输出/副作用**：重定向登录页；session 无认证残留
- **错误**：无
- **不变量**：登出后不能恢复半完成 TFA 登录
- **验收**：`testing.md` TC-AUTH-006；`test_tfa` 的登出断言
- **关联**：`security.md` 3.4

### REQ-AUTH-007 禁用账号的账号级功能保护（已取代）

- **lifecycle**：`superseded`（2026-11-12；`requires_active` 装饰器与授权器分支已移除）
- **superseded-by**：`REQ-AUTH-010`
- **历史行为**：`@requires_active` 在授权器层拒绝 `is_active=False` 的用户，用于保护 `allow_access=True` 视图中的账号功能。
- **现行机制**：禁用账号无法登录（`REQ-AUTH-009`），既有会话由 `user_loader` 失效（`REQ-AUTH-010`），账号功能通过在 `UserView.login_required_functions` 中列出方法名保护。
- **关联**：`security.md` 4.4

### REQ-AUTH-008 安全重定向

- **lifecycle**：`approved`
- **implementation**：`implemented`（HEAD `445b03d` 静态核对，行为与下列验收入口一致）
- **verification**：`passed`（2026-11-13 实跑：HEAD `445b03d1fe6c59cd53405c8187de968c687a2909`，Python 3.13.5，本契约验收入口全部通过，基线登记见 `testing.md` 第 10.5 节）
- **前置**：请求含 `next` / `url` 参数
- **输入**：任意重定向目标
- **行为**：只允许本地路径；拒绝绝对 URL、协议相对 URL、反斜杠、编码 `//`、畸形 URL、首字符空白
- **输出/副作用**：非法目标回退到安全默认 URL
- **错误**：不抛异常，直接使用 fallback
- **不变量**：不能重定向到外部域名
- **验收**：`testing.md` TC-SEC-020；`tests/unit/security/test_urls.py`
- **关联**：`security.md` 7.5

### REQ-AUTH-009 禁用账号不得建立登录会话

- **lifecycle**：`approved`
- **implementation**：`implemented`（HEAD `445b03d` 静态核对，行为与下列验收入口一致）
- **verification**：`passed`（2026-11-13 实跑：HEAD `445b03d1fe6c59cd53405c8187de968c687a2909`，Python 3.13.5，本契约验收入口全部通过，基线登记见 `testing.md` 第 10.5 节）
- **前置**：用户存在、密码正确、`is_active=False`；`is_active` 是管理禁用标记，与邮箱验证无关
- **输入**：登录表单；或处于 TFA pending 状态
- **行为**：登录阶段直接拒绝，不设置 `force` 绕过 Flask-Login 的 `is_active` 检查；`tfa_enabled=True` 时也不写入 `pending_tfa_user_id`；pending 用户被禁用后不能完成 TFA/恢复码登录
- **输出/副作用**：提示 `This account has been disabled. Please contact an administrator.`；session 无 `_user_id`；pending 状态被清理
- **错误**：禁用账号拒绝登录
- **不变量**：`is_active=False` 不能获得新会话；未验证邮箱（`email_verified=False`、`is_active=True`）不受影响
- **验收**：`testing.md` TC-AUTH-029/TC-AUTH-030；`tests/integration/usercenter/test_user_view.py::test_disabled_account_cannot_log_in`、`test_disabled_account_cannot_complete_pending_tfa`
- **关联**：`security.md` 3.1/3.5；`REQ-AUTH-010`

### REQ-AUTH-010 禁用账号的既有会话立即失效

- **lifecycle**：`approved`（2026-11-17 重新批准，变更范围：登录受限端点的匿名响应由登录重定向改为 403）
- **implementation**：`implemented`（HEAD `445b03d` 静态核对；2026-11-17 工作树将登录要求改为 `login_required_functions`）
- **verification**：`passed`（2026-11-17 实跑：HEAD `1349295` 加未提交工作树差异，Python 3.13.5，本契约验收入口全部通过，基线登记见 `testing.md` 第 10.5 节 2026-11-17 行）
- **前置**：用户已登录并持有有效会话，随后被设置为 `is_active=False`
- **输入**：携带旧会话 Cookie 的任意请求
- **行为**：`user_loader` 返回 `None`，清除 session 中的 `_user_id`，并标记清除 remember-me Cookie
- **输出/副作用**：`current_user` 变为匿名；受 `login_required_functions` 保护的页面返回 403（不再重定向登录）；重新启用账号后旧 Cookie 仍然无效，必须重新登录
- **错误**：不抛异常；旧会话按匿名处理
- **不变量**：禁用在下一次请求即生效，不依赖任何视图级装饰器
- **验收**：`testing.md` TC-AUTH-020；`tests/integration/usercenter/test_user_view.py::test_disabling_account_invalidates_existing_session`
- **关联**：`security.md` 3.2/3.5；`REQ-AUTH-009`

### REQ-AUTH-011 连续失败登录触发账号锁定

- **lifecycle**：`approved`
- **implementation**：`implemented`（HEAD `445b03d` 静态核对，行为与下列验收入口一致）
- **verification**：`passed`（2026-11-16 实跑：提交 `134929564791b2d5bc843685650ee8ccd13d1bc6`，Python 3.13.5，本契约验收入口全部通过，基线登记见 `testing.md` 第 10.5 节 2026-11-16 行）
- **前置**：用户存在；失败可来自密码错误或第二因子验证码错误
- **输入**：登录表单、`/user/verify_tfa/`、`/user/recovery/`
- **行为**：每次失败在同一用户行上累加 `failed_login_count`；达到 `USER_LOGIN_MAX_FAILURES`（默认 5）后设置 `locked_until`，延迟从 `USER_LOGIN_LOCKOUT_BASE_SECONDS`（默认 60 秒）起按 2 的幂增长，上限 `USER_LOGIN_LOCKOUT_MAX_SECONDS`（默认 3600 秒）；锁定期间不做密码校验，直接拒绝；只有完整登录成功或成功重置密码才清零；`locked_until` 及用户模型时间列使用 UTC 计算与存储
- **输出/副作用**：登录页提示 `Too many failed sign-in attempts. Try again in ...`；pending TFA 状态被清理；锁定不修改 `is_active`
- **错误**：`AccountLockedError`（`field="username"`，带 `retry_after` 秒数）；锁定参数非法时抛 `ValueError`
- **不变量**：按账号而非按 IP 计数；共享同一数据库的多进程/多实例结果一致；自动过期，不需要管理员解锁；锁定期内密码正确也拒绝；锁定截止时间比较在 UTC 下进行，不因进程本地时区不同而漂移；无时区数据库存 UTC wall time，历史 naive 值按 UTC 解释；自定义 `UserStore` 必须声明并实现 `login_user_by_username_password`、`is_locked`、`record_login_failure`、`clear_login_failures`，缺失时无法实例化
- **验收**：`testing.md` TC-AUTH-031~TC-AUTH-033；`tests/integration/userstore/test_sqla_userstore.py`、`tests/integration/userstore/test_sqla_userstore.py::test_model_timestamps_are_timezone_aware_utc`、`tests/integration/usercenter/test_user_view.py::test_repeated_failed_logins_lock_the_account`、`test_failed_tfa_codes_lock_the_account`、`test_password_reset_clears_lockout`
- **关联**：`security.md` 8.5/11（SEC-03）；`REQ-AUTH-009`

### REQ-AUTH-012 JWT 绑定凭据状态与 TFA 完成状态

- **lifecycle**：`approved`（2026-11-14 单独批准，范围仅本条）
- **implementation**：`implemented`（2026-11-14 工作树：`jwt_encode_for_user` 写入 `pwd`/`amr`，`load_user_from_request` 校验；UserCenter 不新增 HTTP 签发端点）
- **verification**：`passed`（2026-11-14 实跑：HEAD `445b03d1fe6c59cd53405c8187de968c687a2909` 加未提交工作树差异，Python 3.13.5，本契约验收入口全部通过，基线登记见 `testing.md` 第 10.5 节 2026-11-14 单独批准行）
- **前置**：调用方已确认用户身份；如用户启用 TFA，调用方已确认第二因子完成
- **输入**：`jwt_encode_for_user(user, amr=None, delta=None)`
- **行为**：生成 `token_use="access"` 的 JWT，载荷含 `id`、`pwd`（当前密码哈希的带密钥指纹）、`amr`（至少 `pwd`；完成 TOTP 或恢复码后含 `otp`）；TFA 用户缺少 `otp` 时拒绝签发；`load_user_from_request` 恒定时间比对 `pwd`，并在 `tfa_enabled=True` 时要求 `amr` 含 `otp`
- **输出/副作用**：返回签名后的 JWT 字符串；由使用方在自己的 API 登录流程决定如何响应
- **错误**：TFA 用户未提供 `otp` 时抛 `ValueError`；载荷缺少或伪造 `pwd`、TFA 用户缺少 `otp` 时 Bearer 认证按匿名处理
- **不变量**：不含 `pwd` 的旧 token 一律拒绝（不提供过渡兼容）；密码变更或重置后旧 token 失效；改邮箱不改变密码指纹
- **验收**：`tests/integration/builtin_extensions/test_login.py::test_bearer_token_without_password_fingerprint_is_rejected`、`test_bearer_token_is_rejected_after_password_change`、`test_tfa_user_requires_otp_claim`；执行证据见 `testing.md` 第 10.5 节 2026-11-14 单独批准行
- **关联**：`security.md` 9.1～9.3、SEC-02、SEC-08；`REQ-AUTH-005`

### REQ-AUTH-013 JWT 算法、密钥与声明校验硬化

- **lifecycle**：`approved`（2026-11-16 重新批准，变更范围：JWT 解码新增 `iat` 必填；此前 2026-11-14 单独批准，范围仅本条）
- **implementation**：`implemented`（2026-11-14 提交 `db1b35e`：算法白名单、密钥校验、`iat`/`JWT_LEEWAY`、Bearer 大小写、`id`/`amr` 严格解析；2026-11-16 提交 `1349295` 补充解码强制要求 `iat`）
- **verification**：`passed`（2026-11-16 实跑：提交 `134929564791b2d5bc843685650ee8ccd13d1bc6`，Python 3.13.5，本契约验收入口全部通过，基线登记见 `testing.md` 第 10.5 节 2026-11-16 行）
- **前置**：应用配置 JWT 功能
- **输入**：`jwt_encode` / `jwt_decode` / `jwt_encode_for_user` 的载荷、密钥、算法、`JWT_LEEWAY` 与 `Authorization` 头
- **行为**：签发与解码只接受 `HS256`/`HS384`/`HS512`；首次使用校验 `JWT_SECRET_KEY` 已设置、至少 32 字节且不同于 `SECRET_KEY`；编码写入 `iat`/`exp`/`token_use`，解码要求 `exp`/`iat`/`token_use` 并按 `JWT_LEEWAY` 容忍时钟偏差；Bearer scheme 大小写不敏感；`id` 只接受整数或纯十进制字符串；`amr` 接受字符串或字符串可迭代对象，字符串视为单个方法
- **输出/副作用**：合规令牌正常签发与解析；不合规配置或输入在首次使用时失败
- **错误**：算法或密钥不合规抛 `RuntimeError`；`amr` 类型错误抛 `TypeError`；畸形头与解码失败抛 `InvalidAuthorizationError`；缺少 `exp`/`iat`/`token_use` 的令牌被拒绝；无效 `id` 或 `pwd` 不匹配按匿名处理
- **不变量**：`none` 永不被接受；算法与密钥校验失败不签发令牌；`amr="otp"` 不会被拆成单个字符；`id=True` 与 `id=1.9` 不会被解析为用户 1
- **验收**：`tests/integration/builtin_extensions/test_login.py::test_unsupported_jwt_algorithm_is_rejected`、`test_unsupported_configured_jwt_algorithm_is_rejected`、`test_jwt_requires_secret_key`、`test_jwt_rejects_short_secret_key`、`test_jwt_rejects_secret_key_shared_with_flask_secret`、`test_jwt_encode_records_issued_at`、`test_jwt_decode_requires_issued_at`、`test_jwt_decode_honours_configured_leeway`、`test_jwt_encode_for_user_accepts_amr_string`、`test_jwt_encode_for_user_rejects_invalid_amr`、`test_bearer_token_rejects_non_integer_user_id`、`test_bearer_scheme_is_case_insensitive`；执行证据见 `testing.md` 第 10.5 节 2026-11-16 行
- **关联**：`security.md` 9.1～9.3、10.2；`REQ-AUTH-012`

## 6. 授权

### REQ-AUTHZ-001 admin 角色允许访问 Admin

- **lifecycle**：`approved`
- **implementation**：`implemented`（HEAD `445b03d` 静态核对，行为与下列验收入口一致）
- **verification**：`passed`（2026-11-13 实跑：HEAD `445b03d1fe6c59cd53405c8187de968c687a2909`，Python 3.13.5，本契约验收入口全部通过，基线登记见 `testing.md` 第 10.5 节）
- **前置**：用户有 `admin` 角色
- **输入**：访问 Admin 视图
- **行为**：`SimpleAuthorizer` 放行
- **输出/副作用**：视图可渲染
- **错误**：无
- **不变量**：非 admin 用户默认拒绝
- **验收**：`testing.md` TC-SEC-012；`tests/unit/security/test_simple_authorizer.py::test_allow_admin_user`
- **关联**：`security.md` 4.2

### REQ-AUTHZ-002 默认拒绝与匿名访问

- **前置**：无认证或用户无角色
- **输入**：访问普通 Admin/ModelView
- **行为**：匿名访问非公开视图返回 403（先要求登录）；`allow_access=True` 时，`login_required_functions` 中的方法对匿名请求同样返回 403，未列出的方法放行；已登录且 `is_active=True` 且 `get_roles()` 含 `admin` 的用户在 `check_view_access()` 直接放行，不进入后续 requirement；无角色普通用户拒绝
- **输出/副作用**：403
- **错误**：默认拒绝
- **不变量**：未授权用户不能访问 Admin 模型数据
- **验收**：`testing.md` TC-ADMIN-025/TC-ADMIN-026、TC-SEC-013；`tests/unit/security/test_simple_authorizer.py::test_non_public_view_requires_authentication`、`tests/unit/security/test_rbac_authorizer.py::test_non_public_view_requires_authentication`、`tests/unit/security/test_simple_authorizer.py::test_view_less_check_falls_back_to_roles`、`tests/unit/security/test_authorizer.py::test_admin_role_passes_the_shared_gate`、`test_inactive_admin_does_not_use_the_superuser_shortcut`、`tests/integration/usercenter/test_user_view.py::test_login_required_functions_deny_anonymous_before_allow_access`
- **关联**：`security.md` 4.2/4.5

### REQ-AUTHZ-003 allow_access 公开视图

- **前置**：视图设置 `allow_access=True`
- **输入**：匿名/已登录请求
- **行为**：未列入 `login_required_functions` 的方法允许匿名访问；不再要求 admin 角色；禁用账号已在登录/会话阶段被拒绝（`REQ-AUTH-009`、`REQ-AUTH-010`）。例外：`login_required_functions` 中列出的方法对匿名请求仍拒绝（403）
- **输出/副作用**：公开页面可访问；登录受限方法返回 403
- **错误**：登录受限方法对匿名请求返回 403
- **不变量**：公开视图不能泄露受保护数据
- **验收**：`testing.md` TC-SEC-014；`tests/unit/security/test_simple_authorizer.py::test_view_allow_access_precedes_authentication_gates`、`test_login_required_function_denies_anonymous_despite_allow_access`、`test_login_required_function_allows_authenticated_user`、`tests/unit/security/test_authorizer.py::test_public_view_allows_anonymous_unlisted_method`、`tests/unit/security/test_rbac_authorizer.py::test_allow_access_precedes_everything`、`test_login_required_functions_deny_anonymous_before_requirements`、`test_public_view_allows_anonymous_unlisted_method`
- **关联**：`security.md` 4.2

### REQ-AUTHZ-004 requires_active 保护账号功能（已废弃）

- **lifecycle**：`deprecated`（2026-11-12；装饰器与授权器分支已移除，无替代契约）
- **历史行为**：`@requires_active` 标记 `allow_access=True` 视图中的账号功能，拒绝 `is_active=False` 的用户。
- **现行机制**：禁用账号在登录与 `user_loader` 阶段即被拒绝（`REQ-AUTH-009`、`REQ-AUTH-010`），账号功能通过 `login_required_functions` 声明。
- **关联**：`security.md` 4.4

### REQ-AUTHZ-005 禁用 admin 必须失去 Admin 权限

- **lifecycle**：`approved`
- **implementation**：`implemented`（`check_view_access()` 的 admin 捷径要求 `is_active=True`；`SimpleAuthorizer` 与 `RBACAuthorizer` 在角色或 requirement 判定前执行 `is_active` 检查）
- **verification**：`passed`（2026-11-18 实跑：HEAD `1349295` 加未提交工作树差异，`tests/unit/security/test_simple_authorizer.py::test_deny_inactive_admin_user` 与 `tests/integration/admin/test_admin.py::test_inactive_admin_is_denied` 均通过；基线登记见 `testing.md` 第 10.5 节 2026-11-18（admin 登录门超级权限）行）
- **前置**：用户有 `admin` 角色且 `is_active=False`
- **输入**：访问 Admin/账号功能
- **行为**：**必须拒绝**；禁用账号不能继续使用高权限
- **输出/副作用**：403/拒绝
- **错误**：拒绝
- **不变量**：`is_active=False` 必须覆盖 `admin` 角色
- **本轮实现观察**：`admin + is_active=False` 访问 Admin 视图返回 403；active admin 仍可访问；公开 `allow_access` 视图行为不变。
- **验收**：`testing.md` TC-SEC-022；`tests/unit/security/test_simple_authorizer.py::test_deny_inactive_admin_user`、`tests/integration/admin/test_admin.py::test_inactive_admin_is_denied`
- **关联**：`security.md` 4.3；`spec.md` 第 7 章；`SEC-01`（已在 0.4.2 修复）

### REQ-AUTHZ-006 role_need 回退

- **前置**：用户已登录；可选传入 `role_need`
- **输入**：`role_need` 或 `admin` 角色
- **行为**：`role_need` 匹配放行；`admin` 角色直接放行；inactive 用户一律拒绝（包括 `admin`）
- **输出/副作用**：允许/拒绝
- **错误**：无匹配时拒绝
- **不变量**：inactive 用户不能靠 `role_need` 绕过 active 检查
- **验收**：`testing.md` TC-SEC-013；`tests/unit/security/test_simple_authorizer.py::test_authorize_without_view_uses_permission_context`、`test_view_less_check_falls_back_to_roles`、`tests/unit/security/test_rbac_authorizer.py::test_missing_view_falls_back_to_admin_only`、`tests/unit/security/test_authorizer`
- **关联**：`security.md` 4.2

### REQ-AUTHZ-007 RBAC requirement 组合判定

- **lifecycle**：`approved`（2026-11-18 单独批准，RBAC 能力）
- **implementation**：`implemented`（`RBACAuthorizer` 与 requirement 类型在工作树中实现）
- **verification**：`passed`（2026-11-18 实跑：HEAD `1349295` 加未提交工作树差异，本契约验收入口全部通过，基线登记见 `testing.md` 第 10.5 节 2026-11-18（admin 登录门超级权限）行）
- **前置**：已选择 `RBACAuthorizer`；`BuildContext` 已加载用户的 roles/permissions
- **输入**：`Role`、`Permission`、`Predicate`、`All`、`Any`、`Not`、`Authenticated` 或其组合
- **行为**：`Role` 默认任一角色匹配，`match="all"` 时要求全部；`Permission` 默认全部权限匹配，`match="any"` 时任一即可；`Predicate` 调用传入 callable 并以其返回值判定；`All`/`Any`/`Not` 分别执行全部、任一、全否组合；`&`/`|` 等价于 `All`/`Any`；`Authenticated` 要求 `is_authenticated` 为真
- **输出/副作用**：requirement 的 `check()` 返回 `bool`；只读取上下文，不修改 roles/permissions
- **错误**：`Role()`/`Permission()` 无参数、未知 `match` 抛 `ValueError`；`Predicate` 收到非 callable 抛 `TypeError`
- **不变量**：requirement 不能绕过登录门或 `is_active` 检查；空集合按失败处理
- **验收**：`testing.md` TC-SEC-023；`tests/unit/security/test_rbac_authorizer.py::test_single_role`、`test_all_match_requires_every_role`、`test_all_match_is_the_default`、`test_any_match`、`test_receives_kwargs_and_pstore`、`test_operators_build_composites`、`test_authenticated`、`test_empty_role_set_is_rejected`、`test_non_callable_is_rejected`
- **关联**：`security.md` 4.6.1

### REQ-AUTHZ-008 RBAC 视图声明、身份数据与查询 API

- **lifecycle**：`approved`（2026-11-18 单独批准，RBAC 能力）
- **implementation**：`implemented`（视图声明解析、loader 与查询辅助方法在工作树中实现）
- **verification**：`passed`（2026-11-18 实跑：HEAD `1349295` 加未提交工作树差异，本契约验收入口全部通过，基线登记见 `testing.md` 第 10.5 节 2026-11-18（admin 登录门超级权限）行）
- **前置**：视图可声明 `permission`、`permissions`、`roles`
- **输入**：视图类属性、可选的 `fn`、`role_loader`/`permission_loader`/`user_data_loader`、用户对象
- **行为**：按 `permissions[fn.__name__]` → `permission` → `roles` 的顺序解析；字符串声明等价于 `Role`；身份数据按 `user_data_loader` → 独立 loader → `get_roles()`/`get_permissions()` 的顺序加载；`can`、`has_role`、`has_permission`、`build_context` 提供查询能力
- **输出/副作用**：命中的 requirement 返回 `bool`；loader 与用户 getter 只被读取
- **错误**：不支持的声明类型抛 `TypeError`；没有 getter 且没有 loader 时 roles/permissions 为空集合并拒绝
- **不变量**：方法级声明优先于视图级声明；loader 返回值不来自不可信请求数据；查询辅助方法不替代路由登录门与 `is_active` 检查
- **验收**：`testing.md` TC-SEC-024；`tests/unit/security/test_rbac_authorizer.py::test_permission_attribute`、`test_function_entry_overrides_view_default`、`test_string_shorthand_means_role`、`test_unsupported_declaration_is_rejected`、`test_role_and_permission_loaders_are_used`、`test_user_data_loader_takes_precedence`、`test_user_without_getters_has_nothing`、`test_can_with_multiple_requirements`、`test_has_role_and_permission`
- **关联**：`security.md` 4.6.2/4.6.3

### REQ-AUTHZ-009 RBAC 授权器选择与既有规则兼容

- **lifecycle**：`approved`（2026-11-18 单独批准，RBAC 能力）
- **implementation**：`implemented`（`Registry` 选择逻辑与 `RBACAuthorizer.allow()` 在工作树中实现）
- **verification**：`passed`（2026-11-18 实跑：HEAD `1349295` 加未提交工作树差异，本契约验收入口全部通过，基线登记见 `testing.md` 第 10.5 节 2026-11-18（admin 登录门超级权限）行）
- **前置**：应用初始化安全扩展
- **输入**：`SECURITY_AUTHORIZER` 配置、视图 `allow_access` 与 requirement、用户登录/激活状态
- **行为**：配置 `"simple"` 或未配置时使用 `SimpleAuthorizer`，配置 `"rbac"` 时使用 `RBACAuthorizer`；RBAC 先执行共用登录门，公开视图直接放行，非公开视图拒绝匿名与 inactive 用户，随后执行 requirement；未声明 requirement 或 `view` 为空时回退 `allow_by_roles()`
- **输出/副作用**：允许时返回 `True`，拒绝时返回 `False`（视图默认 403）
- **错误**：未知 `SECURITY_AUTHORIZER` 值抛 `ValueError`
- **不变量**：RBAC 不削弱 `is_active`、`login_required_functions` 或默认拒绝；公开视图不执行 requirement；`admin`/`role_need` 回退保持兼容；active `admin` 在共用登录门直接放行
- **验收**：`testing.md` TC-SEC-025；`tests/unit/security/test_rbac_authorizer.py::test_allow_access_precedes_everything`、`test_inactive_user_denied_even_when_requirement_passes`、`test_undeclared_view_falls_back_to_admin_only`、`test_missing_view_falls_back_to_admin_only`、`test_admin_role_passes_before_permission_requirements`、`test_default_is_simple_authorizer`、`test_rbac_is_selected_by_config`、`test_unknown_name_is_rejected`
- **关联**：`security.md` 4.6.4；`REQ-AUTHZ-002`/`REQ-AUTHZ-003`/`REQ-AUTHZ-005`/`REQ-AUTHZ-006`

## 7. 注册与邮箱验证

### REQ-REG-001 注册创建激活但未验证邮箱的用户

- **lifecycle**：`approved`
- **implementation**：`implemented`（HEAD `445b03d` 静态核对，行为与下列验收入口一致）
- **verification**：`passed`（2026-11-13 实跑：HEAD `445b03d1fe6c59cd53405c8187de968c687a2909`，Python 3.13.5，本契约验收入口全部通过，基线登记见 `testing.md` 第 10.5 节）
- **前置**：用户名/邮箱未被占用
- **输入**：`username`、`password`、`email`、CSRF
- **行为**：创建用户；密码哈希；`is_active=True`；`email_verified=False`；不自动登录；发送 `user_registered` 信号
- **输出/副作用**：用户落库；重定向登录；验证邮件（若配置 sender）
- **错误**：重复用户名/邮箱提示
- **不变量**：密码明文不落库；邮箱验证状态不改变 active
- **验收**：`testing.md` TC-AUTH-001；`test_register`
- **关联**：`security.md` 3.5

### REQ-REG-002 重复用户名/邮箱拒绝

- **lifecycle**：`approved`
- **implementation**：`implemented`（HEAD `445b03d` 静态核对，行为与下列验收入口一致）
- **verification**：`passed`（2026-11-13 实跑：HEAD `445b03d1fe6c59cd53405c8187de968c687a2909`，Python 3.13.5，本契约验收入口全部通过，基线登记见 `testing.md` 第 10.5 节）
- **前置**：用户名或邮箱已存在
- **输入**：注册表单
- **行为**：拒绝创建；提示重复字段；不产生新用户
- **输出/副作用**：错误提示；数据库无新记录
- **错误**：`UserAlreadyExistsError` / 表单错误
- **不变量**：用户名/邮箱唯一
- **验收**：`testing.md` TC-AUTH-002；实测入口为 `tests/integration/usercenter/test_user_view.py::TestUserView.test_register_rejects_duplicate_email`（断言 `Email already exists.`）；注册时用户名重复路径当前缺少自动化用例（测试缺口，待补）。
- **关联**：`security.md` 5.2

### REQ-REG-003 邮箱验证令牌

- **lifecycle**：`approved`
- **implementation**：`implemented`（HEAD `445b03d` 静态核对，行为与下列验收入口一致）
- **verification**：`passed`（2026-11-13 实跑：HEAD `445b03d1fe6c59cd53405c8187de968c687a2909`，Python 3.13.5，本契约验收入口全部通过，基线登记见 `testing.md` 第 10.5 节）
- **前置**：用户有邮箱且未验证
- **输入**：验证令牌
- **行为**：校验签名/时间/邮箱哈希/密码哈希；标记 `email_verified=True`、`email_verified_at`；不修改 `is_active`；重复使用返回 `already_verified`
- **输出/副作用**：用户邮箱状态更新
- **错误**：过期/无效/用户不存在分别返回错误状态
- **不变量**：验证邮箱不改变账号 active 状态
- **验收**：`testing.md` TC-SEC-008；实测入口为 `tests/integration/security/test_core.py::TestSecurity.test_verify_email`（断言返回 `verified`、标记 `email_verified=True` 且保持 `is_active=True`，无效令牌抛 `InvalidTokenError`）；HTTP 路由级过期边界待补自动化用例。
- **关联**：`security.md` 6.3

### REQ-REG-004 重发验证邮件

- **lifecycle**：`approved`
- **implementation**：`implemented`（HEAD `445b03d` 静态核对，行为与下列验收入口一致）
- **verification**：`passed`（2026-11-13 实跑：HEAD `445b03d1fe6c59cd53405c8187de968c687a2909`，Python 3.13.5，本契约验收入口全部通过，基线登记见 `testing.md` 第 10.5 节）
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

- **lifecycle**：`approved`
- **implementation**：`implemented`（HEAD `445b03d` 静态核对，行为与下列验收入口一致）
- **verification**：`passed`（2026-11-13 实跑：HEAD `445b03d1fe6c59cd53405c8187de968c687a2909`，Python 3.13.5，本契约验收入口全部通过，基线登记见 `testing.md` 第 10.5 节）
- **前置**：注册表单提交
- **输入**：`email`
- **行为**：必须是合法邮箱格式；非法格式拒绝
- **输出/副作用**：表单错误
- **错误**：邮箱格式错误
- **不变量**：非法邮箱不得创建用户，也不得触发验证或重置邮件
- **实现观察**（`0.4.2`）：`RegisterForm.email` 使用 `DataRequired()`、`Email()` 与 `Length(max=254)`；`Email()` 通过 `email-validator` 做语法校验，不启用投递性检查
- **验收**：`tests/integration/usercenter/test_user_view.py::test_register_rejects_invalid_email`；非法邮箱返回表单错误且不创建用户；执行证据见 `testing.md` 第 10.5 节 2026-11-13 行，HEAD `445b03d`
- **关联**：`security.md` SEC-05（已修复）、`testing.md` 第 7.7 节

## 8. 密码重置

### REQ-RESET-001 找回密码不泄露邮箱是否存在

- **lifecycle**：`approved`
- **implementation**：`implemented`（HEAD `445b03d` 静态核对，行为与下列验收入口一致）
- **verification**：`passed`（2026-11-13 实跑：HEAD `445b03d1fe6c59cd53405c8187de968c687a2909`，Python 3.13.5，本契约验收入口全部通过，基线登记见 `testing.md` 第 10.5 节）
- **前置**：无（未登录）
- **输入**：邮箱
- **行为**：无论邮箱是否存在都显示同一提示；仅对存在且 `email_verified=True` 的用户发送重置令牌
- **输出/副作用**：统一提示；可能发送邮件
- **错误**：无（不暴露存在性）
- **不变量**：响应内容/时序不应明显区分邮箱是否存在（时序为尽力而为）
- **验收**：`testing.md` TC-AUTH-014；`test_forgot_password`
- **关联**：`security.md` 6.5

### REQ-RESET-002 重置令牌校验与密码更新

- **lifecycle**：`approved`
- **implementation**：`implemented`（HEAD `445b03d` 静态核对，行为与下列验收入口一致）
- **verification**：`passed`（2026-11-13 实跑：HEAD `445b03d1fe6c59cd53405c8187de968c687a2909`，Python 3.13.5，本契约验收入口全部通过，基线登记见 `testing.md` 第 10.5 节）
- **前置**：用户 `email_verified=True`
- **输入**：重置令牌、新密码、重复密码、CSRF
- **行为**：校验令牌；要求邮箱已验证；设置新密码哈希；成功后重定向登录
- **输出/副作用**：密码更新；旧密码失效
- **错误**：过期/无效/未验证/缺少密码分别拒绝
- **不变量**：未验证邮箱不能重置；令牌不可跨密码/邮箱变化复用
- **验收**：`testing.md` TC-SEC-010；实测入口为 `tests/integration/security/test_core.py::TestSecurity.test_verify_email`（插件级重置密码与二次使用抛 `InvalidTokenError`）与 `tests/integration/usercenter/test_user_view.py::TestUserView.test_forgot_password`（端到端表单提交）；HTTP 级令牌过期场景待补用例。
- **关联**：`security.md` 6.5

### REQ-RESET-003 重置后旧密码/旧令牌/旧会话失效

- **lifecycle**：`approved`
- **implementation**：`implemented`（HEAD `445b03d` 静态核对，行为与下列验收入口一致）
- **verification**：`passed`（2026-11-13 实跑：HEAD `445b03d1fe6c59cd53405c8187de968c687a2909`，Python 3.13.5，本契约验收入口全部通过，基线登记见 `testing.md` 第 10.5 节）
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

- **lifecycle**：`approved`（2026-11-16 重新批准，变更范围：未知 serializer 默认 1800 秒）
- **implementation**：`implemented`（HEAD `445b03d` 静态核对；2026-11-16 提交 `1349295` 改为显式 serializer 默认值映射，未知 serializer 回退 1800 秒）
- **verification**：`passed`（2026-11-16 实跑：提交 `134929564791b2d5bc843685650ee8ccd13d1bc6`，Python 3.13.5，本契约验收入口全部通过，基线登记见 `testing.md` 第 10.5 节 2026-11-16 行）
- **前置**：无
- **输入**：`RESET_PASSWORD_MAX_AGE` / `VERIFY_EMAIL_MAX_AGE` / `CHANGE_EMAIL_MAX_AGE`
- **行为**：重置默认 1800 秒；验证/改邮箱默认 7 天；未知 serializer 默认 1800 秒，不再静默继承 7 天；超过有效期返回 `expired`
- **输出/副作用**：过期令牌被拒绝
- **错误**：`ExpiredTokenError`
- **不变量**：过期令牌不能执行动作；未知 serializer 的有效期不得超过保守默认值
- **验收**：`testing.md` TC-SEC-006；`tests/integration/security/test_core.py::TestSecurity::test_unknown_serializer_uses_conservative_default_max_age` 覆盖未知 serializer 的默认值与配置覆盖；`tests/integration/security/test_core.py::test_serializer` 中第 51-57 行关于 `max_age=2` 的过期断言代码被注释，未形成有效自动化验收（测试缺口，待补）。
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

## 10. CSRF 与浏览器安全

### REQ-CSRF-001 令牌按会话生成并使用派生密钥

- **lifecycle**：`approved`
- **implementation**：`implemented`（HEAD `445b03d` 静态核对；2026-11-16 提交 `1349295` 将 session token 生成改为 `secrets.token_urlsafe(32)`）
- **verification**：`passed`（2026-11-16 实跑：提交 `134929564791b2d5bc843685650ee8ccd13d1bc6`，Python 3.13.5，本契约验收入口全部通过，基线登记见 `testing.md` 第 10.5 节 2026-11-16 行）
- **前置**：`CSRF_ENABLED=True`
- **输入**：表单/请求
- **行为**：session 中使用 CSPRNG 生成随机 token（`secrets.token_urlsafe(32)`）；用 `CSRF_SECRET_KEY` 或从 `SECRET_KEY` 派生的 CSRF 密钥签名；同一请求内 `g` 缓存
- **输出/副作用**：表单包含 `csrf_token`
- **错误**：无
- **不变量**：CSRF 密钥与主密钥/其他用途密钥隔离
- **验收**：`testing.md` TC-FORM-008/TC-FORM-011；实测入口为 `tests/unit/forms/form/test_form.py::test_csrf_token_uses_derived_key`，明确断言 CSRF 令牌由派生子密钥签名且旧主密钥解密抛 `BadSignature`。
- **关联**：`security.md` 7.1；`spec.md` 4.4

### REQ-CSRF-002 缺失/无效/过期令牌被拒绝

- **lifecycle**：`approved`
- **implementation**：`implemented`（HEAD `445b03d` 静态核对，行为与下列验收入口一致）
- **verification**：`passed`（2026-11-13 实跑：HEAD `445b03d1fe6c59cd53405c8187de968c687a2909`，Python 3.13.5，本契约验收入口全部通过，基线登记见 `testing.md` 第 10.5 节）
- **前置**：`CSRF_ENABLED=True`
- **输入**：缺失/篡改/过期/不匹配 token
- **行为**：分别返回缺失、无效、过期、不匹配错误；不执行写操作
- **输出/副作用**：表单校验失败
- **错误**：`ValidationError`
- **不变量**：无有效 token 的写请求不能成功
- **验收**：`testing.md` TC-FORM-010；实测入口为 `tests/unit/forms/form/test_form.py::test_csrf_form`（断言无 token 时 `validate() is False`，带有效 token 时通过）；HTTP 路由级篡改/过期用例待补。
- **关联**：`security.md` 7.1

### REQ-CSRF-003 默认开启，显式配置才关闭

- **lifecycle**：`approved`
- **implementation**：`implemented`（HEAD `445b03d` 静态核对，行为与下列验收入口一致）
- **verification**：`passed`（2026-11-13 实跑：HEAD `445b03d1fe6c59cd53405c8187de968c687a2909`，Python 3.13.5，本契约验收入口全部通过，基线登记见 `testing.md` 第 10.5 节）
- **前置**：无
- **输入**：`CSRF_ENABLED`
- **行为**：默认 `True`；只有显式 `False` 才禁用；禁用时不生成/不校验 token
- **输出/副作用**：表单字段存在/不存在
- **错误**：无
- **不变量**：生产默认不能静默关闭
- **验收**：`testing.md` TC-FORM-009；实测入口为 `tests/unit/forms/form/test_form.py::test_nocsrf_form`，断言 `CSRF_ENABLED=False` 时表单不包含 `csrf_token` 字段且校验通过。
- **关联**：`security.md` 7.2

### REQ-SEC-001 安全 Cookie 与响应头默认值

- **lifecycle**：`approved`（2026-11-14 单独批准，范围仅本条）
- **implementation**：`implemented`（2026-11-14 工作树：`SecurityExtension` 应用 Cookie 默认值、响应头与 HTTPS 校验；2026-11-15 补充默认值开关、配置类型校验与代理场景测试）
- **verification**：`passed`（2026-11-15 实跑：HEAD `445b03d1fe6c59cd53405c8187de968c687a2909` 加未提交工作树差异，Python 3.13.5，本契约验收入口全部通过，基线登记见 `testing.md` 第 10.5 节 2026-11-15 SEC-12 行）
- **前置**：应用初始化 `SecurityExtension`
- **输入**：`SECURITY_HEADERS_ENABLED`、`SECURITY_HEADERS`、`SECURITY_HSTS_ENABLED`、`SECURITY_HSTS`、`SECURITY_REQUIRE_HTTPS`、`SECURITY_COOKIE_DEFAULTS_ENABLED`；HTTP/HTTPS 请求（含受信反向代理提供的 `X-Forwarded-Proto`）；`SESSION_COOKIE_*` 与 `REMEMBER_COOKIE_*` 配置
- **行为**：默认下发 `X-Content-Type-Options`、`X-Frame-Options`、`Referrer-Policy`、`Permissions-Policy` 与最小 `Content-Security-Policy`；`SECURITY_HEADERS` 覆盖或按 `None` 移除单项；HTTPS 请求按配置追加 `Strict-Transport-Security`；`SAMESITE` 未配置时设为 `Lax`，`SECURITY_COOKIE_DEFAULTS_ENABLED=False` 时保留 Flask 原值，字符串 `"None"` 用于显式跨站 Cookie；`SECURITY_REQUIRE_HTTPS=True` 时要求两个 `*_COOKIE_SECURE` 均为 `True`；启动阶段校验 `SECURITY_HEADERS` 与 `SECURITY_HSTS` 的类型
- **输出/副作用**：响应头出现在所有响应；HTTPS 下 Cookie 可带 `Secure`；启动阶段执行配置校验
- **错误**：`SECURITY_REQUIRE_HTTPS=True` 而 Secure Cookie 未开启时抛 `RuntimeError`；`SECURITY_HEADERS` 不是 mapping、键不是非空字符串、值不是字符串或 `None`，或 `SECURITY_HSTS` 不是字符串或 `None` 时抛 `RuntimeError`
- **不变量**：库不自动强制 `*_COOKIE_SECURE`，HTTP 开发与测试仍可使用；HSTS 只对 HTTPS 请求下发，反向代理需安装 `ProxyFix`；单个响应头可被应用覆盖或移除；Cookie 默认值可整体关闭
- **验收**：`tests/integration/security/test_security_headers.py::test_security_headers_are_added_to_http_responses`、`test_hsts_is_only_added_over_https`、`test_security_headers_can_be_disabled`、`test_security_headers_can_be_overridden_or_removed`、`test_hsts_can_be_disabled`、`test_session_cookie_emits_secure_attributes_when_configured`、`test_session_cookie_stays_usable_over_http`、`test_secure_cookie_defaults_are_applied`、`test_require_https_rejects_insecure_cookies`、`test_require_https_accepts_secure_cookies`、`test_cookie_defaults_can_be_disabled`、`test_explicit_samesite_none_is_emitted`、`test_hsts_is_added_behind_a_trusted_proxy`、`test_extension_initialization_accepts_valid_config`、`test_extension_rejects_invalid_security_config`；执行证据见 `testing.md` 第 10.5 节 2026-11-15 SEC-12 行
- **关联**：`security.md` 3.3、7.4、10.2、SEC-12

## 11. Admin / View

### REQ-ADMIN-001 列表分页

- **前置**：已授权访问 ModelView
- **输入**：`page`、`page_size`
- **行为**：`page` 从 0 开始；负数 `page` 夹到 0；非整数 `page` 回退 0；`page_size` 必须在白名单内，否则回退默认；返回当前页数据与总数
- **输出/副作用**：列表模板渲染
- **错误**：非法参数回退默认
- **不变量**：分页不能越界导致 500；负数页码不产生负 offset；总数与页数一致
- **验收**：`testing.md` TC-ADMIN-002～TC-ADMIN-004；`tests/unit/admin/model/test_pagination.py::test_get_list_args_clamps_negative_page`、`tests/integration/admin/sqla/test_pagination.py`
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

- **lifecycle**：`approved`
- **implementation**：`implemented`（`build_count()` 对 JOIN、搜索、筛选后的结果执行 `count(*)`，与列表查询使用同一 `_apply()`）
- **verification**：`passed`（`test_related_search_count_matches_list_rows`；执行证据见 `testing.md` 第 10.5 节 2026-11-13 行（HEAD `445b03d`））
- **前置**：根模型与子模型是一对多关系；搜索/筛选涉及子表
- **输入**：搜索/筛选请求
- **行为**：分页总数必须等于**列表查询实际返回的行数**（包含一对多 JOIN 产生的行），用于与列表页显示行数一致
- **输出/副作用**：`count` 与列表查询返回行数一致
- **错误**：无
- **不变量**：`count == len(list rows)`；分页页数按该行数计算；不额外做根记录去重
- **本轮实现观察**：1 个 Author 关联 5 条匹配子记录时，列表返回 5 行（同一根对象重复），`count == 5`；复合主键模型计数仍正确。
- **验收**：`testing.md` TC-ADMIN-031；`tests/integration/admin/sqla/test_search.py::test_related_search_count_matches_list_rows`
- **关联**：`spec.md` 第 10.16 节 CR-002（按列表行数语义关闭）与第 12.5.2 节

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
- **关联**：`spec.md` 10.9 / CR-001（本轮 HEAD 静态核对，未专项测试）

### REQ-ADMIN-008 AJAX 外键查询与内联更新

- **前置**：`ajax_refs` 或 `column_editable_list` 配置
- **输入**：`/ajax/lookup/`、`/ajax/update/` JSON 请求
- **行为**：按 term 搜索关联记录并返回 `(id, text)`；负数 `offset` 夹到 0；内联更新校验 CSRF 后保存
- **输出/副作用**：JSON 响应；数据库更新
- **错误**：无权限/CSRF/校验失败拒绝
- **不变量**：不能通过 AJAX 绕过授权/CSRF；负数 offset 不产生数据库错误
- **验收**：`testing.md` TC-ADMIN-022；`tests/integration/admin/sqla/test_ajax.py`、`tests/integration/admin/sqla/test_inline_ajax.py`
- **关联**：`spec.md` 10.10 / CR-001（本轮 HEAD 静态核对，未专项测试）

### REQ-ADMIN-009 导出

- **前置**：`can_export=True`
- **输入**：导出类型、当前搜索/筛选/排序
- **行为**：按 `column_export_list` 导出；CSV 流式；tablib 格式；`export_max_rows` 限制；不支持的格式提示并重定向；导出值按原样写出，不做电子表格公式注入中和
- **输出/副作用**：文件下载
- **错误**：不支持的格式/宏格式化器拒绝
- **不变量**：导出不能绕过授权；不能导出超过上限；导出内容不因公式前缀（`=`、`+`、`-`、`@` 等）而改变
- **验收**：`testing.md` TC-ADMIN-013～TC-ADMIN-015；`test_export.py`
- **关联**：`spec.md` 10.11

### REQ-ADMIN-010 视图级权限开关

- **lifecycle**：`approved`
- **implementation**：`implemented`（`ajax_update` 在读取请求体前检查 `can_edit`，为 `False` 时返回 403）
- **verification**：`passed`（`test_ajax_update_requires_can_edit`；执行证据见 `testing.md` 第 10.5 节 2026-11-13 行（HEAD `445b03d`））
- **前置**：`can_create`/`can_edit`/`can_delete`
- **输入**：创建/编辑/删除/内联更新请求
- **行为**：开关为 `False` 时对应路由必须拒绝（重定向或 403），包括 `/ajax/update/`
- **输出/副作用**：不执行写操作
- **错误**：拒绝
- **不变量**：任一视图开关为 `False` 时，所有对应写路径（含 `/ajax/update/` 与 Inline）都不能执行写操作
- **本轮实现观察**：`can_edit=False` 且配置 `column_editable_list` 时，AJAX 更新返回 403，数据库记录保持不变；`column_editable_list` 为空时仍返回 404。
- **验收**：`testing.md` TC-ADMIN-040；`tests/integration/admin/sqla/test_actions.py::test_ajax_update_requires_can_edit`
- **关联**：`security.md` SEC-19（已在 0.4.2 修复；旧别名 `V-01` 已废止，见 `glossary.md` 第 1.2 节）

### REQ-ADMIN-011 列表 URL 正确编码

- **lifecycle**：`approved`
- **implementation**：`implemented`（`get_list_url` 使用 `urllib.parse.urlencode(params, doseq=True)`；移除 `hasattr(self, "get_url")` 死分支，改为 `self.view.get_url(".index_view")`；2026-11-16 提交 `1349295` 修复页码链接：`page > 0` 时保留零基页码，不再因 `page > 1` 丢弃第二页链接）
- **verification**：`passed`（`test_get_list_url_encodes_special_characters`、`test_get_list_url_omits_first_page_and_keeps_later_pages`、`test_search_url_encodes_special_characters`；执行证据见 `testing.md` 第 10.5 节 2026-11-16 行（提交 `1349295`））
- **前置**：搜索词/筛选值含空格、`&`、`#`、非 ASCII 字符等
- **输入**：分页/排序/搜索/筛选参数
- **行为**：生成的列表 URL 必须正确编码并可回放；第 0 页省略 `page`，第 1 页及以后保留零基 `page`
- **输出/副作用**：URL 可访问且结果一致
- **错误**：无
- **不变量**：列表 URL 经回放后搜索/筛选/排序结果与生成时一致，特殊字符不丢失；第 1 页链接不会丢失 `page=1`
- **本轮实现观察**：空格、`&`、非 ASCII 字符搜索词生成的列表 URL 可正确编码并回放；`sort=0` 不再被丢弃；第二页及后续页可打开请求的页码。
- **验收**：`testing.md` TC-ADMIN-032；`tests/unit/admin/model/test_pagination.py::test_get_list_url_omits_first_page_and_keeps_later_pages`、`tests/integration/admin/sqla/test_search.py`
- **关联**：`spec.md` 10.12；`CR-005` / `CR-006`（已修复）

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

- **lifecycle**：`approved`（2026-11-17 重新批准，变更范围：登录要求改用 `login_required_functions`，匿名响应为 403）
- **implementation**：`implemented`（HEAD `445b03d` 静态核对；2026-11-17 工作树改用 `login_required_functions`）
- **verification**：`passed`（2026-11-17 实跑：HEAD `1349295` 加未提交工作树差异，Python 3.13.5，本契约验收入口全部通过，基线登记见 `testing.md` 第 10.5 节 2026-11-17 行）
- **前置**：自定义 `View` 或 `list_template`
- **输入**：`expose_url`、`allow_access`、`login_required_functions`
- **行为**：路由可访问；`render`/`render_string` 渲染；模板可 `extends` 内置模板并传自定义参数
- **输出/副作用**：HTML 响应
- **错误**：未授权 403（`login_required_functions` 不再重定向登录）
- **不变量**：模板覆盖不丢失列表/分页/筛选 UI
- **验收**：`demo.md` TreeView；`tests/unit/admin/test_view.py::test_view`、`test_login_required_functions_are_kept_on_the_view`、`test_login_required_functions_must_be_exposed`、`test_login_required_functions_reject_a_bare_string`；未断言真实模板覆盖渲染（测试缺口，待补自动化用例）。
- **关联**：`spec.md` 10.14

## 12. 当前待办与测试缺口

原 0.4.1 快照中的前 5 项高优先级契约（`REQ-AUTHZ-005`、`REQ-ADMIN-005`、`REQ-ADMIN-010`、`REQ-ADMIN-011`、`REQ-REG-006`）已全部在 0.4.2 实测通过并获得维护者批准（记录见各条目及 `release.md`）。当前真正未闭环的待办项如下：

1. **测试入口补全（11 条待核实契约）**：
   `REQ-ADMIN-001`～`REQ-ADMIN-004`、`REQ-ADMIN-006`、`REQ-ADMIN-009`、`REQ-ADMIN-012`、`REQ-REG-005`、`REQ-TOKEN-001`、`REQ-TOKEN-003`、`REQ-TOKEN-004`。需在“验收”字段补齐具体测试文件与函数入口，补齐后由 `check_docs.py` 仓库交叉检查接管。
2. **`CR-001` 缺陷相关契约**：
   `REQ-ADMIN-007`、`REQ-ADMIN-008`：在修复 `create_ajax_loader` 签名不匹配后，需在 `tests/integration/admin/sqla/test_inline_ajax.py` 补充为子模型配置 `ajax_refs` 的专项用例。
3. **边界与异常路径自动化测试**：
   - 令牌过期与签名篡改测试（`REQ-TOKEN-*`）
   - CSRF 跨域提交与过期边界测试（`REQ-CSRF-*`）
   - SMTP 证书校验与缺失发信人脱敏边界（`REQ-EMAIL-*`）
4. **测试基础设施与工程门禁**：
   - 建立 `tests/e2e/` HTTP 端到端旅程测试与 `tests/performance/` 查询基准。
   - 将 `check_docs.py`（含 `FLASK_EXTS_REPO` 模式）纳入 CI 持续门禁（见 `README.md` P0-4）。
