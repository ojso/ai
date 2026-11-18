# 版本与发布说明

> 本文档用于说明当前文档集和项目的版本状态、影响范围、发布前检查以及回滚条件。
>
> | 项目 | 内容 |
> | --- | --- |
> | 文档版本 | v0.1 |
> | 状态 | 可用 |
> | 最后更新 | 2026-11-18 |
> | 数据快照 | 2026-11-18（发布版本 `0.5.0`；HEAD `ca9f325fa2d43f53eaf14ca71a77ee75b1471406`；本地标签 `v0.5.0`，未推送；全量 `393 passed`） |
> | 适用范围 | 本目录文档与工程发布评审 |
>
> 本文件是发布前门禁、兼容性策略、回滚条件与发布说明模板的唯一事实源；其他文档只引用，不复制。

## 1. 当前状态

- **文档集**
  - 版本/来源：v0.1
  - 状态：可用
  - 说明：适合设计、审查和协作基线

- **工程代码**
  - 版本/来源：版本文件 `0.5.0`；HEAD `ca9f325fa2d43f53eaf14ca71a77ee75b1471406`；本地标签 `v0.5.0`
  - 状态：已提交并本地打标签；**未推送**至 `origin`，未发布到 PyPI
  - 说明：`0.5.0` 同时包含未发布的 `0.4.3` 变更；基于该提交全量实跑 393 passed；`dist/flask_exts-0.5.0-*` 已在本地构建

- **发布执行**
  - 版本/来源：`.github/workflows/release.yml` 由 tag `v*` 触发
  - 状态：未触发
  - 说明：`origin` 无 `v0.5.0` 标签；PyPI 最新版本仍为 `0.4.2`；未推送标签前不会构建或发布

- **文档与实现关系**
  - 版本/来源：本轮已按 HEAD `ca9f325` 更新有证据支持的事实
  - 状态：部分校准
  - 说明：未核对项仍标为待核实；文档不得覆盖源码事实

### 1.1 0.4.2 闭环与退役条目记录

依据 `AGENTS.md` 第 5.7 节退役规则，以下条目已在 `0.4.2` 版本（提交 `445b03d1fe6c59cd53405c8187de968c687a2909`）完成代码修复或实测闭环，并由回归测试守护：

- **代码审查缺陷闭环**：`CR-002`（一对多计数按列表行数一致）、`CR-005`/`CR-006`（列表 URL 参数编码与死分支移除）、`CR-007`（未使用 query builders 包移除）、`CR-011`（扩展逆序关闭异常隔离）、`CR-012`（RowAction/BulkAction 规范化命名）。
- **安全风险闭环**：`SEC-01`（禁用管理员访问 Admin 返回 403）、`SEC-05`（注册邮箱合法格式校验）、`SEC-13`（恢复码仅接受哈希验证）、`SEC-16`（TFA 重绑与解绑清空旧恢复码）、`SEC-17`（SMTP 强制默认 SSL 上下文与证书校验）、`SEC-18`（发信失败告警日志脱敏敏感载荷）、`SEC-19`（只读视图阻断 AJAX 行内编辑）；`SEC-03` 账号级失败锁定与指数退避已落地（部分修复，IP 维度与未知用户名计数仍需部署层配合）。
- **优先契约闭环**：`requirements.md` 原建议顺序中的前 5 项核心契约（`REQ-AUTHZ-005`、`REQ-ADMIN-005`、`REQ-ADMIN-010`、`REQ-ADMIN-011`、`REQ-REG-006`）全部实测通过并经维护者正式批准。

> 说明：文档版本与仓库版本应区分；若不一致，必须在发布前说明差异来源。

### 1.2 0.5.0 发布内容与已知限制

发布内容：

- **新增**
  - `RBACAuthorizer`：`Role` / `Permission` / `Predicate` requirement，可由 `All` / `Any` / `Not` 组合，并通过 `SECURITY_AUTHORIZER = "rbac"` 启用。
  - `View.login_required_functions`：替代已移除的 `login_required` 装饰器，匿名访问受限方法返回 403。
  - demo 的 `UserInterest` / `InterestView`：展示“登录用户读取全部、`Predicate` 限制只编辑本人记录”。
- **变更**
  - 时间戳统一为 UTC；分页、导出、默认视图、TOTP flush 等修复。
  - `admin` 角色成为唯一内建超级用户，在共享登录门先于 requirement 放行。
- **破坏性变更**
  - 移除 `flask_exts.admin.login_required`，改用 `View.login_required_functions`。
  - 未发布的 `0.4.3` 已包含 JWT 凭据绑定、算法/密钥收紧与安全 Cookie/响应头默认值；这些变更首次随 `0.5.0` 发布。

已知限制（本版本未修复）：

- `form_excluded_columns` 在自动脚手架下被忽略。
  - 影响：依赖该选项隐藏外键或归属字段的表单仍会生成字段；用于安全隐藏时可能暴露或接受不应提交的值。
  - 规避：显式设置 `form_columns`，只列出允许编辑的字段。
- 对象级 requirement 只覆盖声明它的方法。
  - 影响：`delete_view` / `edit_view` 的 `Predicate` 不会自动保护 `action_view`（批量操作）、`ajax_update`（内联编辑）或 `ajax_inline_model` 等入口。
  - 规避：为每个写入口单独声明 requirement，或关闭对应能力（`can_delete`、`action_disallowed_list`、`column_editable_list`、`inline_models`）。

## 2. 版本维护规则

- 文档版本与代码版本不是一回事，必须分开维护。
- 文档更新时，若涉及关键行为、架构边界、安全风险或测试门禁，必须同步说明影响范围。
- 发布前，至少检查：需求、架构、安全、视图、测试、demo 是否保持一致。
- 不要把“计划”写成“已完成”。

## 3. 兼容性策略

- 公开 API 或默认配置变更必须先更新 `requirements.md`、`architecture.md` 和 `security.md`，再做实现和测试。
- 新增字段/选项不自动代表向后兼容；需验证现有调用方、配置、数据和默认行为不受影响。无法确认时标为 `待确认`；删除、重命名或改变既有语义时记录迁移策略。
- 如果某次修改会影响认证、授权、数据库结构、CSRF、JWT、TFA、Admin 权限或数据导出，必须标注为“高风险兼容性修改”。
- 兼容性问题必须在发布前给出：影响对象、替代方案、迁移方式、回滚方式。
- 若不能确认兼容性，结论必须写为 `待确认`，不能隐含“兼容性正常”。

### 3.1 运行环境与依赖兼容性矩阵

依据 `pyproject.toml` 声明与本轮在 HEAD `445b03d1fe6c59cd53405c8187de968c687a2909` 的实测数据，支持矩阵如下：

- **Python**
  - 声明范围：`>=3.11`
  - 实测验证状态：3.13.5（本地；274 passed，见 `testing.md` 第 1.1 节）
  - 生产建议与注意事项：支持 3.11 / 3.12 / 3.13；CI 运行 3.11–3.13 矩阵，3.11 验证最低支持、3.13 验证主力版本，版本策略见 ADR-005

- **Flask**
  - 声明范围：`>=3.0`
  - 实测验证状态：3.1.3（测试环境）
  - 生产建议与注意事项：遵循 Flask 3.x 蓝图与上下文规范；不向下兼容 Flask 1.x/2.x

- **WTForms**
  - 声明范围：`>=3.3.2`
  - 实测验证状态：3.3.2（测试环境）
  - 生产建议与注意事项：使用 3.3 的 choices/字段行为；下限排除 3.3.0/3.3.1 的 FieldList 缺陷；3.0–3.2 与 2.x 不在声明范围内

- **SQLAlchemy**
  - 声明范围：`>=2.1`
  - 实测验证状态：2.1.8（测试环境）
  - 生产建议与注意事项：沿用 2.0 风格的 `Mapped` 与 `select()` 语法；2.0.x 与 1.x 不在声明范围内

- **SQLite**
  - 声明范围：`>=3.35`
  - 实测验证状态：3.46.1（内置驱动）
  - 生产建议与注意事项：适合开发与轻量测试；测试外键前需显式 `PRAGMA foreign_keys=ON`

- **PostgreSQL**
  - 声明范围：`>=13`
  - 实测验证状态：未纳入自动化矩阵
  - 生产建议与注意事项：驱动推荐 `psycopg2-binary>=2.9` 或 `psycopg[binary]>=3.1`；需设置连接池与心跳

- **MySQL / MariaDB**
  - 声明范围：`>=8.0` / `>=10.5`
  - 实测验证状态：未纳入自动化矩阵
  - 生产建议与注意事项：驱动推荐 `pymysql>=1.1`；需指定 `utf8mb4` 字符集与排序规则

- **密码学依赖**
  - 声明范围：`cryptography>=46.0`
  - 实测验证状态：50.0.2（测试环境）
  - 生产建议与注意事项：用于 AES-256-GCM 加密 TOTP secret；必须支持 OpenSSL 3.x 环境

- **Web 浏览器**
  - 声明范围：现代标准浏览器
  - 实测验证状态：未建立浏览器 E2E
  - 生产建议与注意事项：后台依赖 Bootstrap 5 与现代 ES6 语法；不支持 IE11 或老旧内核

> 快照：2026-11-11。实测值来自本地单一环境；发布版本 `0.4.1`（HEAD `03006024d21167c0f6285a5724a3be5ef24d9a59`）、`0.4.2`（HEAD `445b03d1fe6c59cd53405c8187de968c687a2909`）与 `0.5.0`（HEAD `ca9f325fa2d43f53eaf14ca71a77ee75b1471406`）的 `pyproject.toml` 依赖声明一致：Python `>=3.11`、WTForms `>=3.3.2`、SQLAlchemy `>=2.1`、`cryptography>=46.0`。依赖下限变化后应重新测量；未列出的组合不能据此推断兼容。
>
> 依赖基线的决策背景、备选方案与回滚方式见 [`architecture.md` ADR-004](./architecture.md#adr-004-依赖基线提升为-python-311-wtforms-33-sqlalchemy-21)；开发/主力 Python 版本的选择与提升时机见 [`architecture.md` ADR-005](./architecture.md#adr-005-开发与主力验证-python-版本锚定-debian-stable)。

### 3.2 0.5.0 高风险兼容性修改

以下修改已进入 `0.5.0`。JWT 与安全 Cookie 部分原本计划随 `0.4.3` 发布，但 `0.4.3` 从未打标签或发布，因此首次随 `0.5.0` 生效；升级前必须完成迁移说明、回归验证与回滚评估。

- **移除 `login_required` 装饰器**
  - 影响对象：使用 `flask_exts.admin.login_required` 装饰视图方法的应用
  - 变更：该装饰器被移除；改用 `View.login_required_functions = ("method_name",)`，匿名访问受限方法返回 403，不再重定向到登录页
  - 迁移：把装饰器替换为类属性，并确认前端按 403 处理
  - 回滚：回退到 0.4.2，或恢复旧装饰器实现；不提供兼容分支

- **admin 超级用户语义**
  - 影响对象：依赖 `admin` 角色受视图 requirement 约束的部署
  - 变更：已登录且 active 的 `admin` 在共享登录门直接放行，不再评估 `permission` / `permissions` / `Predicate`
  - 迁移：需要限制管理员时，移除其 `admin` 角色或改用其他角色
  - 回滚：回退 `Authorizer.check_view_access()` 的超级用户分支

- **JWT 旧令牌不兼容**
  - 影响对象：已签发且不含 `pwd` 声明、或 TFA 用户不含 `otp` 声明的 Bearer token
  - 变更：`load_user_from_request` 要求 `pwd` 指纹，并在 `tfa_enabled=True` 时要求 `amr` 含 `otp`
  - 迁移：发布前通知使用方重新登录并重新签发 token；不提供过渡兼容
  - 回滚：回退 JWT 请求加载校验；代价是重新暴露 SEC-02/SEC-08

- **JWT 算法收窄为 HMAC 白名单**
  - 影响对象：配置 `JWT_HASH` 为 `RS256`/`RS384`/`RS512` 或其他值的部署
  - 变更：只允许 `HS256`/`HS384`/`HS512`；首次使用即抛 `RuntimeError`
  - 迁移：改用 HMAC 密钥；非对称签名支持需另行设计后发布
  - 回滚：回退算法白名单；不得恢复对 `none` 或未校验算法的接受

- **JWT 配置校验收紧**
  - 影响对象：`JWT_SECRET_KEY` 缺失、短于 32 字节或与 `SECRET_KEY` 相同的部署
  - 变更：首次使用 JWT 时抛 `RuntimeError`
  - 迁移：配置独立、至少 32 字节的随机密钥
  - 回滚：不提供放宽选项；如需回退只能回退该版本代码

- **`id` 与 `amr` 解析收紧**
  - 影响对象：使用布尔、浮点、带符号或非十进制字符串作为 `id`，或把 `amr` 当字符串传入的内部调用方
  - 变更：`id` 只接受整数或纯十进制字符串；`amr` 字符串视为单个方法，元素必须是字符串
  - 迁移：签发端改用整数 `id` 与 `amr=["otp"]`
  - 回滚：回退 `login_ext.py` 的解析逻辑

- **默认安全 Cookie 与响应头（SEC-12）**
  - 影响对象：依赖跨站 Cookie、iframe 嵌入或严格自定义响应头的应用
  - 变更：`SAMESITE` 未配置时设为 `Lax`；默认下发 `X-Frame-Options: SAMEORIGIN`、最小 CSP 等安全头；HTTPS 请求下发 HSTS；启动阶段校验响应头配置类型
  - 迁移：需要跨站或嵌入时通过 `SECURITY_HEADERS` 覆盖响应头，把 `SESSION_COOKIE_SAMESITE` 设为字符串 `"None"` 并开启 Secure；需要保留 Flask 原 Cookie 行为时设置 `SECURITY_COOKIE_DEFAULTS_ENABLED=False`；生产同时开启 `SESSION_COOKIE_SECURE`、`REMEMBER_COOKIE_SECURE` 与 `SECURITY_REQUIRE_HTTPS`；反向代理安装 `ProxyFix`
  - 回滚：设置 `SECURITY_HEADERS_ENABLED=False` 和 `SECURITY_COOKIE_DEFAULTS_ENABLED=False`；不建议回退 Secure Cookie 策略

## 4. 发布前检查清单

- [ ] 文档职责变化是否已同步更新 `README.md`
- [ ] 需求变更是否已同步 `requirements.md`
- [ ] 架构边界是否已同步 `architecture.md`
- [ ] 安全风险是否已同步 `security.md`
- [ ] 视图/后台行为是否已同步 `spec.md` 第 10 章
- [ ] 测试与 demo 是否已同步更新
- [ ] 需要时是否完成代码审查
- [ ] 是否已按 `AGENTS.md` 第 5.7 节扫描 `spec.md` 第 10.16 节与 `security.md` 第 11 节主清单，并将满足退役条件、已过观察期的条目登记到本文对应版本说明
- [ ] 是否只按 `pyproject.toml` 声明的依赖基线实现，未新增面向旧版本的兼容分支或测试级弃用告警过滤
- [ ] 关键回滚方式是否已记录
- [ ] JWT 变更是否按第 3.2 节完成升级通知：旧 token 失效、算法白名单、密钥校验与 `id`/`amr` 解析收紧
- [ ] 是否已确认 `JWT_SECRET_KEY` 独立且至少 32 字节，`JWT_HASH` 在 HMAC 白名单内
- [ ] 是否已确认生产 Cookie 开启 `Secure`、`SECURITY_REQUIRE_HTTPS=True`，并评估默认安全响应头对 iframe/CSP 的影响
- [ ] 受影响契约的 `lifecycle`、`implementation`、`verification`，以及测试入口、实际执行结果和代码基线是否可追溯
- [ ] 已确认缺口及未排除的历史风险是否已评估并按严重度处理；风险接受不等于契约已验证
- [ ] 未执行或失败的检查是否列明原因、影响与责任人，并按严重度决定阻塞或书面风险接受

未建立的 CI、未执行的 demo 或审查不等于通过；不能仅凭文档方案或 AI 自述签核。审查严重度见第 5 节，Critical 级问题绝对阻塞发布，不得通过风险接受绕过。

### 4.1 0.5.0 本轮执行结果（2026-11-18）

已执行：

- `python -m pytest -q`：393 passed
- 变更文件的 `ruff check` 与 `ruff format --check`：通过
- `python -m sphinx -b html docs docs/_build/html -W -n --keep-going`：通过
- `uv build`：生成 `dist/flask_exts-0.5.0-py3-none-any.whl` 与 `dist/flask_exts-0.5.0.tar.gz`，wheel 元数据版本为 `0.5.0`

未执行：

- 未推送 `main` 与 `v0.5.0` 标签；未触发 GitHub Actions，未发布到 PyPI
- 未对现有 `examples/demo/demo.sqlite` 执行破坏性重建；demo 的 RBAC 路径使用临时数据库验证
- 未运行 `djlint`；本版本未修改模板

已知限制与风险接受见第 1.2 节与第 5 节。

## 5. 代码审查与缺陷严重度门禁

发布前应依据以下清单对变更代码进行核验：

### 5.1 核心核验维度

- **契约与架构**：符合 `requirements.md` 预期行为；依赖方向不反向、无循环导入。
- **数据完整性**：CRUD 状态与事务回滚正确，一对多计数语义正确，外键与级联行为合规。
- **安全基线**：密码不入日志，CSRF 开启，TFA 流程不可跳过，未授权默认 403，无 SQL 注入与任意文件访问。
- **测试质量**：正例、反例、错误路径均有断言，断言最终数据状态而非仅断言状态码。
- **版本兼容**：只按 `pyproject.toml` 声明的依赖基线实现；不出现 `try/except ImportError` 导入回退、`hasattr`/`getattr` 回退、`sys.version_info` 或版本号判断等旧版本兼容分支。测试不得用 `warnings.catch_warnings()` 配合 `simplefilter("error", DeprecationWarning)` 处理弃用，应直接断言新版本行为；弃用告警由项目级 pytest 配置统一处理。升级无法按新版本实现时，提升下限并记录变更。

### 5.2 严重度与发布门禁

- **Critical**
  - 定义：可导致 RCE、认证绕过、大规模数据泄露/损坏
  - 示例：RCE、SQL 注入、未授权 Admin 访问
  - 发布影响：**绝对阻塞发布**（不得书面豁免）

- **High**
  - 定义：可导致账号接管、权限提升、TFA 绕过、令牌伪造
  - 示例：弱签名令牌、JWT 绕过 TFA、inactive admin 越权
  - 发布影响：**阻塞发布**，或需负责人书面风险接受

- **Medium**
  - 定义：局部数据偏差、信息泄露或条件触发问题
  - 示例：一对多计数偏大（CR-002）、缺少邮箱格式正则
  - 发布影响：修复或登记遗留风险

- **Low / Info**
  - 定义：轻微体验、日志、代码命名或文档规范问题
  - 示例：命名不直观、注释错别字
  - 发布影响：可排期后续优化

## 6. 影响范围说明

每次版本或功能升级，至少说明：

- **影响范围**：哪些模块、文档或接口受到影响
- **安全影响**：是否涉及认证、授权、CSRF、JWT、TFA 或敏感配置
- **兼容性影响**：是否保留旧接口、是否需要迁移
- **测试影响**：是否需新增测试或调用 demo
- **发布影响**：是否需要额外审查或回滚计划

## 7. 回滚条件

适用于以下情形：

- 安全风险高于可接受范围
- 核心 demo 无法运行
- 关键需求失效或核心路径回归
- 文档与实现冲突且无法及时确定真相

### 最小回滚动作

1. 停止发布或撤回当前版本。
2. 记录影响范围与触发条件。
3. 更新对应风险文档。
4. 评估是否需要回退到上一个稳定版本。
5. 记录回滚后状态与下一步计划。

## 8. 发布说明模板

```text
版本：vX.Y.Z
发布日期：YYYY-MM-DD
摘要：
  - 主要改动
  - 影响范围
  - 兼容性说明
风险：
  - 安全
  - 兼容
  - 测试
回滚：
  - 触发条件
  - 具体动作
```

## 9. 说明

本文是工程发布的最小治理文件，用于确认“当前状态、影响、检查、回滚”四个关键问题。它不替代需求、架构和安全文档，而是让这些文档在版本管理中形成闭环。
