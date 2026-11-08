# Flask-Exts 行为契约与需求目录（Requirements & Contracts）

> 本文是 Flask-Exts 的**行为契约单一事实源**：用稳定的 `REQ-*` 编号描述“系统应该怎样”，并给出前置条件、输入、行为、输出/副作用、错误、不变量与验收依据。
>
> | 项目 | 内容 |
> | --- | --- |
> | 文档版本 | v0.1（首批 49 条） |
> | 状态 | 可用 |
> | 最后更新 | 2026-11-08 |
> | 数据快照 | 2026-11-07（仓库版本 `0.4.0`；未复核） |
> | 适用仓库 | `flask-exts` |
> | 配套文档 | `architecture.md`（架构）、`spec.md`（设计/实现）、`testing.md`（测试）、`demo.md`（示例）、`security.md`（安全）、`view.md`（View/Admin） |
>
> **使用规则**
>
> - 测试从本文的 `REQ-*` 推导，而不是从实现反推。
> - 每条 `active` 契约至少有一个测试引用它；没有测试的契约必须标 `implemented-partial` 或 `known-gap`。
> - 本文描述“应该怎样”；`spec.md` 描述“为什么这样设计/当前怎么实现”；两者冲突时按第 2.4 节处理。
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
- [12. 追溯矩阵](#12-追溯矩阵)

## 0. 快速使用

### 0.1 写测试时

1. 找到要验证的 `REQ-*`。
2. 阅读“行为 / 输出 / 错误 / 不变量”。
3. 在测试的 docstring、测试名或注释中标注 `REQ-*`，例如：

```python
def test_login_success_creates_session(app, client, user_factory):
    """REQ-AUTH-001: valid credentials establish a session."""
    ...
```

4. 在 `testing.md` 的用例表中记录 `REQ-*`（后续补齐）。

### 0.2 改行为时

1. 先判断是“契约错”还是“实现错”。
2. 契约错：更新本文，再改测试与实现。
3. 实现错：保留契约，先写失败测试，再修代码。
4. 不允许直接把代码现状抄进本文来“消除冲突”。

## 1. 契约格式与编号

### 1.1 编号规则

```text
REQ-<域>-<三位序号>
```

| 域 | 含义 | 示例 |
| --- | --- | --- |
| `EXT` | 扩展生命周期 | `REQ-EXT-003` |
| `DATA` | 数据库/查询 | `REQ-DATA-002` |
| `AUTH` | 登录/会话/TFA | `REQ-AUTH-003` |
| `AUTHZ` | 授权 | `REQ-AUTHZ-004` |
| `REG` | 注册/邮箱验证/改邮箱 | `REQ-REG-005` |
| `RESET` | 密码重置 | `REQ-RESET-002` |
| `TOKEN` | 令牌生成/校验/失效 | `REQ-TOKEN-004` |
| `CSRF` | CSRF | `REQ-CSRF-002` |
| `ADMIN` | Admin/ModelView | `REQ-ADMIN-005` |
| `VIEW` | View/自定义页面 | `REQ-VIEW-001` |

规则：

- 编号**永不复用**；删除/废弃的契约保留编号，状态改 `deprecated`。
- 一个 `REQ` 只描述一个可验证的行为；不要把多个行为塞进一条。
- 契约描述“可观察结果”，不要绑定内部类名/函数名，除非行为依赖它。
- 需要实现细节时，链接 `spec.md` / `view.md` / `security.md`，不要复制整段代码。

### 1.2 条目模板

每条契约包含：

| 字段 | 要求 |
| --- | --- |
| 状态 | `implemented` / `implemented-partial` / `known-gap` / `proposed` / `deprecated` |
| 前置 | 触发行为前必须成立的条件 |
| 输入 | 请求参数、表单、令牌、配置等 |
| 行为 | 系统必须做什么 |
| 输出/副作用 | 响应、状态码、重定向、数据库变化、邮件、session |
| 错误 | 必须返回的错误类型/状态/提示 |
| 不变量 | 任何情况下都不能发生的事 |
| 验收 | 测试文件/用例 ID；没有测试时写“待补” |
| 关联 | 架构/安全/示例文档链接 |

## 2. 状态、追溯与冲突处理

### 2.1 状态定义

| 状态 | 含义 |
| --- | --- |
| `implemented` | 当前代码满足，且至少有一个测试覆盖 |
| `implemented-partial` | 当前代码基本满足，但测试/边界不完整 |
| `known-gap` | 这是目标契约，但当前代码**不满足**；关联 `SEC-*`/`C*` 风险 |
| `proposed` | 尚未实现，作为下一阶段目标 |
| `deprecated` | 不再适用；保留编号与历史说明 |

### 2.2 追溯规则

- `REQ` → `testing.md` 用例 ID → 测试文件/函数。
- `REQ` → `demo.md` 场景（如果用户可见）。
- `REQ` → `view.md` / `security.md`（如果涉及领域细节）。
- `known-gap` 必须在 `security.md` 第 11 节或 `view.md` 第 16 章有对应条目。

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

当“本文说 A、代码做 B”时：

1. 判断哪边错：契约错，还是实现偏离契约。
2. 契约错：更新本文，再改测试/实现。
3. 实现错：保留契约，先写失败测试，再修代码。
4. 无法立即修复：状态改 `known-gap`，关联 `SEC-*`/`C*`，并在 `testing.md` 标“待补/待修”。

## 3. 扩展生命周期

### REQ-EXT-001 扩展注册与名称校验

- **状态**：`implemented`
- **前置**：无
- **输入**：`Extension` 子类
- **行为**：注册扩展；名称必须唯一、非空、ASCII 合法；重复名称拒绝
- **输出/副作用**：注册表新增实例；可被 `get_extension` 查询
- **错误**：重复名称/非 `Extension`/非法名称抛 `ExtensionError`
- **不变量**：同一注册表内名称唯一；失败注册不改变已有扩展
- **验收**：`testing.md` E-01～E-04；`tests/unit/extension_core/test_registry.py`
- **关联**：`spec.md` 2.2/2.3

### REQ-EXT-002 依赖顺序与依赖错误

- **状态**：`implemented`
- **前置**：扩展声明 `dependencies`
- **输入**：扩展注册顺序、依赖图
- **行为**：依赖先于被依赖初始化；无依赖扩展保持注册顺序；缺失依赖/循环依赖/自依赖拒绝
- **输出/副作用**：初始化顺序稳定
- **错误**：缺失依赖抛 `ExtensionNotFoundError`；循环/自依赖抛 `ExtensionDependencyError`
- **不变量**：任何扩展都不会在依赖之前初始化
- **验收**：`testing.md` E-05～E-10；`tests/unit/extension_core/test_registry.py`
- **关联**：`spec.md` 2.2

### REQ-EXT-003 两阶段初始化幂等与顺序

- **状态**：`implemented`
- **前置**：扩展已注册
- **输入**：`init_app` / `post_init`
- **行为**：`init_app` 先于 `post_init`；两阶段各自幂等；`post_init` 按依赖顺序执行
- **输出/副作用**：每个扩展的 `init_app`/`post_init` 最多执行一次
- **错误**：`post_init` 前未 `init` 抛 `ExtensionInitError`
- **不变量**：重复调用不产生重复注册/重复副作用
- **验收**：`testing.md` E-11～E-14；`tests/unit/extension_core/test_registry.py`
- **关联**：`spec.md` 2.2/2.3

### REQ-EXT-004 关闭顺序与异常隔离

- **状态**：`implemented`
- **前置**：扩展已初始化
- **输入**：`shutdown`
- **行为**：按初始化逆序关闭；单个扩展关闭异常不阻止其他扩展关闭
- **输出/副作用**：资源释放；产生 warning
- **错误**：单扩展异常被隔离
- **不变量**：关闭后不残留已绑定资源
- **验收**：`testing.md` E-15/E-16；`tests/unit/extension_core/test_manager.py`
- **关联**：`spec.md` 2.2

## 4. 数据库与查询

### REQ-DATA-001 单例绑定、会话与释放

- **状态**：`implemented`
- **前置**：Flask app 配置 `SQLALCHEMY_DATABASE_URI`
- **输入**：`db.init_app(app)` / `db.dispose()` / app context
- **行为**：`db` 是单应用单例；绑定后 `db.session` 在 app context 内复用；重复绑定未 dispose 的 app 报错；dispose 后允许重新绑定；`reset_all()` 删表重建
- **输出/副作用**：engine/session 绑定到当前 app
- **错误**：缺少 URI/重复绑定抛 `RuntimeError`
- **不变量**：一个 `db` 实例同一时刻只绑定一个 app；上下文结束后 session 被移除
- **验收**：`testing.md` D-01～D-08；`tests/unit/datastore/sqla/test_db.py`
- **关联**：`spec.md` 4.2；`flask-exts/docs/advanced/database.rst`

### REQ-DATA-002 Query 的 JOIN、搜索、筛选与排序

- **状态**：`implemented-partial`
- **前置**：SQLAlchemy 模型与关系
- **输入**：列路径、搜索词、过滤操作符、排序字段
- **行为**：关系路径自动 JOIN 并复用 alias；`=` 精确、`^` 前缀、`$` 后缀、否则包含；过滤支持 `==`/`!=`/`>`/`<`/`like`/`in`/`between`/`is_null` 等；排序支持单列/多列
- **输出/副作用**：生成可执行的 `Select`
- **错误**：无效关系路径抛 `ValueError`/`AttributeError`
- **不变量**：相同 JOIN 路径不重复生成 alias
- **验收**：`testing.md` D-09～D-18；`tests/unit/datastore/sqla/test_query.py`（部分）
- **关联**：`spec.md` 4.2.3；Admin 计数契约见 `REQ-ADMIN-005`

## 5. 认证与会话

### REQ-AUTH-001 登录成功建立会话

- **状态**：`implemented`
- **前置**：用户存在、密码正确、账号可登录、CSRF 通过
- **输入**：`username`、`password`、可选 `next`
- **行为**：校验密码哈希；`tfa_enabled=False` 时调用 `login_user(force=True)`；渲染/重定向到 `next` 或 `/user/index/`
- **输出/副作用**：session 中存在 `_user_id`；HTTP 302
- **错误**：无（失败见 `REQ-AUTH-002`）
- **不变量**：密码明文不落库、不进日志；`next` 必须经过安全重定向
- **验收**：`testing.md` UC-03；`tests/integration/usercenter/test_user_view.py::test_register`
- **关联**：`spec.md` 5.2；`security.md` 3.1

### REQ-AUTH-002 登录失败统一提示

- **状态**：`implemented`
- **前置**：无
- **输入**：不存在的用户名 / 错误密码
- **行为**：不区分“用户不存在/密码错误”；不存在用户也执行 dummy scrypt 校验；不建立 session
- **输出/副作用**：统一提示 `Invalid username or password.`
- **错误**：`InvalidCredentialsError` 被表单捕获
- **不变量**：响应不泄露用户是否存在；失败不产生 `_user_id`
- **验收**：`testing.md` UC-04；`tests/integration/usercenter/test_user_view.py`
- **关联**：`security.md` 3.1/5.1

### REQ-AUTH-003 TFA 未完成不得建立会话

- **状态**：`implemented`
- **前置**：用户 `tfa_enabled=True`，密码正确
- **输入**：登录表单
- **行为**：只写 `pending_tfa_user_id`（及 remember 标记），**不调用** `login_user`；重定向 `/user/verify_tfa/?next=...`
- **输出/副作用**：session 无 `_user_id`；有 pending 标记
- **错误**：无
- **不变量**：TFA 完成前任何登录保护页不可访问
- **验收**：`testing.md` S-18；`test_tfa`、`test_tfa_cannot_be_bypassed_after_password_login`
- **关联**：`security.md` 8.3

### REQ-AUTH-004 TFA 验证成功完成登录

- **状态**：`implemented`
- **前置**：session 中有有效 pending user，用户仍启用 TFA
- **输入**：正确 TOTP 或恢复码
- **行为**：验证第二因子；成功后 `login_user(force=True)`；清理 pending；设置 `tfa_verified`；重定向 `next`
- **输出/副作用**：session 中有 `_user_id` 与 `tfa_verified`；恢复码登录消耗一个恢复码
- **错误**：错误验证码不建立 session，提示 `Invalid code`
- **不变量**：第二因子失败不改变登录状态；恢复码只能使用一次
- **验收**：`testing.md` S-16/S-17；`test_tfa`、`test_recovery`
- **关联**：`security.md` 8.3

### REQ-AUTH-005 密码变更使旧会话失效

- **状态**：`implemented`
- **前置**：用户已登录
- **输入**：旧密码、新密码、重复新密码
- **行为**：校验旧密码；保存新哈希；`get_id()` 的密码指纹变化
- **输出/副作用**：旧 session 的 `_user_id` 失效；旧密码登录失败；新密码登录成功
- **错误**：旧密码错误/两次不一致时拒绝
- **不变量**：密码变更后旧会话不能继续访问受保护页
- **验收**：`testing.md` S-19；`test_core.py::test_password_change_invalidates_existing_login_session`、`test_change_password`
- **关联**：`security.md` 5.3；JWT 例外见 `security.md` SEC-08

### REQ-AUTH-006 登出清理认证与 TFA 状态

- **状态**：`implemented`
- **前置**：用户已登录或处于 TFA pending
- **输入**：`GET /user/logout/`
- **行为**：调用 `logout_user`；清理 `_user_id`、`tfa_verified`、`tfa_recovery`、pending TFA、rebind pending、remember 标记
- **输出/副作用**：重定向登录页；session 无认证残留
- **错误**：无
- **不变量**：登出后不能恢复半完成 TFA 登录
- **验收**：`testing.md` UC-06；`test_tfa` 的登出断言
- **关联**：`security.md` 3.4

### REQ-AUTH-007 未激活账号的访问边界

- **状态**：`implemented`
- **前置**：用户已认证但 `is_active=False`（非 admin）
- **输入**：访问资料/账号功能
- **行为**：`profile`/`index` 可访问；`change_password`、`email_change`、`enable_tfa`、`setup_tfa`、`recovery_codes` 被拒绝
- **输出/副作用**：拒绝时 403
- **错误**：`@requires_active` 拒绝
- **不变量**：未激活账号不能使用账号级功能
- **验收**：`testing.md` UC-20；`test_inactive_account_blocked_from_account_features`
- **关联**：`security.md` 4.4；admin 例外见 `REQ-AUTHZ-005`

### REQ-AUTH-008 安全重定向

- **状态**：`implemented`
- **前置**：请求含 `next` / `url` 参数
- **输入**：任意重定向目标
- **行为**：只允许本地路径；拒绝绝对 URL、协议相对 URL、反斜杠、编码 `//`、畸形 URL、首字符空白
- **输出/副作用**：非法目标回退到安全默认 URL
- **错误**：不抛异常，直接使用 fallback
- **不变量**：不能重定向到外部域名
- **验收**：`testing.md` S-20；`tests/unit/security/test_urls.py`
- **关联**：`security.md` 7.5

## 6. 授权

### REQ-AUTHZ-001 admin 角色允许访问 Admin

- **状态**：`implemented`
- **前置**：用户有 `admin` 角色
- **输入**：访问 Admin 视图
- **行为**：`SimpleAuthorizer` 放行
- **输出/副作用**：视图可渲染
- **错误**：无
- **不变量**：非 admin/非 super_admin 默认拒绝
- **验收**：`testing.md` S-12；`tests/unit/security/test_authorizer.py::test_allow_admin_user`
- **关联**：`security.md` 4.2

### REQ-AUTHZ-002 默认拒绝与匿名访问

- **状态**：`implemented`
- **前置**：无认证或用户无角色
- **输入**：访问普通 Admin/ModelView
- **行为**：匿名 ModelView 返回 403；`@login_required` 先重定向登录；无角色普通用户拒绝
- **输出/副作用**：403 或登录重定向
- **错误**：默认拒绝
- **不变量**：未授权用户不能访问 Admin 模型数据
- **验收**：`testing.md` A-25/A-26、S-13；`test_authorizer.py`
- **关联**：`security.md` 4.2/4.5

### REQ-AUTHZ-003 allow_access 公开视图

- **状态**：`implemented`
- **前置**：视图设置 `allow_access=True`
- **输入**：匿名/已登录请求
- **行为**：允许访问；不再要求 admin/super_admin；`@requires_active` 的方法仍检查 active
- **输出/副作用**：公开页面可访问
- **错误**：无
- **不变量**：公开视图不能泄露受保护数据
- **验收**：`testing.md` S-14；`test_authorizer.py::test_view_allow_access_precedes_authentication_gates`
- **关联**：`security.md` 4.2

### REQ-AUTHZ-004 requires_active 保护账号功能

- **状态**：`implemented`
- **前置**：方法标记 `@requires_active`
- **输入**：已登录用户请求
- **行为**：`is_active=False` 时拒绝；`is_active=True` 时继续后续授权
- **输出/副作用**：403
- **错误**：拒绝
- **不变量**：未激活账号不能使用标记为 active-only 的功能
- **验收**：`testing.md` S-15；`test_inactive_account_blocked_from_account_features`
- **关联**：`security.md` 4.2

### REQ-AUTHZ-005 禁用 admin 必须失去 Admin 权限

- **状态**：`known-gap`
- **前置**：用户有 `admin` 角色且 `is_active=False`
- **输入**：访问 Admin/账号功能
- **行为**：**必须拒绝**；禁用账号不能继续使用高权限
- **输出/副作用**：403/拒绝
- **错误**：拒绝
- **不变量**：`is_active=False` 必须覆盖 `admin` 角色
- **当前实现**：`SimpleAuthorizer` 在 active 检查前短路 admin，**仍放行**
- **验收**：待补（新增测试将先失败）；关联 `security.md` SEC-01
- **关联**：`security.md` 4.3；`spec.md` 第 7 章

### REQ-AUTHZ-006 role_need 与 super_admin

- **状态**：`implemented`
- **前置**：用户 active
- **输入**：`role_need` 或 `super_admin` 角色
- **行为**：`role_need` 匹配放行；`super_admin` 放行；inactive 的非 admin 用户拒绝
- **输出/副作用**：允许/拒绝
- **错误**：无匹配时拒绝
- **不变量**：inactive 用户不能靠 `role_need`/`super_admin` 绕过 active 检查
- **验收**：`testing.md` S-13；`test_authorizer.py::test_authorize_without_view_uses_permission_context`
- **关联**：`security.md` 4.2

## 7. 注册与邮箱验证

### REQ-REG-001 注册创建激活但未验证邮箱的用户

- **状态**：`implemented`
- **前置**：用户名/邮箱未被占用
- **输入**：`username`、`password`、`email`、CSRF
- **行为**：创建用户；密码哈希；`is_active=True`；`email_verified=False`；不自动登录；发送 `user_registered` 信号
- **输出/副作用**：用户落库；重定向登录；验证邮件（若配置 sender）
- **错误**：重复用户名/邮箱提示
- **不变量**：密码明文不落库；邮箱验证状态不改变 active
- **验收**：`testing.md` UC-01；`test_register`
- **关联**：`spec.md` 5.3；`security.md` 3.5

### REQ-REG-002 重复用户名/邮箱拒绝

- **状态**：`implemented-partial`
- **前置**：用户名或邮箱已存在
- **输入**：注册表单
- **行为**：拒绝创建；提示重复字段；不产生新用户
- **输出/副作用**：错误提示；数据库无新记录
- **错误**：`UserAlreadyExistsError` / 表单错误
- **不变量**：用户名/邮箱唯一
- **验收**：`testing.md` UC-02；`test_register_rejects_duplicate_email`（用户名重复待补）
- **关联**：`spec.md` 4.6

### REQ-REG-003 邮箱验证令牌

- **状态**：`implemented-partial`
- **前置**：用户有邮箱且未验证
- **输入**：验证令牌
- **行为**：校验签名/时间/邮箱哈希/密码哈希；标记 `email_verified=True`、`email_verified_at`；不修改 `is_active`；重复使用返回 `already_verified`
- **输出/副作用**：用户邮箱状态更新
- **错误**：过期/无效/用户不存在分别返回错误状态
- **不变量**：验证邮箱不改变账号 active 状态
- **验收**：`testing.md` S-08；`test_core.py::test_verify_email`、`test_register`（过期边界待补）
- **关联**：`security.md` 6.3

### REQ-REG-004 重发验证邮件

- **状态**：`implemented`
- **前置**：用户已登录
- **输入**：POST `/user/resend_verification/`
- **行为**：已验证提示；未验证且有邮箱则发送新令牌；无邮箱提示错误
- **输出/副作用**：邮件；重定向 profile
- **错误**：表单失败 400
- **不变量**：不改变 active/email_verified
- **验收**：`testing.md` UC-09；`test_resend_email_verification`
- **关联**：`security.md` 6.3

### REQ-REG-005 改邮箱需要密码与新邮箱确认

- **状态**：`implemented`
- **前置**：用户已登录且 active
- **输入**：新邮箱、当前密码、CSRF
- **行为**：校验当前密码；新邮箱格式合法；发送确认链接到新邮箱；确认前旧邮箱继续有效；确认后更新邮箱并标记已验证；重复邮箱拒绝
- **输出/副作用**：确认邮件；确认后用户邮箱变化
- **错误**：密码错误/邮箱非法/重复邮箱拒绝
- **不变量**：未确认前不切换邮箱；旧令牌在邮箱/密码变化后失效
- **验收**：`testing.md` UC-10～UC-12、S-09；`test_change_email_*`
- **关联**：`security.md` 6.4

### REQ-REG-006 注册邮箱必须是合法邮箱格式

- **状态**：`known-gap`
- **前置**：注册表单提交
- **输入**：`email`
- **行为**：必须是合法邮箱格式；非法格式拒绝
- **输出/副作用**：表单错误
- **错误**：邮箱格式错误
- **当前实现**：`RegisterForm.email` 只有 `DataRequired()`，没有 `Email()`（`security.md` SEC-05）
- **验收**：待补（新增无效邮箱注册测试）
- **关联**：`security.md` SEC-05

## 8. 密码重置

### REQ-RESET-001 找回密码不泄露邮箱是否存在

- **状态**：`implemented`
- **前置**：无（未登录）
- **输入**：邮箱
- **行为**：无论邮箱是否存在都显示同一提示；仅对存在且 `email_verified=True` 的用户发送重置令牌
- **输出/副作用**：统一提示；可能发送邮件
- **错误**：无（不暴露存在性）
- **不变量**：响应内容/时序不应明显区分邮箱是否存在（时序为尽力而为）
- **验收**：`testing.md` UC-14；`test_forgot_password`
- **关联**：`security.md` 6.5

### REQ-RESET-002 重置令牌校验与密码更新

- **状态**：`implemented-partial`
- **前置**：用户 `email_verified=True`
- **输入**：重置令牌、新密码、重复密码、CSRF
- **行为**：校验令牌；要求邮箱已验证；设置新密码哈希；成功后重定向登录
- **输出/副作用**：密码更新；旧密码失效
- **错误**：过期/无效/未验证/缺少密码分别拒绝
- **不变量**：未验证邮箱不能重置；令牌不可跨密码/邮箱变化复用
- **验收**：`testing.md` S-10；`test_core.py`、`test_forgot_password`（过期边界待补）
- **关联**：`security.md` 6.5

### REQ-RESET-003 重置后旧密码/旧令牌/旧会话失效

- **状态**：`implemented-partial`
- **前置**：重置成功
- **输入**：旧密码/旧令牌/旧 session
- **行为**：旧密码登录失败；旧令牌因密码哈希变化失效；旧 session 因密码指纹变化失效
- **输出/副作用**：新密码可登录
- **错误**：旧密码/旧令牌拒绝
- **不变量**：重置后旧凭据不可继续使用
- **验收**：`testing.md` S-19；`test_core.py`、`test_change_password`
- **关联**：`security.md` 5.3/6.5；JWT 例外见 SEC-08

## 9. 令牌

### REQ-TOKEN-001 令牌载荷包含用户与凭据指纹

- **状态**：`implemented`
- **前置**：用户存在
- **输入**：用户、动作类型
- **行为**：生成载荷 `(user_id, email_hash, password_hash)`；改邮箱额外包含 `new_email`
- **输出/副作用**：签名令牌
- **错误**：用户/邮箱缺失时不生成
- **不变量**：令牌不能伪造；载荷长度/类型必须校验
- **验收**：`testing.md` S-01/S-05/S-09；`test_core.py`
- **关联**：`security.md` 6.2

### REQ-TOKEN-002 令牌有效期与配置

- **状态**：`implemented-partial`
- **前置**：无
- **输入**：`RESET_PASSWORD_MAX_AGE` / `VERIFY_EMAIL_MAX_AGE` / `CHANGE_EMAIL_MAX_AGE`
- **行为**：重置默认 1800 秒；验证/改邮箱默认 7 天；超过有效期返回 `expired`
- **输出/副作用**：过期令牌被拒绝
- **错误**：`ExpiredTokenError`
- **不变量**：过期令牌不能执行动作
- **验收**：`testing.md` S-06（过期测试当前注释掉，待补）
- **关联**：`security.md` 6.1

### REQ-TOKEN-003 无效/篡改/用户不存在令牌被拒绝

- **状态**：`implemented-partial`
- **前置**：无
- **输入**：随机/篡改/错误 salt/未知用户令牌
- **行为**：签名无效/载荷错误 → `invalid`；用户不存在 → `no_user`
- **输出/副作用**：不执行动作
- **错误**：`InvalidTokenError` / `TokenUserNotFoundError`
- **不变量**：无效令牌不能修改任何用户状态
- **验收**：`testing.md` S-07/S-11；`test_core.py::test_verify_email`（部分）
- **关联**：`security.md` 6.2

### REQ-TOKEN-004 邮箱/密码变化使旧令牌失效

- **状态**：`implemented-partial`
- **前置**：令牌已签发
- **输入**：邮箱或密码发生变化后的旧令牌
- **行为**：邮箱哈希/密码哈希不匹配 → 拒绝；重置/改邮箱令牌一次性；邮箱验证重复使用返回 `already_verified`
- **输出/副作用**：旧令牌不可用
- **错误**：`InvalidTokenError`
- **不变量**：旧令牌不能在新凭据状态下执行动作
- **验收**：`testing.md` S-09/S-10；`test_core.py`（改邮箱令牌在密码变更后失效待补）
- **关联**：`security.md` 6.2

## 10. CSRF

### REQ-CSRF-001 令牌按会话生成并使用派生密钥

- **状态**：`implemented`
- **前置**：`CSRF_ENABLED=True`
- **输入**：表单/请求
- **行为**：session 中生成随机 token；用 `CSRF_SECRET_KEY` 或从 `SECRET_KEY` 派生的 CSRF 密钥签名；同一请求内 `g` 缓存
- **输出/副作用**：表单包含 `csrf_token`
- **错误**：无
- **不变量**：CSRF 密钥与主密钥/其他用途密钥隔离
- **验收**：`testing.md` F-08/F-11；`tests/unit/forms/form/test_form.py`
- **关联**：`security.md` 7.1；`spec.md` 4.4.2

### REQ-CSRF-002 缺失/无效/过期令牌被拒绝

- **状态**：`implemented-partial`
- **前置**：`CSRF_ENABLED=True`
- **输入**：缺失/篡改/过期/不匹配 token
- **行为**：分别返回缺失、无效、过期、不匹配错误；不执行写操作
- **输出/副作用**：表单校验失败
- **错误**：`ValidationError`
- **不变量**：无有效 token 的写请求不能成功
- **验收**：`testing.md` F-10；`test_form.py`（过期/篡改 HTTP 级待补）
- **关联**：`security.md` 7.1

### REQ-CSRF-003 默认开启，显式配置才关闭

- **状态**：`implemented`
- **前置**：无
- **输入**：`CSRF_ENABLED`
- **行为**：默认 `True`；只有显式 `False` 才禁用；禁用时不生成/不校验 token
- **输出/副作用**：表单字段存在/不存在
- **错误**：无
- **不变量**：生产默认不能静默关闭
- **验收**：`testing.md` F-09；`test_nocsrf_form`
- **关联**：`security.md` 7.2

## 11. Admin / View

### REQ-ADMIN-001 列表分页

- **状态**：`implemented`
- **前置**：已授权访问 ModelView
- **输入**：`page`、`page_size`
- **行为**：`page` 从 0 开始；`page_size` 必须在白名单内，否则回退默认；返回当前页数据与总数
- **输出/副作用**：列表模板渲染
- **错误**：非法参数回退默认
- **不变量**：分页不能越界导致 500；总数与页数一致
- **验收**：`testing.md` A-01～A-04；`test_pagination.py`
- **关联**：`view.md` 12

### REQ-ADMIN-002 搜索

- **状态**：`implemented`
- **前置**：`column_searchable_list` 配置
- **输入**：`search`
- **行为**：在配置列/关联列搜索；`=` 精确、`^` 前缀、`$` 后缀、否则包含；多词 AND、列间 OR
- **输出/副作用**：过滤后的列表与总数
- **错误**：无
- **不变量**：搜索不改变未匹配记录
- **验收**：`testing.md` A-07/A-08；`test_search.py`
- **关联**：`view.md` 7.6

### REQ-ADMIN-003 筛选

- **状态**：`implemented`
- **前置**：`column_filters` 配置
- **输入**：`flt*` 参数
- **行为**：按列类型生成操作符；支持关联列；保留 active filters
- **输出/副作用**：过滤后的列表
- **错误**：非法值按过滤器 clean 处理
- **不变量**：筛选不会绕过授权
- **验收**：`testing.md` A-09/A-10；`test_views.py`/`test_search.py`
- **关联**：`view.md` 7.4

### REQ-ADMIN-004 排序

- **状态**：`implemented`
- **前置**：`column_sortable_list` / `column_default_sort`
- **输入**：`sort`（列索引）、`desc`
- **行为**：按指定列排序；支持多列；无参数时使用默认排序
- **输出/副作用**：有序列表
- **错误**：非法索引回退默认
- **不变量**：排序不改变结果集
- **验收**：`testing.md` A-05/A-06；`test_sorting.py`
- **关联**：`view.md` 7.5

### REQ-ADMIN-005 一对多搜索/筛选的计数正确

- **状态**：`known-gap`
- **前置**：根模型与子模型是一对多关系；搜索/筛选涉及子表
- **输入**：搜索/筛选请求
- **行为**：分页总数必须等于**去重后的根记录数**，不能按 JOIN 行数计数
- **输出/副作用**：`count` 与根记录数一致
- **错误**：无
- **不变量**：计数不随子记录数量放大
- **当前实现**：`build_count()` 应用 JOIN 未去重，计数偏大（C2）
- **验收**：`testing.md` A-31（待补）；关联 `view.md` C2
- **关联**：`spec.md` 4.2.3/7.1

### REQ-ADMIN-006 CRUD 与最终数据库状态

- **状态**：`implemented`
- **前置**：已授权；`can_create/edit/delete` 允许
- **输入**：创建/编辑/删除表单
- **行为**：创建/更新/删除记录；成功 flash；失败回滚；删除仅 POST
- **输出/副作用**：数据库最终状态符合提交
- **错误**：校验失败/数据库错误返回错误提示
- **不变量**：失败不留下部分写入
- **验收**：`testing.md` A-11/A-17；`test_views.py`/`test_actions.py`
- **关联**：`view.md` 13

### REQ-ADMIN-007 Inline 父子记录

- **状态**：`implemented-partial`
- **前置**：父模型与子模型存在关系；`inline_models` 配置
- **输入**：父表单 + Inline 子表单
- **行为**：支持一对多/一对一/多对多；保存父记录后处理子记录新增/修改/删除；失败抛 `InlineModelError`
- **输出/副作用**：父子记录最终状态正确
- **错误**：关系找不到/子表单无效时拒绝
- **不变量**：子记录必须属于该父记录
- **验收**：`testing.md` A-18～A-21；`test_inline_forms.py`/`test_inline_views.py`
- **关联**：`view.md` 9；Inline+AJAX 缺陷 C1

### REQ-ADMIN-008 AJAX 外键查询与内联更新

- **状态**：`implemented-partial`
- **前置**：`ajax_refs` 或 `column_editable_list` 配置
- **输入**：`/ajax/lookup/`、`/ajax/update/` JSON 请求
- **行为**：按 term 搜索关联记录并返回 `(id, text)`；内联更新校验 CSRF 后保存
- **输出/副作用**：JSON 响应；数据库更新
- **错误**：无权限/CSRF/校验失败拒绝
- **不变量**：不能通过 AJAX 绕过授权/CSRF
- **验收**：`testing.md` A-22；`test_ajax.py`/`test_inline_ajax.py`
- **关联**：`view.md` 10；Inline+AJAX C1

### REQ-ADMIN-009 导出

- **状态**：`implemented-partial`
- **前置**：`can_export=True`
- **输入**：导出类型、当前搜索/筛选/排序
- **行为**：按 `column_export_list` 导出；CSV 流式；tablib 格式；`export_max_rows` 限制；不支持的格式提示并重定向
- **输出/副作用**：文件下载
- **错误**：不支持的格式/宏格式化器拒绝
- **不变量**：导出不能绕过授权；不能导出超过上限
- **验收**：`testing.md` A-13～A-15；`test_export.py`
- **关联**：`view.md` 11

### REQ-ADMIN-010 视图级权限开关

- **状态**：`known-gap`
- **前置**：`can_create`/`can_edit`/`can_delete`
- **输入**：创建/编辑/删除/内联更新请求
- **行为**：开关为 `False` 时对应路由必须拒绝（重定向或 403），包括 `/ajax/update/`
- **输出/副作用**：不执行写操作
- **错误**：拒绝
- **当前实现**：`ajax_update` 只检查 `column_editable_list`，未检查 `can_edit`（V-01）
- **验收**：待补；关联 `view.md` V-01、`security.md` SEC-19
- **关联**：`view.md` 4.4

### REQ-ADMIN-011 列表 URL 正确编码

- **状态**：`known-gap`
- **前置**：搜索词/筛选值含空格、`&`、`#`、中文等
- **输入**：分页/排序/搜索/筛选参数
- **行为**：生成的列表 URL 必须正确编码并可回放
- **输出/副作用**：URL 可访问且结果一致
- **错误**：无
- **当前实现**：`get_list_url` 手写查询字符串，未 URL 编码（C6）；`hasattr(get_url)` 死分支（C5）
- **验收**：`testing.md` A-32（待补）；关联 `view.md` C5/C6
- **关联**：`view.md` 12

### REQ-ADMIN-012 复合主键与字符串主键

- **状态**：`implemented`
- **前置**：模型有复合主键或字符串主键
- **输入**：列表/编辑/删除/导出
- **行为**：主键正确编码/解析；记录可定位与删除
- **输出/副作用**：CRUD 正常
- **错误**：不存在记录提示
- **不变量**：主键值不丢失/不串记录
- **验收**：`testing.md` A-23/A-24；`test_primary_keys.py`
- **关联**：`view.md` 6.1

### REQ-VIEW-001 自定义页面与模板

- **状态**：`implemented-partial`
- **前置**：自定义 `View` 或 `list_template`
- **输入**：`expose_url`、`allow_access`、`login_required`、`requires_active`
- **行为**：路由可访问；`render`/`render_string` 渲染；模板可 `extends` 内置模板并传自定义参数
- **输出/副作用**：HTML 响应
- **错误**：未授权 403/登录重定向
- **不变量**：模板覆盖不丢失列表/分页/筛选 UI
- **验收**：`demo.md` TreeView；无专门单元测试（待补）
- **关联**：`view.md` 14

## 12. 追溯矩阵

### 12.1 按域汇总

| 域 | 契约数 | 主要验收 | 已知缺口 |
| --- | ---: | --- | --- |
| EXT | 4 | E-01～E-16 | — |
| DATA | 2 | D-01～D-18 | Query 边界测试部分 |
| AUTH | 8 | UC-03～UC-06、S-16～S-20 | JWT/TFA 见 SEC-02 |
| AUTHZ | 6 | S-12～S-15 | SEC-01（inactive admin） |
| REG | 6 | UC-01/02/09～12、S-08/S-09 | SEC-05（邮箱格式）、S-09 边界 |
| RESET | 3 | UC-14、S-10/S-19 | 令牌过期测试 |
| TOKEN | 4 | S-01～S-11 | 过期/篡改测试部分 |
| CSRF | 3 | F-08～F-11 | 过期/篡改 HTTP 级 |
| ADMIN | 12 | A-01～A-33 | C2、C5/C6、V-01 |
| VIEW | 1 | demo TreeView | 自定义页面测试待补 |

### 12.1a 关键 `REQ → CASE` 映射

> 说明：本表当前覆盖 **14/49** 条核心链路，不是完整追溯矩阵。每次新增/修改契约时都必须先补上对应用例，再更新此表；未列出的条目以各契约的“验收”字段为准。

| 关键契约 | 主要验证入口 | 说明 |
| --- | --- | --- |
| `REQ-EXT-003` | `E-11`、`E-12`、`E-13`、`E-14` | 扩展初始化/后初始化幂等与顺序 |
| `REQ-EXT-004` | `E-15`、`E-16` | 关闭顺序与异常隔离 |
| `REQ-DATA-001` | `D-01`～`D-08` | 数据库绑定、session、dispose |
| `REQ-DATA-002` | `D-09`～`D-18` | Query search/filter/sort/order |
| `REQ-AUTH-001` | `UC-03` | 登录成功建立 session |
| `REQ-AUTH-003` | `S-18` | TFA 未完成不得建立 session |
| `REQ-AUTH-004` | `S-16`、`S-17` | TFA 成功后完成登录 |
| `REQ-AUTHZ-005` | `待补` | inactive admin 权限问题，当前为 `known-gap` |
| `REQ-REG-001` | `UC-01` | 注册流程 |
| `REQ-REG-006` | `待补` | 非法邮箱格式，当前为 `known-gap` |
| `REQ-RESET-001` | `UC-14` | 找回密码不泄露邮箱存在性 |
| `REQ-RESET-002` | `S-10` | 重置令牌校验与密码更新 |
| `REQ-ADMIN-005` | `A-31` | 一对多计数/聚合正确性 |
| `REQ-VIEW-001` | `demo TreeView` | 自定义 view/模板可用性 |

### 12.2 状态汇总

| 状态 | 数量 | 说明 |
| --- | ---: | --- |
| `implemented` | 31 | 有测试或行为明确 |
| `implemented-partial` | 13 | 行为基本满足，边界/测试待补 |
| `known-gap` | 5 | AUTHZ-005、REG-006、ADMIN-005、ADMIN-010、ADMIN-011 |

> 数量会随契约补充变化；以条目状态为准。
>
> 当前 `REQ → CASE` 映射覆盖 **14/49**（见 12.1a）；`testing.md` 引用 **10** 个唯一 `REQ-*`。

### 12.3 下一步补齐顺序

1. `REQ-AUTHZ-005`（inactive admin）→ 先写失败测试，修授权顺序。
2. `REQ-ADMIN-005`（一对多计数）→ 聚合/子查询修复，补 `A-31`。
3. `REQ-ADMIN-010`（can_edit）→ `ajax_update` 加检查，补 `V-01` 测试。
4. `REQ-ADMIN-011`（URL 编码）→ `url_for` + `urlencode`，补 `A-32`。
5. `REQ-REG-006`（邮箱格式）→ 补 `Email()`，补无效邮箱测试。
6. 补令牌过期/篡改、CSRF 过期/篡改、SMTP 证书/日志等边界测试。
