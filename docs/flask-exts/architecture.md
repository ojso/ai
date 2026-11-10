# Flask-Exts 架构概览（Architecture Overview）

> 本文是 Flask-Exts 的**稳定架构一页纸**：系统边界、模块依赖、扩展生命周期、请求路径、状态所有权、关键决策与失败边界。实现与领域细节见 `spec.md`；安全边界见 `security.md`。
>
> | 项目 | 内容 |
> | --- | --- |
> | 文档版本 | v0.1 |
> | 状态 | 可用 |
> | 最后更新 | 2026-11-09 |
> | 数据快照 | 2026-11-07（仓库版本 `0.4.0`；未复核） |
> | 适用仓库 | `flask-exts` |
> | 配套文档 | `requirements.md`（契约）、`spec.md`（实现、Admin、插件与数据库专题）、`security.md`（安全）、`testing.md`（验证）、`demo.md`（示例） |

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

- Flask 3.x、WTForms 3.x、SQLAlchemy 2.x、Flask-Login、Flask-Babel、tablib、PyJWT、pyotp、cryptography。
- 数据库：默认 SQLite；生产建议 PostgreSQL。
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

| 模块 | 责任 | 不应承担 |
| --- | --- | --- |
| `extension_core` | 扩展注册、依赖、两阶段生命周期、关闭 | 具体业务功能 |
| `builtin_extensions` | 把内置能力装配成可组合扩展 | 复杂业务逻辑 |
| `datastore/sqla` | `db` 单例、engine/session、Query 构造 | Admin/表单/安全策略 |
| `admin` | View、ModelView、Handler、DataBackend、SqlaBackend | 用户存储/安全插件实现 |
| `forms` | WTForms 扩展、字段、控件、校验器、CSRF | 数据库查询/路由 |
| `security` | 密钥、哈希、加密、令牌、授权、TFA | 用户表 CRUD |
| `userstore` | 用户/角色/资料存储抽象与 SQLAlchemy 实现 | 登录页面/路由 |
| `usercenter` | 登录/注册/改邮箱/改密/TFA/找回页面 | 密码哈希算法实现 |
| `emailer` | 信号驱动的邮件发送与 SMTP | 业务令牌生成 |
| `frontend` | 插件管理、样式/脚本、Jinja 全局 | 业务逻辑 |
| `portal` | 首页与 Admin 入口 | 模型管理 |

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
        ├─ 单扩展异常隔离，不阻止其他扩展
        └─ 最终 db.dispose()
```

关键约束：

- 扩展名称唯一、ASCII 合法。
- 缺失依赖 → `ExtensionNotFoundError`；循环/自依赖 → `ExtensionDependencyError`。
- `init_app` 与 `post_init` 各自幂等。
- `post_init` 晚注册扩展不会自动回溯扫描（见 `spec.md` 第 10.16 节 C10）。
- `db` 是单应用单例；重新绑定前必须 `dispose()`。

> 扩展编写者的实现要求、约束与作者检查清单，详见 [`spec.md` 第 11 章（插件与扩展机制）](./spec.md#11-插件与扩展机制)。

## 4. 请求生命周期

### 4.1 Admin 列表

```text
GET /admin/<endpoint>/
  → ViewMeta 包装
  → 可选 @login_required（匿名先重定向登录）
  → View.allow → SimpleAuthorizer
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
  → 校验密码
  → tfa_enabled?
      ├─ 否 → login_user → 重定向
      └─ 是 → session[pending_tfa_user_id] → /user/verify_tfa/
POST /user/verify_tfa/
  → 校验 TOTP/恢复码
  → login_user(force=True) → 清理 pending
```

### 4.4 自定义 View

```text
@expose_url 方法
  → ViewMeta 包装
  → @login_required / @requires_active
  → View.allow
  → render() / render_string()
```

## 5. 状态与数据所有权

| 状态 | 存放位置 | 生命周期 | 说明 |
| --- | --- | --- | --- |
| 扩展实例/注册表 | `app.extensions["exts"]` | app 生命周期 | Manager/Registry |
| `db` engine/session | 模块级 `db` 单例 | app 绑定，dispose 释放 | 一进程一 app |
| SQLAlchemy session | app context 内 `scoped_session` | 请求/app context | teardown 移除 |
| 用户/角色/资料 | `userstore`（默认 SQLAlchemy） | 持久化 | `User`/`Role`/`UserProfile` |
| 登录状态 | Flask signed session | 浏览器会话 | `_user_id` 含密码指纹 |
| TFA pending/verified | Flask session | 登录流程 | pending 不等于已登录 |
| TOTP secret | `users.totp_secret` | 持久化 | AES-GCM 加密 |
| 恢复码 | `users.recovery_codes` | 持久化 | 哈希存储 |
| 邮箱/重置令牌 | URL + 签名载荷 | 短时有效 | 载荷含 id/email hash/password hash |
| CSRF token | session + `g` | 请求/会话 | 派生密钥签名 |
| 配置 | `app.config` | app 生命周期 | 密钥/SMTP/CSRF/Babel |

设计含义：

- `db` 不适合“一进程多 app 并发”；需要多 app 时每个 app 使用独立 `SqlaDb` 实例。
- 令牌是无状态签名，不依赖 session；密码/邮箱变化通过载荷哈希使旧令牌失效。
- TFA secret 必须可逆（计算 TOTP），所以用 AES-GCM 而不是哈希。
- session 只存引用/标记，不存大对象。

## 6. 横切关注点

| 关注点 | 机制 | 详见 |
| --- | --- | --- |
| 安全 | 密钥派生、哈希、加密、令牌、CSRF、TFA、授权 | `security.md` |
| 国际化 | Flask-Babel、翻译目录、时区 | `testing.md` 第 7.12 节 / `requirements.md` |
| 配置 | `app.config`、环境变量、实例配置 | 仓库 `flask-exts/docs/configure.rst` |
| 信号 | `user_registered`、`to_send_email` | `testing.md` 第 7.8 节 / 本文第 3、4 章 |
| 前端资源 | `frontend` 插件、依赖排序、vendor | `testing.md` 第 7.10 节 / `spec.md` 第 5 章 |
| CLI | `datastore`、`security` 命令组 | `testing.md` 第 7.11 节 / `requirements.md` |
| 测试 | pytest、Admin fixtures、安全/用户中心用例 | `testing.md` |
| 示例 | `examples/demo`、`examples/simple` | `demo.md` |

## 7. 关键决策与取舍

| 决策 | 原因 | 代价 |
| --- | --- | --- |
| 扩展组合 + 依赖排序 | 可拆装、可复用、可测试 | 跨扩展协作需要 `post_init`/信号/代理 |
| 两阶段初始化 | 先建服务，再互相装配 | 生命周期更复杂，必须幂等 |
| `ModelView` 组合 `DataBackend` | 视图与数据源解耦 | 协议较大，新后端样板多 |
| backend 用工厂创建 | backend 需要读取 `view` 配置 | 构造顺序更隐式 |
| `db` 模块级单例 | 使用简单，符合 Flask 生态 | 一进程一 app；测试需 `dispose()` |
| `LocalProxy` | 避免层层传递 app/扩展 | 隐式依赖上下文，静态分析困难 |
| 信号解耦邮件/注册 | 注册与发信互不直接依赖 | 参数契约隐式，测试需清理全局 sender |
| 按用途派生密钥 | 一处泄露不波及全部 | `SECRET_KEY` 轮换影响 TOTP/令牌/会话 |
| session 密码指纹 | 改密自动失效旧会话 | 不保护 JWT（见 `security.md` SEC-08） |
| 无状态签名令牌 | 不需要服务端存储 | 无法主动撤销单个令牌，只能等过期/轮换密钥 |
| SQLAlchemy 2.0 `Mapped` + `back_populates` | 类型清晰、关系显式 | 代码略冗长 |

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

## 8. 失败边界与约束

| 场景 | 当前行为 | 风险/注意 |
| --- | --- | --- |
| 扩展依赖缺失/循环 | 启动期抛异常 | 不会带病启动 |
| 单扩展 `shutdown` 异常 | 隔离并 warning | 其他扩展继续关闭 |
| 数据库写入失败 | `rollback`，视图 flash 错误 | 不留下部分写入 |
| Inline 保存失败 | `InlineModelError`，返回 4xx/错误 | Inline+AJAX 有 C1 缺陷 |
| 令牌过期/无效 | `ExpiredTokenError`/`InvalidTokenError` | 不修改用户状态 |
| 邮件发送失败 | `SmtpError` 被捕获并 warning | 注册可能“成功但没收到信” |
| `db` 重复绑定 | `RuntimeError` | 必须先 `dispose()` |
| 列表计数一对多 | 当前可能偏大 | C2；见 `requirements.md` `REQ-ADMIN-005` |
| TFA 无限重试 | 可在线暴力破解 | SEC-03；见 `security.md` |
| 未激活 admin | 仍可访问 Admin | SEC-01；见 `security.md` |

非功能约束：

- Python 3.10+；不支持更早版本。
- 单进程单 app 的 `db` 限制；多 app 需独立 `SqlaDb`。
- SQLite 适合开发/测试；生产注意外键、大小写、并发差异。
- 列表页通过 `joinedload`/`selectinload` 降低 N+1；计数正确性仍需修复。
- 安全边界、限流、审计、密钥轮换不在架构层自动保证，需部署/代码配合。

## 9. 相关文档

| 文档 | 用途 |
| --- | --- |
| [`requirements.md`](./requirements.md) | 行为契约、`REQ-*`、验收标准 |
| [`spec.md`](./spec.md) | 项目规划、设计模式、模块实现；第 10～12 章分别维护 View/Admin、插件与数据库专题 |
| [`security.md`](./security.md) | 威胁模型、认证/授权、令牌、CSRF、TFA、风险 |
| [`testing.md`](./testing.md) | 测试分层、用例、E2E、性能、覆盖率、CI |
| [`demo.md`](./demo.md) | `examples/demo` 运行、结构、扩展、排错 |
| [`README.md`](./README.md) | 文档索引、单一事实源、更新规则 |
