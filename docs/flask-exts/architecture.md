# Flask-Exts 架构概览（Architecture Overview）

> 本文是 Flask-Exts 的**稳定架构一页纸**：系统边界、模块依赖、扩展生命周期、请求路径、状态所有权、关键决策与失败边界。实现与领域细节见 `spec.md`；安全边界见 `security.md`。
>
> | 项目 | 内容 |
> | --- | --- |
> | 文档版本 | v0.1 |
> | 状态 | 可用 |
> | 最后更新 | 2026-11-18 |
> | 适用仓库 | `flask-exts` |

## 1. 系统上下文

```text
┌──────────────┐
│ 浏览器/API 客户端 │
└──────┬───────┘
       │ HTTPS
       ▼
┌──────────────┐     可选：TLS 终止、限流、安全响应头
│ 反向代理/WAF  │
└──────┬───────┘
       ▼
┌────────────────────────────────────────────┐
│ Flask 应用                                  │
│  ├─ Admin UI（/admin）                      │
│  ├─ UserCenter（/user）                     │
│  ├─ Portal（/）                             │
│  └─ 自定义 View/API                         │
│                                            │
│  ExtensionManager + builtin_extensions      │
└──────┬───────────────────────────┬─────────┘
       │ SQLAlchemy                 │ SMTP_SSL
       ▼                            ▼
┌──────────────┐            ┌──────────────┐
│ SQLite /     │            │ 邮件服务      │
│ PostgreSQL   │            └──────────────┘
└──────────────┘
```

外部依赖：

- Flask 3.x、WTForms 3.3+、SQLAlchemy 2.1+、Flask-Login、Flask-Babel、tablib、PyJWT、pyotp、cryptography。
- 仓库内 `examples/demo` 使用 SQLite；库中的 `SqlaDb` 按 `SQLALCHEMY_DATABASE_URI` 绑定数据源，不能把 demo 配置泛化为全库默认。
- 邮件：`smtplib.SMTP_SSL`；未配置 `NOREPLY_EMAIL_SENDER` 时不真正发信。

## 2. 模块与依赖

```text
extension_core
  ├─ Extension / Registry / Manager
  └─ 生命周期与依赖排序
        ▲
        │ 被编排
builtin_extensions（组合根）
  ├─ datastore/sqla      → SQLAlchemy db/query
  ├─ admin               → View/ModelView/DataBackend/SqlaModelView
  ├─ forms               → FlaskForm/fields/widgets/validators/CSRF
  ├─ security            → keys/hasher/encryptor/tokens/authorizer/TFA
  ├─ userstore           → UserStore/SqlaUserStore
  ├─ usercenter          → UserView/forms（/user）
  ├─ emailer             → 信号 → SMTP
  ├─ frontend            → 插件与静态资源
  ├─ portal              → 首页/Admin 入口
  └─ login               → Flask-Login 集成

proxies / signals / commands / constants  → 横切基础设施
```

- `extension_core`
  - 责任：扩展注册、依赖、两阶段生命周期、关闭
  - 不应承担：具体业务功能

- `builtin_extensions`
  - 责任：把内置能力装配成可组合扩展
  - 不应承担：复杂业务逻辑

- `datastore/sqla`
  - 责任：默认导出的模块级 `db`、`SqlaDb` 实例、engine/session 与 Query 构造
  - 不应承担：Admin/表单/安全策略

- `admin`
  - 责任：View、ModelView、Handler、DataBackend、SqlaBackend
  - 不应承担：用户存储/安全插件实现

- `forms`
  - 责任：WTForms 扩展、字段、控件、校验器、CSRF
  - 不应承担：数据库查询/路由

- `security`
  - 责任：密钥、哈希、加密、令牌、授权、TFA
  - 不应承担：用户表 CRUD

- `userstore`
  - 责任：用户/角色/资料存储抽象与 SQLAlchemy 实现
  - 不应承担：登录页面/路由

- `usercenter`
  - 责任：登录/注册/改邮箱/改密/TFA/找回页面
  - 不应承担：密码哈希算法实现

- `emailer`
  - 责任：信号驱动的邮件发送与 SMTP
  - 不应承担：业务令牌生成

- `frontend`
  - 责任：插件管理、样式/脚本、Jinja 全局
  - 不应承担：业务逻辑

- `portal`
  - 责任：首页与 Admin 入口
  - 不应承担：模型管理

> 逻辑依赖方向是“上层依赖下层抽象”；跨模块协作优先用 `proxies`、信号和扩展 `post_init`，避免硬编码互相导入。

## 3. 扩展生命周期

```text
ExtensionManager()
  ├─ register_builtin=True → 注册内置扩展
  └─ init_app(app)
        ├─ app.extensions["exts"] = manager
        ├─ Phase 1: registry.init_all(app)
        │     └─ 按依赖顺序调用每个扩展的 init_app
        └─ Phase 2: registry.post_init_all(app)
              └─ 按依赖顺序调用 post_init
                    （如 AdminExtension 收集 AdminViewMixin 的视图）

运行期
  └─ shutdown()
        ├─ 逆序调用每个扩展的 shutdown
        ├─ Registry 捕获 `ExtensionError` 并记录 warning；其他异常可能继续传播并中断后续清理
        └─ 数据库扩展关闭时调用 `db.dispose()`
```

关键约束：

- 扩展名称唯一、ASCII 合法。
- 缺失依赖 → `ExtensionNotFoundError`；循环/自依赖 → `ExtensionDependencyError`。
- `init_app` 与 `post_init` 各自幂等。
- app 初始化后注册的新扩展会执行自身的 `init_app` / `post_init`；不会重跑已初始化扩展的 `post_init`。例如 Admin 不会自动重新扫描后来注册扩展提供的视图（见 `spec.md` 第 10.16 节 CR-010）。
- 默认导出的模块级 `db` 同一时刻绑定一个 app；任一 `SqlaDb` 实例 `dispose()` 后可重新绑定，不能同时绑定多个 app。

> 扩展编写者的实现要求、约束与作者检查清单，详见 [`spec.md` 第 11 章（插件与扩展机制）](./spec.md#11-插件与扩展机制)。

## 4. 请求生命周期

### 4.1 Admin 列表

```text
GET /admin/<endpoint>/
  → ViewMeta 包装
  → View.allow → Authorizer.check_view_access（共用登录门）→ SimpleAuthorizer 角色回退或 RBACAuthorizer requirement
  → ModelView.index_view
      → get_list_args（page/page_size/sort/desc/search/flt）
      → get_safe_page_size
      → get_list
          → Pagination/Filter/Form Handler
          → DataBackend.get_list
              → Query：search → filter → auto join → count → page → sort
              → SQLAlchemy execute
      → render(list.html)
```

### 4.2 Admin 创建/编辑/删除

```text
GET  /new/ | /edit/?id=... | /details/?id=...
  → FormHandler / backend.scaffold_form
  → ModelFieldConverter → WTForms
POST /new/ | /edit/
  → validate_on_submit
  → form.populate_obj
  → backend.create_model / update_model / delete_model
      → session.add/commit
      → 失败 rollback
  → flash + redirect
```

### 4.3 登录与 TFA

```text
POST /user/login/
  → 锁定未过期? → 提示剩余时间，不校验密码
  → 校验密码
      ├─ 失败 → failed_login_count + 1（达到阈值写 locked_until）→ 统一错误
      └─ 成功 → is_active?
            ├─ 否 → 提示禁用，不建立会话
            └─ 是 → tfa_enabled?
                  ├─ 否 → login_user → 清零失败计数 → 重定向
                  └─ 是 → session[pending_tfa_user_id] → /user/verify_tfa/
POST /user/verify_tfa/
  → 锁定未过期 / pending 无效 → 清理 pending → 登录页
  → 校验 TOTP/恢复码
      ├─ 失败 → failed_login_count + 1（与密码失败共享）
      └─ 成功 → login_user → 清理 pending → 清零失败计数
每个请求加载会话：
  → user_loader → is_active?
      ├─ 否 → 清除 `_user_id` / remember Cookie → 匿名
      └─ 是 → 校验密码指纹 → current_user
```

### 4.4 自定义 View

```text
@expose_url 方法
  → ViewMeta 包装
  → View.allow（非公开视图要求登录；公开视图按 login_required_functions 拦截）
  → render() / render_string()
```

## 5. 状态与数据所有权

- **扩展实例/注册表**
  - 存放位置：`app.extensions["exts"]`
  - 生命周期：app 生命周期
  - 说明：Manager/Registry

- `db` engine/session
  - 存放位置：默认模块级 `db` 或显式 `SqlaDb` 实例
  - 生命周期：app 绑定；`dispose()` 释放并允许重绑
  - 说明：单个实例不能同时绑定多个 app

- **SQLAlchemy session**
  - 存放位置：app context 内 `scoped_session`
  - 生命周期：请求/app context
  - 说明：teardown 移除

- **用户/角色/资料**
  - 存放位置：`userstore`（默认 SQLAlchemy）
  - 生命周期：持久化
  - 说明：`User`/`Role`/`UserProfile`

- **登录状态**
  - 存放位置：Flask signed session
  - 生命周期：浏览器会话
  - 说明：`_user_id` 含密码指纹

- **TFA pending/verified**
  - 存放位置：Flask session
  - 生命周期：登录流程
  - 说明：pending 不等于已登录

- **TOTP secret**
  - 存放位置：`users.totp_secret`
  - 生命周期：持久化
  - 说明：AES-GCM 加密

- **失败登录计数/锁定**
  - 存放位置：`users.failed_login_count` / `users.locked_until`
  - 生命周期：持久化；锁定到期自动失效
  - 说明：账号级，与 IP 无关，跨进程共享

- **恢复码**
  - 存放位置：`users.recovery_codes`
  - 生命周期：持久化
  - 说明：哈希存储

- **邮箱/重置令牌**
  - 存放位置：URL + 签名载荷
  - 生命周期：短时有效
  - 说明：载荷含 id/email hash/password hash

- **CSRF token**
  - 存放位置：session + `g`
  - 生命周期：请求/会话
  - 说明：派生密钥签名

- **配置**
  - 存放位置：`app.config`
  - 生命周期：app 生命周期
  - 说明：密钥/SMTP/CSRF/Babel

设计含义：

- 一个 `SqlaDb` 实例不支持并发绑定多个 app；多 app 并发需用独立实例。同一实例可在 `dispose()` 后顺序重用。
- 令牌是无状态签名，不依赖 session；密码/邮箱变化通过载荷哈希使旧令牌失效。
- TFA secret 必须可逆（计算 TOTP），所以用 AES-GCM 而不是哈希。
- session 只存引用/标记，不存大对象。

## 6. 横切关注点

- **安全**
  - 机制：密钥派生、哈希、加密、令牌、CSRF、TFA、授权
  - 详见：`security.md`

- **国际化**
  - 机制：Flask-Babel、翻译目录、时区
  - 详见：`testing.md` 第 7.13 节 / `requirements.md`

- **配置**
  - 机制：`app.config`、环境变量、实例配置
  - 详见：仓库 `flask-exts/docs/configure.rst`

- **信号**
  - 机制：`user_registered`、`to_send_email`
  - 详见：`testing.md` 第 7.12 节 / 本文第 3、4 章

- **前端资源**
  - 机制：`frontend` 插件、依赖排序、vendor
  - 详见：`testing.md` 第 7.9 节 / `spec.md` 第 5 章

- **CLI**
  - 机制：`datastore`、`security` 命令组
  - 详见：`testing.md` 第 7.10 节 / `requirements.md`

- **测试**
  - 机制：pytest、Admin fixtures、安全/用户中心用例
  - 详见：`testing.md`

- **示例**
  - 机制：仓库内 `examples/demo`、`examples/simple`
  - 详见：`demo.md`

## 7. 关键决策与取舍

- **扩展组合 + 依赖排序**
  - 原因：可拆装、可复用、可测试
  - 代价：跨扩展协作需要 `post_init`/信号/代理

- **两阶段初始化**
  - 原因：先建服务，再互相装配
  - 代价：生命周期更复杂，必须幂等

- `ModelView` 组合 `DataBackend`
  - 原因：视图与数据源解耦
  - 代价：协议较大，新后端样板多

- **backend 用工厂创建**
  - 原因：backend 需要读取 `view` 配置
  - 代价：构造顺序更隐式

- **默认模块级 `db` 与显式 `SqlaDb` 实例**
  - 原因：使用简单，符合 Flask 生态
  - 代价：单实例同一时刻绑定一个 app；`dispose()` 后可复用

- `LocalProxy`
  - 原因：避免层层传递 app/扩展
  - 代价：隐式依赖上下文，静态分析困难

- **信号解耦邮件/注册**
  - 原因：注册与发信互不直接依赖
  - 代价：参数契约隐式，测试需清理全局 sender

- **按用途派生密钥**
  - 原因：一处泄露不波及全部
  - 代价：`SECRET_KEY` 轮换影响 TOTP/令牌/会话

- **session 密码指纹**
  - 原因：改密自动失效旧会话
  - 代价：不保护 JWT（见 `security.md` SEC-08）

- **无状态签名令牌**
  - 原因：不需要服务端存储
  - 代价：无法主动撤销单个令牌，只能等过期/轮换密钥

- **SQLAlchemy 2.0 `Mapped` + `back_populates`**
  - 原因：类型清晰、关系显式
  - 代价：代码略冗长

- **开发/主力 Python 锚定 Debian stable**
  - 原因：开发环境与系统一致
  - 代价：仅在发行版升级时提升，需同步 CI/RTD

### 7.1 设计决策记录规范（ADR）

重大架构调整或新增设计取舍时，应按以下最小模板记录：

```text
ADR-<序号>: <决策标题>
状态： proposed | accepted | superseded | rejected
日期： YYYY-MM-DD
背景： 触发问题、约束条件、相关需求
决策： 做什么、不做什么
理由： 优点、权衡
备选方案： 其他可行方案与未采用原因
风险： 主要风险与回滚方式
关联文档： spec.md / requirements.md / security.md
```

### 7.2 核心架构决策记录

#### ADR-001: 模块级默认 db 与显式 SqlaDb 实例生命周期

- **状态**：accepted
- **日期**：2026-11-10
- **背景**：Flask 生态普遍习惯导入模块级 `db`（如 `from flask_exts.datastore.sqla import db`），但测试环境频繁重建 app 或多 app 场景易引发单例跨 app 污染与未绑定异常。
- **决策**：导出默认模块级 `db` 实例满足 90% 单应用快速开发；每个 `SqlaDb` 实例同一时刻严格只绑定一个 app。多 app 并发时强制使用显式构造的 `SqlaDb()` 实例；同一实例顺序复用前必须显式调用 `dispose()`。
- **理由**：既契合主流 Flask 开发直觉，又避免了静态全局变量无序复用导致的数据串扰和连接池泄露。
- **备选方案**：纯动态 Factory 模式（要求每个视图层显式传参 `db`，对现有插件与 demo 侵入性过高）；允许多 app 共享连接池（线程安全与表元数据易混乱）。
- **风险**：测试用例忘记在 teardown 中 `db.dispose()` 会导致后续测试报 `RuntimeError`；已通过 `tests/conftest.py` 固化夹具清理。
- **关联章节**：[`spec.md` 第 12 章](./spec.md#12-数据库与持久化)、[`requirements.md` REQ-DATA-001](./requirements.md#req-data-001-单例绑定会话与释放)。

#### ADR-002: 模型关系强制显式声明，禁用动态 backref

- **状态**：accepted
- **日期**：2026-11-10
- **背景**：传统 SQLAlchemy 使用 `backref` 字符串隐式在目标模型注入反向属性，在 Admin 自动化表单生成、Inline 处理和类型检查（Mypy/IDE）时经常发生属性名不可见或隐式覆盖冲突。
- **决策**：所有内置模型与示例模型全面采用 SQLAlchemy 2.0 风格的 `Mapped[...]` 显式类型标注；双向关联强制使用 `relationship(..., back_populates="...")` 对称声明，严禁在库级模型中使用动态 `backref`。
- **理由**：双向属性显式可查，Admin 在内省外键与关系加载器时可以直接反射出对端真实字段名，降低运行时内省失败风险。
- **备选方案**：继续沿用 SQLAlchemy 1.4 的字符串 `backref`（简单但隐式，自动化字段反射易出错）。
- **风险**：模型代码声明行数增加约 15%~20%；已被 IDE 代码补全和类型安全性抵消。
- **关联章节**：[`spec.md` 第 10.4 节](./spec.md#104-modelview)。

#### ADR-003: 派生独立密钥隔离安全动作上下文

- **状态**：accepted
- **日期**：2026-11-10
- **背景**：单条 `SECRET_KEY` 如果在 Session 签名、CSRF 校验、邮箱验证令牌和 TOTP 加密中直接混用，任一场景（如 CSRF 或客户端令牌）发生签名推测，攻击者可直接复用到敏感的高特权上下文。
- **决策**：引入 `derive_key(secret_key, purpose)`，以版本化上下文 `flask-exts:key-derivation:v1:{purpose}` 为 salt 通过 HMAC-SHA256 派生不同用途的独立子密钥；JWT 强制使用独立配置 `JWT_SECRET_KEY`，不得回退到 `SECRET_KEY`。
- **理由**：实现密码学意义上的目的隔离（Key Separation），单用途令牌即便在传输或日志中泄露，也无法被反向用于伪造会话或解密数据库中的 TOTP secret。
- **备选方案**：所有模块共用 Flask 原生 `SECRET_KEY`（传统简单做法，安全防线单薄）。
- **风险**：轮换 `SECRET_KEY` 时会同时失效所有派生子密钥（包括 TOTP secret 加密密钥），需建立对应的重绑定/重加密流程。
- **关联章节**：[`security.md` 第 2.2 节](./security.md#22-密钥派生)。

#### ADR-004: 依赖基线提升为 Python >=3.11, WTForms >=3.3, SQLAlchemy >=2.1

- **状态**：accepted（2026-11-11 维护者确认；已在 v0.4.2 实施）
- **日期**：2026-11-11
- **背景**：WTForms 3.3.x（3.3.0/3.3.1/3.3.2）的上游 `Requires-Python` 均为 `>=3.11`；SQLAlchemy 2.1 系列（抽查 2.1.0/2.1.8）的上游 `Requires-Python` 也为 `>=3.11`。同时 WTForms 3.3 将 choice 迭代结果从裸元组改为 `Choice`/`SelectChoice` 对象，对 tuple choices 发出弃用告警，并调整了 `FieldList` 条目命名。项目当前只在 SQLAlchemy 2.1.8 上验证，为避免长期维护 2.0 与 2.1 两套行为路径，选择同时提升 WTForms 与 SQLAlchemy 的下限。
- **决策**：项目最低 Python 版本提升为 3.11；`pyproject.toml` 声明 `requires-python = ">=3.11"`、`WTForms>=3.3.2`、`SQLAlchemy>=2.1`，并移除 Python 3.10 classifier；测试文档与建议的 CI 矩阵只覆盖 3.11/3.12/3.13，SQLAlchemy 只覆盖 2.1.x。字段与 widget 按 WTForms 3.3 的 `Choice`/`SelectChoice` 行为实现，并在 `ChoiceField` 入口把 legacy tuple/dict choices 规范化为 `SelectChoice`，以消除 3.3 的弃用告警；不保留对 WTForms 3.2 及更早版本、SQLAlchemy 2.0 及更早版本的行为分支。
- **下限修订（2026-11-11）**：WTForms 下限由 `>=3.3` 提升为 `>=3.3.2`。3.3.1 修复 FieldList 重编号时丢失 form prefix（#944），3.3.2 修复嵌套 FieldList 条目复用父级旧索引（#948）；项目的 Admin inline/model 表单使用 FieldList，需排除这两个已知缺陷版本。
- **配套编码约束**：只为声明范围内的版本写代码。升级导致行为变化时，直接按新版本实现并提升下限，不写运行时兼容分支，例如 `try: from wtforms.fields import Choice, SelectChoice / except ImportError`、`hasattr`/`getattr` 回退、`sys.version_info` 或版本号判断。测试同样不得用 `warnings.catch_warnings()` 配合 `simplefilter("error", DeprecationWarning)` 局部处理弃用，应直接断言新版本行为，弃用告警由项目级 pytest 配置统一处理。该约束的代码侧权威说明见仓库 `AGENTS.md`。
- **理由**：WTForms 3.3 与 SQLAlchemy 2.1 的上游下限都已经是 Python 3.11，继续支持 Python 3.10 只能锁定旧版依赖；同时维护两套 choices/`iter_choices` 或 ORM 行为会放大测试矩阵和回归风险。统一到 WTForms 3.3 与 SQLAlchemy 2.1 后，字段、widget、表单与 ORM 行为与上游一致，并消除 tuple choices 的弃用告警。
- **备选方案**：继续声明 `WTForms<3.3`、`SQLAlchemy>=2.0` 并保留 Python 3.10（需要长期维护旧 choices/tuple 与 2.0 ORM 行为）；或同时支持 WTForms 3.3/旧版、SQLAlchemy 2.0/2.1（需在 `select.py`、`editable.py`、`QuerySelectField` 等位置保留双路径，测试矩阵翻倍）。
- **风险**：下游 Python 3.10 或 SQLAlchemy 2.0.x 用户无法直接升级；WTForms 3.3 的 `Choice` 对象、`FieldList` 命名和 choices 规范化行为，以及 SQLAlchemy 2.1 的行为变化，可能影响自定义字段/模板或查询代码；回滚需同时恢复 `WTForms<3.3`、`SQLAlchemy>=2.0`、Python 3.10 声明及旧版字段/ORM 实现，并重跑 3.10 与 SQLAlchemy 2.0 矩阵。
- **关联章节**：[`release.md` 第 3.1 节](./release.md#31-运行环境与依赖兼容性矩阵)、[`testing.md` 第 10.3 节](./testing.md#103-质量门禁)、[`README.md` 第 0.1 节](./README.md#01-准备环境python-311)。

#### ADR-005: 开发与主力验证 Python 版本锚定 Debian stable

- **状态**：accepted（2026-11-11 维护者确认）
- **日期**：2026-11-11
- **背景**：项目主要开发环境为 Debian stable；当前稳定版 Debian 13（trixie）默认 Python 3.13，仓库 `.venv`、CI 与 RTD 的主力任务均使用 3.13。ADR-004 已将最低支持版本定为 3.11，但没有记录“开发/主力版本如何选择、何时提升”的决策依据。
- **决策**：
  - 开发与主力验证 Python 版本跟随当前 Debian stable 的默认 Python：现为 3.13；仅当 Debian stable 升级并切换默认 Python 后，才同步提升主力版本。
  - `requires-python` 保持 ADR-004 的最低支持 `>=3.11`；提升最低支持需要单独决策，不随主力版本自动提升。
  - CI 至少验证两个锚点：3.11（最低支持）与 3.13（主力版本）；当前矩阵额外保留 3.12 作为中间版本补充。文档构建、RTD 与发布任务使用主力版本 3.13。
  - 主力版本变更时同步更新 `pyproject.toml` classifiers、CI 矩阵、`uv.lock`、RTD 配置与受影响的文档，并新增 ADR 或修订本条记录。
- **理由**：开发环境与操作系统稳定版一致，减少“本机可用、CI/部署不可用”的环境差异；同时保留 3.11 下限验证，避免为对齐开发机而丢弃仍受支持的发行版用户（如 Debian 12）。
- **备选方案**：立即将 `requires-python` 提升到 `>=3.13`（会排除 Debian 12、Ubuntu 24.04 等用户，属破坏性变更）；仅验证主力版本 3.13（无法发现最低版本回归）；每发布新 Python 即升级主力（与 Debian stable 节奏脱节，依赖生态未必就绪）。
- **风险**：Debian stable 升级时主力版本跳跃可能遇到依赖 wheel 缺失或行为变化，需要提前在 CI 增加新版本观察；若长期不升级，主力版本会落后于上游生态。回滚方式：恢复上一主力版本并同步 CI、RTD 与 classifier。
- **关联章节**：[`release.md` 第 3.1 节](./release.md#31-运行环境与依赖兼容性矩阵)、[`testing.md` 第 11.3 节](./testing.md#113-测试工作流已落地)、[`README.md` 第 0.1 节](./README.md#01-准备环境python-311)、仓库 `AGENTS.md` 与 `docs/develop.rst`。

## 8. 失败边界与约束

- **扩展依赖缺失/循环**
  - 当前行为：启动期抛异常
  - 风险/注意：不会带病启动

- `shutdown` 抛 `ExtensionError`
  - 当前行为：捕获 `Exception` 并记录 warning，随后清理初始化标记
  - 风险/注意：`BaseException` 不在此处理器中隔离

- **数据库写入失败**
  - 当前行为：`rollback`，视图 flash 错误
  - 风险/注意：不留下部分写入

- **Inline 保存失败**
  - 当前行为：`InlineModelError`，返回 4xx/错误
  - 风险/注意：Inline+AJAX 有 CR-001 缺陷

- **令牌过期/无效**
  - 当前行为：`ExpiredTokenError`/`InvalidTokenError`
  - 风险/注意：不修改用户状态

- **邮件发送失败**
  - 当前行为：`SmtpError` 被捕获并 warning
  - 风险/注意：注册可能“成功但没收到信”

- `SqlaDb` 重复绑定
  - 当前行为：未 `dispose()` 时抛 `RuntimeError`；释放后可重新绑定
  - 风险/注意：多 app 并发需使用独立实例

- **列表计数一对多**
  - 当前行为：`build_count()` 按 JOIN 后实际行数计数，与列表返回行数一致
  - 风险/注意：CR-002 已关闭；一对多重复行会同时出现在列表与计数中

- **TFA 在线尝试**
  - 当前行为：0.4.2 已加入账号级失败锁定与指数退避；仍缺 IP 维度、未知用户名与注册/找回入口限流
  - 风险/注意：SEC-03 部分修复；见 `security.md`

- **未激活 admin**
  - 当前行为：`SimpleAuthorizer` 先拒绝 inactive 用户，再判断 `admin` 角色
  - 风险/注意：SEC-01 已在 0.4.2 修复；旧版本部署仍需移除 `admin` 角色

非功能约束：

- Python 3.11+；不支持更早版本。该下限由 `WTForms>=3.3.2` 与 `SQLAlchemy>=2.1` 的上游要求决定，决策与回滚见第 7.2 节 ADR-004。
- 开发与主力验证版本锚定 Debian stable 默认 Python（当前 Debian 13 → 3.13），仅随 Debian stable 升级而提升；3.11 持续作为最低支持验证版本，见 ADR-005。
- 只支持 `pyproject.toml` 声明的单一依赖基线；不为范围外版本保留运行时兼容分支（`try/except ImportError` 导入回退、`hasattr`/`getattr` 回退、版本判断等）。测试不得用 `warnings.catch_warnings()` 局部屏蔽或升级 `DeprecationWarning`。
- 单个 `SqlaDb` 实例只能同时绑定一个 app；多 app 并发需独立实例，顺序复用前先 `dispose()`。
- SQLite 适合开发/测试；生产注意外键、大小写、并发差异。
- 列表页通过 `joinedload`/`selectinload` 降低 N+1；计数与列表行数保持一致（CR-002 已关闭）。
- 安全边界、限流、审计、密钥轮换不在架构层自动保证，需部署/代码配合。
