# Flask-Exts 安全指南（Security）

> 本文是 Flask-Exts 的**安全单一事实源**：威胁模型、认证/授权、密码与令牌、CSRF、TFA、JWT、配置基线、已知风险、测试覆盖与发布前检查。
>
> | 项目 | 内容 |
> | --- | --- |
> | 文档版本 | v0.1 |
> | 状态 | 可用 |
> | 最后更新 | 2026-11-18 |
> | 数据快照 | 2026-11-13（发布版本 `0.4.2`；HEAD `445b03d1fe6c59cd53405c8187de968c687a2909`；内容核对基线 `171b40968f309c04ae3ad423696227c2767b0055`；`0.4.2` 已包含 SEC-01/SEC-05/SEC-13/SEC-16/SEC-17/SEC-18/SEC-19 修复，SEC-03 为部分修复）。2026-11-15 工作树已修复 SEC-02/SEC-08/SEC-12，并完成 JWT 算法白名单、密钥校验、`iat`/`JWT_LEEWAY`、Bearer 大小写与 `id`/`amr` 严格校验；SEC-12 补充 Cookie 默认值开关、显式 `SameSite=None` 与 `ProxyFix` 场景；尚未提交或发布。2026-11-16 提交 `1349295` 补充 JWT 解码强制 `iat`、CSRF session token 改用 `secrets.token_urlsafe(32)`、TOTP secret 改为 flush 加服务层提交、未知 serializer 默认 30 分钟，以及用户/锁定时间统一 UTC；代码已提交，尚未发布。2026-11-17 工作树以 `View.login_required_functions` 取代 `login_required` 装饰器，匿名访问受限方法返回 403。2026-11-18 登录门抽到 `Authorizer.check_view_access()`，`SimpleAuthorizer` 与 `RBACAuthorizer` 共用；新增 `RBACAuthorizer` requirement 模型、视图声明、loader 与授权器选择说明。 |
> | 适用仓库 | `flask-exts` |
>
> **重要说明**：本文选定风险已对照 HEAD `171b40968f309c04ae3ad423696227c2767b0055` 做静态源码核对；这不是完整安全审计或渗透测试，也不能证明运行配置、风险可利用性或修复已验证。标记为“风险/待决策”的内容仍需结合部署环境评估；代码修复须先评审、补测试，再实施。

## 0. 快速安全基线

### 0.1 五条必须做到

1. **HTTPS + 安全 Cookie**：生产必须 HTTPS，并显式设置 `SESSION_COOKIE_SECURE=True`、`SESSION_COOKIE_SAMESITE`、`REMEMBER_COOKIE_SECURE=True`。
2. **强随机密钥**：`SECRET_KEY`、`JWT_SECRET_KEY`、`CSRF_SECRET_KEY` 使用独立、足够长的随机值，放在环境变量/密钥管理系统中，不写进仓库。
3. **保持 CSRF 开启**：生产不要设置 `CSRF_ENABLED=False`；该开关仅用于测试或明确无 Cookie 的 API。
4. **保护 admin 角色**：`admin` 角色当前拥有高权限；不要共享账号，管理员应启用 TFA，禁用账号前确认其 admin 角色已移除。
5. **限制认证入口**：`0.4.2` 已加入账号级失败锁定，但它只覆盖“已存在用户名”的连续失败；注册、找回密码、未知用户名尝试仍需在反向代理/WAF 层限流。

### 0.2 五条不要做

- 不要把 `SECRET_KEY` 设为 `demo`、`changeme` 或空值。
- 不要把令牌、密码、TOTP secret 写入日志。
- 不要在公网环境使用 demo 的 `admin/admin`。
- 不要在没有 TFA 的情况下把 admin 权限授予普通业务账号。
- 不要直接轮换 `SECRET_KEY` 而不评估 TOTP secret 失效（见 10.4）。

### 0.3 代码未修复时的临时配置阻断（Workarounds）

在核心安全风险未完成代码修复与发版前，生产部署必须在运维与配置层采取以下替代控制措施：

- **SEC-01**（禁用 admin 仍有效）
  - 缺陷根因：已在 `0.4.2` 修复；0.4.1 及更早版本仍优先放行 `admin` 角色
  - 临时阻断要求（运维/管理）：对 0.4.1 及更早的部署：**禁止单纯设置 `is_active=False`**；禁用或离职处理管理员时，必须同时移除其 `admin` 角色，或直接删除账号。

- **SEC-02**（JWT 绕过 TFA；工作树已修复，未发布）
  - 缺陷根因：`load_user_from_request` 仅检查 `is_active`，未验证 TFA 完成标记
  - 临时阻断要求（运维/管理）：对 0.4.2 及更早部署，**切勿为开启双因素认证的高权限账号发放纯密码换取的长期 JWT**；必须在 API 网关处要求二次验证凭据，或只允许会话认证。
  - 修复状态：工作树在 JWT 中加入 `pwd` 指纹与 `amr` 声明，`load_user_from_request` 对 TFA 用户要求 `amr` 含 `otp`；待发布后本条按退役规则处理。

- **SEC-03**（认证端点缺限流）
  - 缺陷根因：`0.4.2` 已加入账号级失败锁定（部分修复）：密码与第二因子共享计数、指数退避；但未知用户名、注册与找回密码入口仍无应用层计数
  - 临时阻断要求（运维/管理）：**反向代理硬性限流仍然必须**：Nginx / Envoy / WAF 对 `/user/login/`、`/user/register/`、`/user/verify_tfa/`、`/user/forgot_password/`、`/user/reset_password/` 按来源 IP 限流（如单 IP 每分钟 ≤5 次），与内置账号锁定叠加。

- **SEC-18**（未配置 sender 泄露令牌）（已在 0.4.2 修复）
  - 缺陷根因：`0.4.2` 的 `send_email` 只记录 sender 类型与脱敏收件人，不再输出 `data`
  - 临时阻断要求（运维/管理）：已发布 0.4.1 及更早版本仍会把完整载荷写入 warning；这些版本的日志需限制访问并过滤验证/重置链接。

- **SEC-19**（内联编辑绕过只读开关；旧别名 `V-01` 已废止）
  - 缺陷根因：已在 `0.4.2` 修复；0.4.1 及更早版本仅检查 `column_editable_list`
  - 临时阻断要求（运维/管理）：对 0.4.1 及更早的部署：若模型需全局只读，务必在 ModelView 中将 `column_editable_list` 显式置空 `()`，不要仅依赖 `can_edit = False`。

## 1. 范围与威胁模型

### 1.1 范围

本文覆盖：

- 用户认证、登录会话、登出、密码修改
- 授权（admin、`role_need`、公开视图、激活状态）
- 密码哈希与密码策略
- 邮箱验证、改邮箱、找回密码令牌
- CSRF
- TFA（TOTP + 恢复码）
- JWT Bearer 认证
- 开放重定向防护
- 安全相关配置、测试与发布检查

不覆盖：

- 操作系统、容器、网络、WAF、DDoS 防护
- 数据库本身的访问控制、备份加密、审计系统
- SMTP 服务商安全、邮件内容加密
- 供应链安全（依赖漏洞扫描需另行接入）
- 前端依赖（Bootstrap/vendor）的漏洞跟踪

### 1.2 资产

- **用户密码哈希**
  - 位置：`users.password`
  - 泄露/篡改影响：离线破解、撞库

- **会话**
  - 位置：Flask signed cookie（`_user_id` 等）
  - 泄露/篡改影响：账号接管

- `SECRET_KEY`
  - 位置：配置/环境
  - 泄露/篡改影响：伪造会话、令牌、CSRF

- `JWT_SECRET_KEY`
  - 位置：配置/环境
  - 泄露/篡改影响：伪造 Bearer token

- **邮箱/重置令牌**
  - 位置：URL query、邮件
  - 泄露/篡改影响：账号接管、邮箱变更

- **TOTP secret**
  - 位置：`users.totp_secret`（AES-GCM 加密）
  - 泄露/篡改影响：生成 2FA 验证码

- **恢复码**
  - 位置：`users.recovery_codes`（哈希）
  - 泄露/篡改影响：绕过 TFA

- **Admin 数据**
  - 位置：数据库/后台
  - 泄露/篡改影响：数据泄露、篡改、删除

- **SMTP 凭据**
  - 位置：`NOREPLY_EMAIL_SENDER`
  - 泄露/篡改影响：冒名发信、钓鱼

### 1.3 参与者与信任边界

- **匿名访问者**
  - 能力：访问公开页面、登录/注册/找回
  - 信任假设：不可信

- **普通用户**
  - 能力：登录、管理自己的资料
  - 信任假设：已通过密码认证

- **Admin**
  - 能力：访问 Admin 模型视图、批量操作、导出
  - 信任假设：高权限，必须重点保护

- **被禁用用户**
  - 能力：旧 session 在下一次请求即失效（`user_loader` 返回 `None` 并清理 session）
  - 信任假设：不应访问任何登录保护页

- **数据库读取者**
  - 能力：读取表数据
  - 信任假设：不应能直接伪造 TOTP/密码

- **网络攻击者**
  - 能力：窃听、篡改、重放
  - 信任假设：HTTPS 应阻止

- **邮件拦截者**
  - 能力：获取令牌链接
  - 信任假设：令牌必须有 TTL 且可失效

信任边界：

```text
浏览器 ──HTTPS──▶ 反向代理/WAF ──▶ Flask 应用 ──▶ 数据库
                                      │
                                      └──TLS──▶ SMTP
```

### 1.4 假设与前提

- 生产使用 HTTPS；Cookie 设置 `Secure`/`HttpOnly`/合理 `SameSite`。
- `SECRET_KEY`、`JWT_SECRET_KEY`、SMTP 凭据只存在于受控环境。
- 数据库访问受限；攻击者不能直接改 `users` 表。
- 邮件服务可信；用户能收到发往其邮箱的链接。
- Admin 角色只授予可信人员。
- 反向代理/WAF 提供限流、TLS 终止、安全响应头（库本身不提供这些）。

### 1.5 风险等级

- **高**：可导致账号接管、权限提升或大规模数据泄露；公网部署前必须处理或明确接受
- **中**：需要特定条件或组合利用；应尽快修复/补偿
- **低**：defense-in-depth、信息泄露或运维风险；按计划处理
- **信息**：设计取舍或文档差异，不直接构成漏洞

## 2. 安全架构与密钥

### 2.1 扩展装配

```text
SecurityExtension
  └─ Security
       ├─ hasher       (Blake2bHasher)
       ├─ serializer   (TimedUrlSerializer)
       ├─ encryptor    (AesGcmEncryptor)
       └─ Registry
            ├─ email_verification
            ├─ email_change
            ├─ reset_password
            ├─ authorizer (SimpleAuthorizer)
            └─ two_factor_authentication

LoginExtension
  └─ Flask-Login LoginManager
       ├─ user_loader               (session: id + fingerprint + is_active)
       └─ request_loader            (Bearer JWT)

UserCenterExtension
  └─ UserView (登录/注册/资料/改邮箱/改密码/TFA/找回/恢复码)

AdminExtension
  └─ Admin + 各 ModelView
```

### 2.2 密钥派生

所有派生密钥来自 Flask 的 `SECRET_KEY`，按用途隔离：

```python
def derive_key(secret_key, purpose):
    context = f"flask-exts:key-derivation:v1:{purpose}".encode("ascii")
    return hmac.digest(secret_key, context, "sha256")
```

- `hasher`
  - 算法/结果：HMAC-SHA256 派生密钥 + BLAKE2b（16 字节摘要）
  - 使用位置：邮箱、已存储密码哈希的指纹、恢复码；用户密码存储算法见第 5.1 节

- `url-token`
  - 算法/结果：HMAC-SHA256 派生密钥 + itsdangerous
  - 使用位置：邮箱验证、改邮箱、重置密码令牌

- `encryptor`
  - 算法/结果：HMAC-SHA256 派生密钥（32 字节）+ AES-256-GCM
  - 使用位置：TOTP secret

- `csrf`
  - 算法/结果：派生密钥或 `CSRF_SECRET_KEY`
  - 使用位置：CSRF token 签名

- **JWT**
  - 算法/结果：`JWT_SECRET_KEY`（独立配置）
  - 使用位置：Bearer token

要点：

- `SECRET_KEY` 为 `None`/空时，`derive_key` 抛 `RuntimeError`/`ValueError`；`Security.init_app()` 在初始化阶段即检查，缺失时直接抛 `RuntimeError`，避免延迟到首次使用才失败。
- 不同 purpose 的密钥互不相等，避免“一处泄露、处处可用”。
- 派生上下文带 `v1`，为未来迁移留出版本位。
- **JWT 使用独立密钥**，不要复用 `SECRET_KEY`。

### 2.3 密钥轮换的影响

- `SECRET_KEY`：现有 session、CSRF token、URL 令牌全部失效；**已加密的 TOTP secret 将无法解密**（当前无迁移机制）
- `CSRF_SECRET_KEY`：现有 CSRF token 失效
- `JWT_SECRET_KEY`：现有 Bearer token 失效
- **数据库中的 TOTP secret**：需要重新绑定 TFA；当前没有批量重加密工具

> 轮换 `SECRET_KEY` 前必须评估 TOTP 用户：要么先让用户重新绑定，要么提供一次性重加密迁移。当前代码没有自动迁移。

## 3. 认证与会话

### 3.1 登录流程

```text
GET /user/login/
  └─ 渲染登录表单（CSRF token）

POST /user/login/
  ├─ 表单校验（CSRF、用户名/密码必填）
  ├─ login_user_by_username_password(username, password)
  │    ├─ 锁定未过期 → 不校验密码 → AccountLockedError
  │    ├─ 用户不存在 → 执行 dummy scrypt 校验 → InvalidCredentialsError
  │    ├─ 用户存在但无密码 → dummy 校验 → InvalidCredentialsError
  │    ├─ 密码错误 → check_password_hash → 记录失败 → InvalidCredentialsError
  │    └─ 成功 → user（失败计数在完整登录成功后清零）
  ├─ user.is_active?
  │    ├─ 否 → 提示账号已禁用，不建立会话
  │    └─ 是 → safe_redirect_target(next, fallback)
  ├─ user.tfa_enabled?
  │    ├─ 否 → login_user(user) → 清零失败计数 → 重定向
  │    └─ 是 → session[pending_tfa_user_id] = user.id
  │             → 重定向 /user/verify_tfa/
  └─ 失败 → 统一提示 "Invalid username or password."
```

### 3.1a 失败计数与锁定

`/user/verify_tfa/` 与 `/user/recovery/` 的验证码错误同样计入 `failed_login_count`，命中阈值后写入 `locked_until`；锁定的账号无法继续 pending TFA（`_get_pending_tfa_user` 清理 pending 状态）。成功完成第二因子或成功重置密码时清零。详见 8.5。

安全要点：

- **统一错误**：登录失败不区分“用户不存在/密码错误”，降低枚举。锁定状态会单独提示剩余时间，因此已锁定账号可被识别；该枚举面与注册表单的用户名/邮箱重复提示一致（SEC-10）。
- **dummy hash**：用户不存在时也执行一次 scrypt 校验，降低时间侧信道。
- **失败锁定**：连续失败计数存在用户行上（`failed_login_count` / `locked_until`），与 IP 无关，跨进程一致，详见 8.5。
- **`is_active` 由 Flask-Login 原生检查**：登录不传 `force`；禁用账号无法建立会话。`is_active` 只表示管理禁用，与邮箱验证无关。
- **TFA 前不建立会话**：密码正确但 TFA 未完成时，只写入 pending user id，不调用 `login_user`。
- **安全重定向**：`next` 参数经过 `safe_redirect_target`（见 7.5）。

### 3.2 会话标识与密码指纹

`User.get_id()` 返回：

```python
password_fingerprint = current_security.hasher.hash(self.password or "")
return f"{self.id}:{password_fingerprint}"
```

`user_loader` 解析 `id:fingerprint`，先拒绝禁用账号，再重新校验密码哈希：

```python
raw_id, password_fingerprint = user_id.rsplit(":", 1)
user = current_userstore.user_loader(int(raw_id))
if user is None:
    return None
if not user.is_active:
    session.pop("_user_id", None)
    session["_remember"] = "clear"
    return None
if not current_security.hasher.verify(user.password or "", password_fingerprint):
    return None
```

效果：

- 修改密码后，旧 session 的 fingerprint 不匹配 → 会话失效。
- `is_active=False` 后，下一次请求即按匿名处理，并清除 `_user_id` 与 remember-me Cookie；重新启用账号不会恢复旧 Cookie。
- 改邮箱不会使 session 失效（session 只绑定密码）。
- 该机制只保护 **session**；JWT 路径在 `load_user_from_request` 中另行校验 `pwd` 指纹与 TFA 的 `amr` 声明（见 9.3）。

### 3.3 会话 Cookie 建议

库在初始化 `SecurityExtension` 时设置安全默认值：`SESSION_COOKIE_HTTPONLY=True`、`SESSION_COOKIE_SAMESITE="Lax"`、`REMEMBER_COOKIE_HTTPONLY=True`、`REMEMBER_COOKIE_SAMESITE="Lax"`。库不自动强制 `*_COOKIE_SECURE`，生产必须显式开启：

```python
from datetime import timedelta

app.config.update(
    SESSION_COOKIE_SECURE=True,
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
    REMEMBER_COOKIE_SECURE=True,
    REMEMBER_COOKIE_HTTPONLY=True,
    REMEMBER_COOKIE_SAMESITE="Lax",
    PERMANENT_SESSION_LIFETIME=timedelta(hours=12),
    SECURITY_REQUIRE_HTTPS=True,
)
```

注意：

- `SECURITY_REQUIRE_HTTPS=True` 会在启动时校验两个 `*_COOKIE_SECURE`；未开启直接抛 `RuntimeError`。
- 默认不强制 `Secure` 是为了让本地 HTTP 开发和测试继续可用；生产遗漏该配置仍会让会话经明文传输。
- Flask 的 `None` 同时表示“未配置”和“不输出 SameSite”，因此库把 `None` 视为未配置。确需跨站 Cookie 时写字符串 `"None"` 并配合 `Secure=True`；它会输出 `SameSite=None`。
- 需要完全保留 Flask 原 Cookie 行为时设置 `SECURITY_COOKIE_DEFAULTS_ENABLED=False`，库不再改任何 Cookie 配置。
- 反向代理要正确传递 `X-Forwarded-Proto` 并在应用上安装 `werkzeug.middleware.proxy_fix.ProxyFix`，否则 `Secure` Cookie 与 HSTS 判断可能不生效。

### 3.4 登出与 TFA 残留

`logout` 会清理：

- `_user_id`（Flask-Login）
- `SESSION_KEY_TFA_VERIFIED`
- `SESSION_KEY_TFA_RECOVERY`
- `SESSION_KEY_PENDING_TFA_REBIND_SECRET`
- `SESSION_KEY_PENDING_TFA_USER_ID`
- `_pending_tfa_remember`

目的：登出后不能恢复半完成的 TFA 登录，也不能残留 rebind 状态。

### 3.5 账号激活与邮箱验证

- `User._is_active` 默认 `True`；新注册用户**默认激活**。
- `is_active` 是**管理禁用标记**，`email_verified` 是邮箱验证状态，两者独立：未验证邮箱不会阻止登录。
- 未验证用户仍可登录、查看资料、修改密码；但 `ResetPassword` 要求 `email_verified=True`。
- `is_active=False` 的账号登录时被拒绝，不会建立新会话；若禁用发生在 TFA 过程中，pending 状态会被清理。既有会话在下一次请求时由 `user_loader` 判定为匿名，并清除 `_user_id` 与 remember-me Cookie；重新启用账号后仍需重新登录。
- `status`、`expired_at` 字段存在，但当前未见业务逻辑使用。

## 4. 授权

### 4.1 授权入口

```text
View 方法
  └─ ViewMeta 包装
       └─ self.allow(...)
            └─ Admin.allow / current_security.authorize_allow(...)
                 └─ Authorizer.allow(...)
                      ├─ 已登录且 active 的 admin：直接放行
                      ├─ allow_access=True：只查 login_required_functions
                      │    └─ 匿名 + 方法已列出 → 拒绝（403）
                      ├─ allow_access=False：未登录 → 拒绝
                      └─ 其他已登录用户：is_active、requirement 或 role_need
```

### 4.2 共用登录门与判定顺序

登录门定义在基类 `Authorizer.check_view_access()`，`SimpleAuthorizer` 与 `RBACAuthorizer` 都必须先调用它，再执行各自的角色回退或 requirement 判定；不得在子类重复实现：

```python
def check_view_access(self, user, view, fn=None):
    if view is None:
        return None

    authenticated = bool(getattr(user, "is_authenticated", False))

    if authenticated and getattr(user, "is_active", True):
        get_roles = getattr(user, "get_roles", None)
        if callable(get_roles) and "admin" in get_roles():
            # admin 是超级用户：直接放行，不执行 requirement
            return True

    if getattr(view, "allow_access", False):
        # 公开视图：只拦截 login_required_functions 中列出的方法
        return not (self.requires_login(view, fn) and not authenticated)

    # 非公开视图：所有方法都要求已登录
    return None if authenticated else False
```

返回值为三态：

- `False`：拒绝，调用方直接返回 `False`（403）。
- `True`：active `admin` 或公开视图放行，无需再查角色或 requirement。
- `None`：没有视图级结论，调用方继续自己的判定。

`SimpleAuthorizer` 在登录门之后只剩角色回退：

```python
def allow(self, *args, **kwargs):
    user = kwargs.get("user")
    decision = self.check_view_access(user, kwargs.get("view"), kwargs.get("fn"))
    if decision is not None:
        return decision

    # 无视图：跳过视图级判定，按角色回退（API 用法）
    return self.allow_by_roles(**{**kwargs, "user": user})
```

`RBACAuthorizer` 在登录门之后依次检查 `is_active`、视图声明的 requirement，最后回退到 `allow_by_roles()`；`allow_access=True` 的公开视图同样在登录门处直接放行，不进入 requirement 判定。

`allow_by_roles()` 按顺序判定：

```python
if not getattr(user, "is_active", True):
    return False
if "admin" in user.get_roles():
    return True
if "role_need" in kwargs and kwargs["role_need"] in user.get_roles():
    return True
return False
```

`admin` 是共用登录门的超级用户：已登录且 active 的 `admin` 在 `check_view_access()` 中直接返回 `True`，不进入任何 authorizer 的 requirement 判定；inactive 的 `admin` 不走该捷径，仍由后续 `is_active` 检查拒绝。`role_need` 回退保持原样。该捷径只读取用户对象的 `get_roles()`；`role_loader`、`permission_loader`、`user_data_loader` 与 `Predicate` 不参与该判断，也不会因 admin 获得额外处理。

### 4.3 判定结果与风险

- **匿名 + 普通视图（`allow_access=False`）**
  - 结果：拒绝 → 403
  - 说明：非公开视图先要求登录，再执行角色判定；默认拒绝

- **匿名 + 公开视图（`allow_access=True`）**
  - 结果：放行
  - 说明：登录/注册/门户等公开端点；若方法列入 `login_required_functions`，则拒绝 → 403

- **匿名 + `login_required_functions` 中的方法**
  - 结果：拒绝 → 403
  - 说明：只在 `allow_access=True` 的视图上有意义；不再重定向登录

- **已登录 + 公开视图**
  - 结果：放行
  - 说明：公开视图不要求角色

- **view 为空**
  - 结果：不做视图级登录/公开判定，按 `is_active` 与角色规则回退
  - 说明：`View.allow()` 总会传入 view；该分支仅用于直接调用 `authorize_allow()` 的 API 场景

- **普通用户 + 无角色**
  - 结果：拒绝
  - 说明：默认拒绝

- **普通用户 + `role_need` 匹配**
  - 结果：放行
  - 说明：需 active

- **`admin` + inactive**
  - 结果：**拒绝**
  - 说明：先检查 `is_active`，再判断 `admin`

- `admin` + 任意视图（active）
  - 结果：放行
  - 说明：高权限，需重点保护

- `admin` + `Permission` requirement（active）
  - 结果：放行
  - 说明：在共用登录门直接放行，不执行 requirement

- 非 `admin` 用户 + 缺少声明的权限
  - 结果：拒绝
  - 说明：`Permission` 按已加载的权限名判定

**SEC-01（高，已在 0.4.2 修复）**：`0.4.2` 已把 `is_active` 检查移到 `admin` 角色判断之前；`is_active=False` 的管理员访问 Admin 返回 403，公开 `allow_access` 视图行为不变。回归测试见 `tests/unit/security/test_simple_authorizer.py::test_deny_inactive_admin_user` 与 `tests/integration/admin/test_admin.py::test_inactive_admin_is_denied`。

对已发布的 0.4.1 及更早版本，仍需按第 0.3 节执行临时阻断：禁用管理员时**同时移除 admin 角色**或删除账号。

### 4.4 公开视图与禁用账号

`UserView.allow_access = True` 让登录/注册等公开端点可匿名访问；账号功能通过 `login_required_functions` 声明：

```python
class UserView(View):
    allow_access = True
    login_required_functions = ("profile", "change_password", ...)

    @expose_url("/change_password/", methods=("GET", "POST"))
    def change_password(self): ...
```

匿名请求这些方法时授权器直接拒绝，视图返回 403。`allow_access = False` 的视图不需要声明；所有方法本来就要求登录。`login_required_functions` 只接受已用 `expose_url` 暴露的方法名；未知名称在视图实例化时抛 `ValueError`，避免拼写错误导致静默放行。

`is_active=False` 的账号无法登录（`REQ-AUTH-009`），既有会话在下一次请求由 `user_loader` 失效（`REQ-AUTH-010`），因此授权器不会收到已认证的禁用用户。未验证邮箱（`email_verified=False`）的账号本身是 active，可登录并使用资料页重发验证邮件。

### 4.5 Admin 视图

> View/ModelView 的路由与配置见 [`spec.md` 第 10 章](./spec.md#10-view-与-admin-专题)；本节只讨论访问控制。

- `Admin` 默认 URL：`/admin`。
- 模型视图默认 `allow_access=False`。
- 匿名访问 `/admin/author/` 默认返回 **403**，不是登录重定向；需要登录要求时把方法名加入 `login_required_functions`，结果仍是 403。若需要跳转登录页，覆盖视图的 `inaccessible_callback`。
- `/admin/` 门户由 `PortalExtension.IndexView` 提供，`allow_access=True`，匿名可访问；不要把它误认为“后台已公开”。
- Admin 视图的 `can_create`/`can_edit`/`can_delete` 是**视图级功能开关**，不是用户授权；用户授权仍由 `SimpleAuthorizer` 决定。

### 4.6 可选 `RBACAuthorizer`

`RBACAuthorizer` 是移植自 Flask-RPBAC 的 requirement 授权器，在共用登录门之后按视图声明判定，能力比 `SimpleAuthorizer` 更强；默认授权器仍是 `SimpleAuthorizer`，只有显式配置才启用。用户使用说明见 `flask-exts/docs/advanced/authorization.rst`。

启用方式：

```python
app.config["SECURITY_AUTHORIZER"] = "rbac"
```

`Registry._create_authorizer()` 只接受 `"simple"`（默认）与 `"rbac"`；其他值在安全扩展初始化时抛 `ValueError`，不会静默回退到默认授权器。

#### 4.6.1 requirement 模型

requirement 在 `BuildContext` 上求值；上下文包含 `user`、`roles`、`permissions`、`kwargs`、`view`、`fn` 和单次检查内共享的 `pstore`。

- `Role(*names, match="any")`
  - 默认 `match="any"`，命中任一角色即通过。
  - `match="all"` 要求全部角色。
  - 无参数抛 `ValueError`，未知 `match` 抛 `ValueError`。
- `Permission(*names, match="all")`
  - 默认 `match="all"`，要求全部权限。
  - `match="any"` 命中任一权限即通过。
  - 无参数或未知 `match` 抛 `ValueError`。
- `Predicate(func)`
  - `func` 接收 `BuildContext`，返回 truthy 即通过。
  - 用于对象级判断，例如比较 `ctx.view.ticket_owner_id` 与 `ctx.user.id`。
  - 非 callable 抛 `TypeError`。
- `All(*requirements)`：全部子 requirement 通过才通过。
- `Any(*requirements)`：任一子 requirement 通过即通过。
- `Not(*requirements)`：所有子 requirement 都不通过才通过。
- `&` 与 `|`：分别是 `All` 与 `Any` 的语法糖。
- `Authenticated()`：`user.is_authenticated` 为真即通过。

requirement 只读取上下文中已加载的 roles/permissions 和传入数据，不会修改角色或权限集合；`admin` 超级权限在 `Authorizer.check_view_access()` 中先于 requirement 执行，loader 与 `Predicate` 不额外识别 admin。

#### 4.6.2 视图声明

requirement 直接声明在视图类上，不使用路由装饰器：

```python
class TicketView(ModelView):
    permission = All(Role("editor"), Predicate(owns_ticket))
    permissions = {"delete": Permission("ticket:delete")}
    roles = ("admin", "support")
```

判定优先级：

1. `permissions[fn.__name__]`：方法级覆盖，仅在提供 `fn` 且映射包含该方法名时生效。
2. `permission`：整个视图的默认 requirement。
3. `roles`：转换为 `Role(*roles)`。
4. `allow_by_roles()`：视图未声明任何 requirement 时，保留 `admin`/`role_need` 回退。

补充规则：

- 字符串是 `Role` 的简写，例如 `permission = "admin"` 等价于 `Role("admin")`。
- 不支持的声明类型抛 `TypeError`，不会静默放行。
- `allow_access = True` 的公开视图在登录门处直接放行，不执行上述 requirement。

#### 4.6.3 身份数据来源

roles/permissions 按以下优先级加载：

1. `user_data_loader`：返回 `{"roles": [...], "permissions": [...]}` 的 callable，优先级最高。
2. `role_loader` 与 `permission_loader`：分别返回当前用户的角色名与权限名。
3. 用户对象的 `get_roles()` 与 `get_permissions()`。
4. 都没有时为空集合，requirement 按失败处理。

loader 属于应用代码，其返回值必须来自可信身份存储，不能直接由请求参数拼接。

#### 4.6.4 判定顺序与兼容性

`RBACAuthorizer.allow()` 的顺序：

1. 调用 `Authorizer.check_view_access()`；匿名访问非公开视图或受限公开方法在此拒绝，已登录且 active 的 `admin` 在此直接放行。
2. `allow_access=True` 的公开视图直接放行。
3. 已登录的非公开视图先检查 `is_active`；禁用用户拒绝。
4. 解析并执行视图 requirement；未声明 requirement 时回退 `allow_by_roles()`。
5. `view` 为空时跳过视图级判定，直接回退 `allow_by_roles()`。

因此：

- `admin`、`role_need` 的既有行为保持兼容。
- `admin` 在共用登录门直接放行，不执行视图 requirement。
- `is_active=False` 不能靠 requirement 通过。
- 公开视图不会因为声明了 `permission` 而变成受保护页面；需要保护时不要设置 `allow_access=True`。
- `can()`、`has_role()`、`has_permission()`、`build_context()` 只是查询辅助方法，不执行登录门与 `is_active` 检查，也不包含 `admin` 超级用户捷径；用它们决定请求是否放行时，调用方必须自行补上这些检查。

行为契约见 `REQ-AUTHZ-007`～`REQ-AUTHZ-009`；回归测试见 `tests/unit/security/test_rbac_authorizer.py`。

## 5. 密码与凭据

### 5.1 密码哈希

```python
class UserMixin(FlaskLoginUserMixin):
    def hash_password(self, password):
        return generate_password_hash(password, method="scrypt")

    def check_password(self, password):
        return check_password_hash(self.password, password)
```

- 使用 Werkzeug 的 `scrypt`。
- `SqlaUserStore.login_user_by_username_password` 对不存在用户执行 dummy scrypt 校验，降低时间枚举。
- 密码哈希参数未暴露为配置项；升级/调参需改代码。

### 5.2 表单密码策略

- **注册**：密码 8–50；重复密码必须一致；用户名 6–50
- **修改密码**：旧密码 3–50；新密码 8–50；重复一致
- **重置密码**：新密码 8–50；重复一致
- **改邮箱**：当前密码 3–50
- **登录**：仅 `DataRequired`，无长度限制

**缺口（SEC-06，中；基于 2026-11-07 快照，当前未复核）**：

- 快照未见常见或泄露密码阻断。仅当密码验证器适用 [README.md 第 5 节登记的 NIST SP 800-63B-4 §3.1.1](./README.md#5-单一事实源) 时，该规范才要求在设定或修改密码时阻断完整密码命中清单。
- 未要求大小写、数字、符号组合本身不应自动判为缺陷；对上述 NIST 适用范围，规范不允许额外的字符组合规则。其他项目按自身适用的政策评估。
- 快照未见密码历史/复用限制；是否需要由项目适用政策决定，不作为通用默认要求。
- 直接调用 `current_userstore.create_user(password=...)` 可绕过表单长度限制。
- 邮箱格式校验问题单独见 SEC-05。

建议：

- 先确认适用标准和部署范围；按适用要求评估密码长度、完整密码阻断及认证尝试限流，不把字符组合规则当作默认控制。
- 采用 Have I Been Pwned 等外部检查前，评估网络依赖与隐私影响；不要默认引入第三方服务。
- 管理员优先启用 TFA；额外密码长度要求应记录风险依据。

### 5.3 密码变更与会话失效

- 修改密码后，`get_id()` 的指纹变化 → 旧 session 失效（已有测试）。
- JWT 载荷包含 `pwd` 指纹；修改密码或重置密码后，`load_user_from_request` 会拒绝旧 JWT（工作树修复，未发布；0.4.2 及更早版本仍有效到过期）。
- 重置密码同样改变密码哈希 → 旧 session 失效；工作树中的旧 JWT 同样失效。

建议：

- 高安全场景缩短 JWT 有效期；已签发 token 的主动吊销仍需 `jti` 或撤销列表。
- 在密码变更后要求重新登录所有设备（工作树中 JWT 已随密码变化失效）。

## 6. 令牌与邮件流程

### 6.1 令牌类型

- **邮箱验证**
  - serializer：`verify_email`
  - 邮件 `type`：`verify_email`
  - 链接字段：`verification_link`
  - 令牌字段：`verification_token`
  - 默认有效期：7 天

- **改邮箱**
  - serializer：`change_email`
  - 邮件 `type`：`verify_email`
  - 链接字段：`verification_link`
  - 令牌字段：`verification_token`
  - 默认有效期：7 天

- **重置密码**
  - serializer：`reset_password`
  - 邮件 `type`：`reset_password`
  - 链接字段：`reset_password_link`
  - 令牌字段：`reset_password_token`
  - 默认有效期：30 分钟

`get_within()`：

```python
_DEFAULT_MAX_AGES = {
    "reset_password": 1800,
    "verify_email": 86400 * 7,
    "change_email": 86400 * 7,
}
default_max_age = _DEFAULT_MAX_AGES.get(serializer_name, 1800)
return self.app.config.get(f"{serializer_name.upper()}_MAX_AGE", default_max_age)
```

可覆盖配置：`RESET_PASSWORD_MAX_AGE`、`VERIFY_EMAIL_MAX_AGE`、`CHANGE_EMAIL_MAX_AGE`。未知 serializer 使用 1800 秒的保守默认值，不继承 7 天。

### 6.2 令牌载荷与失效条件

`EmailVerification`/`ResetPassword` 的令牌载荷：

```python
(
    str(user.id),
    hasher.hash(user.email),
    hasher.hash(user.password or ""),
)
```

`EmailChange` 额外包含新邮箱：

```python
(
    str(user.id),
    hasher.hash(user.email),
    hasher.hash(user.password or ""),
    new_email,
)
```

失效条件：

- 超过最大年龄 → `ExpiredTokenError`（`expired`）
- 签名无效/篡改 → `InvalidTokenError`（`invalid_token`）
- 载荷长度不对/类型不对 → `InvalidTokenError`
- 用户不存在 → `TokenUserNotFoundError`（`no_user`）
- 邮箱哈希不匹配（邮箱已变）→ `InvalidTokenError`
- 密码哈希不匹配（密码已变）→ `InvalidTokenError`

因此：

- 重置密码令牌在密码修改后立即失效（一次性）。
- 改邮箱令牌在邮箱或密码变化后失效。
- 邮箱验证令牌在验证后再次使用会返回 `already_verified`（不重复生效）。

### 6.3 邮箱验证与登录门禁

- 注册成功后发验证邮件；`SecurityExtension` 订阅 `user_registered`。
- 验证邮箱只设置 `email_verified=True` / `email_verified_at`，**不修改 `is_active`**。
- 未验证邮箱**不阻止登录**；这是当前设计取舍。
- 找回密码只对 `email_verified=True` 的用户发送重置令牌；未验证用户无法通过邮箱重置密码。
- `resend_verification` 需要登录，但不要求 active；被禁用账号可在资料页重发。

### 6.4 改邮箱

- 表单要求当前密码（`EmailChangeForm.validate`）。
- 向**新邮箱**发送确认链接，`type` 仍为 `verify_email`。
- 点击确认后：检查旧邮箱/密码哈希、检查新邮箱是否已被占用、更新邮箱并标记 `email_verified=True`。
- 确认前旧邮箱保持有效；不会出现“未确认就切换”的窗口。

### 6.5 找回密码

- 无论邮箱是否存在，页面都显示同一句“已发送”，降低枚举。
- 只有存在且 `email_verified=True` 的用户才会真正收到邮件（当前不额外检查 `is_active`）。
- 重置令牌要求 `email_verified=True`；未验证用户会收到 `email_not_verified` 错误状态。
- 重置成功后旧密码立即失效；旧令牌因密码哈希变化而失效。

### 6.6 邮件枚举与令牌泄露

**枚举（SEC-10，低-中）**：

- 登录失败统一提示（好）。
- 找回密码统一提示（好）。
- 注册/改邮箱的重复检查会提示 `Email already exists.`（可枚举）。
- 注册用户名重复也会提示（可枚举）。

**令牌在 URL 中（SEC-09，低-中）**：

- 验证/重置链接使用 query string（`?token=...`），可能进入浏览器历史、Referer、代理日志。
- 当前只有 TFA 设置/恢复码页面设置 `NO_CACHE_HEADER`；邮件令牌结果页未统一设置 no-cache。
- 建议：反向代理配置 `Referrer-Policy: no-referrer`，日志脱敏，缩短令牌 TTL，避免第三方资源加载。

### 6.7 SMTP 安全

`SmtpSSL` 使用 `smtplib.SMTP_SSL`：

- `SmtpSSL` 显式传入 `ssl.create_default_context()`，启用证书链与主机名校验（`CERT_REQUIRED`、`check_hostname=True`），默认使用 Python/系统 CA 存储。私有 CA 通过 `SSL_CERT_FILE`、`SSL_CERT_DIR` 或系统信任库配置，不要关闭校验。
- TLS 握手失败会包装为 `SmtpError`，`__cause__` 保留 `ssl.SSLCertVerificationError`；`test_smtp_ssl_sends_over_a_verified_context` 与 `test_smtp_ssl_wraps_tls_failures` 覆盖。
- 使用 `NOREPLY_EMAIL_SENDER` 中的 `host/port/user/password`。
- 不要在代码/仓库中硬编码 SMTP 凭据。
- `send_email` 找不到 sender 时只记录 sender 类型与脱敏收件人（如 `a***@example.com`），不记录链接或令牌（SEC-18 已在 0.4.2 修复）。
- 建议：使用专用发信账号、最小权限、密钥轮换与发送量监控。

## 7. CSRF 与浏览器安全

### 7.1 CSRF 机制

```python
csrf_field_name = current_app.config.get("CSRF_FIELD_NAME", "csrf_token")
if csrf_field_name not in session:
    session[csrf_field_name] = secrets.token_urlsafe(32)

csrf_secret_key = csrf_key(current_app.secret_key, current_app.config)
s = URLSafeTimedSerializer(csrf_secret_key, salt=CSRF_SALT)
csrf_token = s.dumps(session[csrf_field_name])
```

session 内的 token 使用 CSPRNG（`secrets.token_urlsafe(32)`）生成，不使用哈希函数模拟随机数。

校验：

- 从表单/ JSON 取 `csrf_token`
- 用同一派生密钥和 salt 解析
- 检查最大年龄（默认 1800 秒）
- `hmac.compare_digest(session token, token)` 防时序攻击

### 7.2 配置

- `CSRF_ENABLED`
  - 默认：`True`
  - 安全建议：生产保持 `True`

- `CSRF_SECRET_KEY`
  - 默认：派生
  - 安全建议：可选独立密钥；轮换会使现有 token 失效

- `CSRF_FIELD_NAME`
  - 默认：`csrf_token`
  - 安全建议：不要随意改名，前后端需一致

- `CSRF_TIME_LIMIT`
  - 默认：`1800`
  - 安全建议：按业务调整；越长暴露窗口越大

> 测试 `tests/conftest.py` 默认 `CSRF_ENABLED=False`，仅用于简化测试；不要把测试配置带到生产。

### 7.3 JSON / AJAX

- `FlaskMeta.wrap_formdata` 支持 `request.form`、`request.files`、JSON。
- 前端从 `<meta name="csrf-token">` 读取 token，AJAX 请求以 `csrf_token` 字段提交。
- `editable.js`、`form.js` 已处理 CSRF 字段；自定义 AJAX 必须显式带上 token。
- 登出是 `GET /user/logout/`，未加 CSRF；影响通常仅为“强制登出”（低），但高安全场景可改为带 CSRF 的 POST。

### 7.4 Cookie 与安全响应头

库在初始化 `SecurityExtension` 时默认下发以下响应头，应用可通过 `SECURITY_HEADERS` 覆盖，或用 `SECURITY_HEADERS_ENABLED=False` 关闭：

- `X-Content-Type-Options`：`nosniff`
- `X-Frame-Options`：`SAMEORIGIN`
- `Referrer-Policy`：`strict-origin-when-cross-origin`
- `Permissions-Policy`：`geolocation=(), microphone=(), camera=()`
- `Content-Security-Policy`：`frame-ancestors 'self'`

HTTPS 请求额外下发：

- `Strict-Transport-Security`：`max-age=31536000; includeSubDomains`（确认全站 HTTPS 后；可用 `SECURITY_HSTS_ENABLED=False` 关闭，或用 `SECURITY_HSTS` 改值）

注意：

- HSTS 依赖 `request.is_secure`。TLS 在反向代理终止时，必须在应用安装 `werkzeug.middleware.proxy_fix.ProxyFix` 并只信任已知代理，否则请求被视为 HTTP，HSTS 静默不下发。
- `SECURITY_HEADERS` 必须是 mapping，键为非空字符串，值为字符串或 `None`；`SECURITY_HSTS` 必须是字符串或 `None`。类型错误在启动时抛 `RuntimeError`，不会留到每个请求。
- 应用仍应按实际资源收紧 `script-src`/`style-src` 等 CSP 指令；默认策略只限制页面被嵌入，不限制脚本与样式。

### 7.5 开放重定向防护

```python
def safe_redirect_target(target, fallback):
    if not target or target.startswith("//") or target[0].isspace() or "\\" in target:
        return fallback
    parsed = urlsplit(target)
    decoded_path = unquote(parsed.path)
    if (
        parsed.scheme
        or parsed.netloc
        or not parsed.path.startswith("/")
        or parsed.path.startswith("//")
        or decoded_path.startswith("//")
        or "\\" in decoded_path
    ):
        return fallback
    return target
```

已拒绝：

- 绝对 URL（`https://...`）
- 协议相对 URL（`//...`、`///...`）
- 反斜杠变体（`/\...`）
- 编码后的 `//`（`/%2f%2f...`）
- 畸形 URL（`http://[`）
- 首字符空白

使用位置：登录 `next`、TFA `next`、恢复码 `next`。

### 7.6 XSS 注意事项

- Jinja 默认自动转义；不要对用户输入使用 `|safe`。
- `Markup` 会绕过转义；例如 demo 的 `phone_number_formatter` 使用 `Markup` 包裹格式化后的电话号码。新增 formatter 时确认数据来源可信，或显式转义。
- 内置 `bool_formatter` 会把列名插入 `title` 属性；该值已用 `markupsafe.escape()` 转义，避免列名注入 HTML。自定义 formatter 同样不能直接拼接未转义的值。
- 富文本字段若允许 HTML，需要单独的白名单清洗（当前库不提供）。

## 8. 双因素认证（TFA）

### 8.1 TOTP secret 加密存储

```python
def get_or_create_totp_secret(self):
    if self.totp_secret is None:
        plaintext = tfa.generate_totp_secret()
        self.totp_secret = current_security.encryptor.encrypt(plaintext)
        db.session.flush()
        return plaintext
    return self.get_totp_secret()

def get_totp_secret(self):
    if self.totp_secret is None:
        return None
    return current_security.encryptor.decrypt(self.totp_secret)
```

- 模型只 `flush()` 把变更写入当前事务，不自行 `commit()`；`setup_tfa` 等服务层通过 `current_userstore.save_user()` 提交，保持事务边界在服务层。
- 使用 AES-256-GCM；每次加密使用随机 nonce，密文为 `nonce || ciphertext` 的 URL-safe base64。
- 数据库泄露时，攻击者不能直接读取 TOTP secret。
- 但 `SECRET_KEY` 泄露或轮换会影响解密（见 10.4）。

### 8.2 启用 / 关闭 / 重绑

- `setup_tfa`
  - 要求：登录 + active
  - 说明：生成/返回 TOTP secret 与 provisioning URI；页面 no-cache

- `enable_tfa`
  - 要求：登录 + active + 有效 TOTP
  - 说明：启用后设置 `SESSION_KEY_TFA_VERIFIED=True`

- **关闭 TFA**
  - 要求：登录 + active + 有效 TOTP
  - 说明：清空 `totp_secret` 与 TFA session 标记

- `rebind_tfa`
  - 要求：登录 + active + `tfa_verified` + `tfa_recovery`
  - 说明：用于恢复码登录后重新绑定 authenticator

- `recovery_codes`
  - 要求：登录 + active + `tfa_verified`
  - 说明：生成并展示一次恢复码；数据库只存哈希

注意：

- 启用/关闭 TFA 需要当前 TOTP 验证码，但**不要求重新输入密码**。
- 关闭 TFA 会同时清空 `totp_secret` 与 `recovery_codes`；重新启用后必须重新生成恢复码（SEC-16）。
- `rebind_tfa` 的 pending secret 在 session 中加密保存；重绑成功会清空未使用的恢复码，需要重新生成。

### 8.3 登录时的 TFA

- 密码正确且 `tfa_enabled=True` → 只写 `pending_tfa_user_id`，**不建立登录会话**。
- `/user/verify_tfa/` 故意不列入 `login_required_functions`；它靠 session 中的 pending id 识别用户。
- 验证通过后才 `login_user`，并清理 pending 状态。
- 恢复码登录同样完成第二因子，并消耗一个恢复码。
- 登出清理所有 TFA 相关 session key。

### 8.4 TFA 缺口

- **JWT 绕过 TFA**（工作树已修复，未发布）
  - 等级：高（启用 JWT 时）
  - 说明：`load_user_from_request` 要求 TFA 用户的 `amr` 含 `otp`（SEC-02）；0.4.2 及更早版本仍只检查 active

- **无限流/锁定**
  - 等级：高（公网）
  - 说明：6 位 TOTP 可被在线暴力尝试；`0.4.2` 已加入内置失败锁定，仍缺注册/找回入口限流与验证码（SEC-03）

- **无 TOTP 重放防护**
  - 等级：低-中
  - 说明：同一 30 秒窗口内验证码可重复使用；pyotp 默认窗口

建议：

- JWT 载荷已包含 `amr`；`load_user_from_request` 对 TFA 用户强制要求 `otp`（工作树，未发布）。
- 在反向代理/WAF 对登录/TFA/恢复码接口限流，与内置账号锁定叠加。
- 评估 TOTP `valid_window` 与重放缓存。

### 8.5 失败登录锁定（v0.4.1 之后）

`main` 在 `users` 表上新增两个字段，并在 `SqlaUserStore` 中实现账号级失败计数：

- `failed_login_count`
  - 类型：`int NOT NULL DEFAULT 0`
  - 作用：连续失败次数，密码错误与第二因子错误共用

- `locked_until`
  - 类型：`timestamp NULL`（UTC）
  - 作用：锁定截止时间，过期后自动恢复

行为：

- 失败达到 `USER_LOGIN_MAX_FAILURES`（默认 5）后开始锁定，延迟从 `USER_LOGIN_LOCKOUT_BASE_SECONDS`（默认 60 秒）起按 2 的幂增长，上限 `USER_LOGIN_LOCKOUT_MAX_SECONDS`（默认 3600 秒）。
- 锁定期间密码校验不会执行，登录页返回剩余等待时间。
- 锁定的账号无法继续进行 pending TFA 校验；`_get_pending_tfa_user` 会清理 pending 状态。
- 只有完整登录成功（密码，或密码 + 第二因子）或成功重置密码才清零计数；仅密码正确不会清零。
- 锁定状态与 `is_active` 分离：前者自动过期，后者是管理员禁用。
- 计数存在数据库中，因此与客户端 IP 无关，并在共享同一数据库的多进程/多实例间一致。
- `locked_until` 与用户模型的其他时间列统一使用 UTC；无时区数据库保存 UTC wall time，读出为 aware UTC。历史行若写入的是本地 naive 时间，升级后会被按 UTC 解释，需要按原部署时区迁移。

未覆盖的部分：

- 未知用户名的尝试无法计数（没有用户行），仍需反向代理按 IP 限流。
- 注册、找回密码、重发验证邮件没有应用层计数，仍需反向代理限流。
- 锁定提示会暴露“该账号存在且被锁定”；当前注册表单本身已可枚举用户名（SEC-10），因此未额外增加泄漏面。

管理员解锁：

```python
current_userstore.user_set(user, failed_login_count=0, locked_until=None)
```

## 9. JWT / API 认证

### 9.1 配置与令牌

```python
def jwt_encode_for_user(user, amr=None, delta=None):
    methods = _normalize_amr(amr)          # 字符串视为单个方法；元素必须是 str
    if "pwd" not in methods:
        methods.insert(0, "pwd")
    if user.tfa_enabled and "otp" not in methods:
        raise ValueError("otp amr claim required")
    return jwt_encode(
        {
            "id": user.id,
            "pwd": current_security.hasher.hash(user.password or ""),
            "amr": methods,
        },
        delta=delta,
    )
```

- 默认有效期 900 秒；`jwt_encode` 写入 `iat`、`exp`、`token_use`。
- `jwt_decode` 要求 `exp`/`iat`/`token_use`，并通过 `JWT_LEEWAY` 容忍多实例时钟偏差（默认 `0`）；缺少 `iat` 的旧令牌会被拒绝。
- 访问令牌另含 `pwd` 与 `amr`；`pwd` 是 `Blake2bHasher` 的带密钥指纹，与 session 的 `get_id()` 同源。
- `amr` 至少含 `pwd`；完成 TOTP 或恢复码后含 `otp`。TFA 用户缺少 `otp` 时签发函数直接抛 `ValueError`。
- `amr` 参数只接受字符串或字符串可迭代对象；`amr="otp"` 视为单个方法，不再按字符拆分。
- `jwt_decode` 只接受白名单算法 `HS256`/`HS384`/`HS512`；配置 `none` 或其他算法直接抛 `RuntimeError`。
- `JWT_SECRET_KEY` 首次使用时校验：必须已设置、至少 32 字节、且不同于 `SECRET_KEY`。
- `Authorization: Bearer <token>`；auth-scheme 大小写不敏感（`bearer` 与 `Bearer` 均可）。

### 9.2 请求加载

```python
if "Authorization" in request.headers:
    payload = authorization_decoder(authstr)
    user = resolve_user(payload)          # id 或 identity
    if user is not None and user.is_active:
        if not compare_digest(payload["pwd"], hasher.hash(user.password or "")):
            return None
        if user.tfa_enabled and "otp" not in payload.get("amr", []):
            return None
        return user
```

安全点：

- 只接受 `Bearer`，拒绝 Basic；auth-scheme 大小写不敏感。
- 不读取 `api_key` 查询参数或其他请求参数；认证只来自 `Authorization` 头。
- 只接受 `token_use="access"`。
- 检查 `is_active`。
- `id` 只接受整数或纯十进制字符串；布尔、浮点和容器类型一律拒绝，避免 `True`/`1.9` 被当成用户 1。
- 恒定时间比对 `pwd` 指纹；缺失或类型错误一律拒绝。
- TFA 用户要求 `amr` 含 `otp`。

### 9.3 JWT 缺口

- **TFA 声明校验**（工作树已修复，未发布）
  - 等级：高（启用 JWT 时）
  - 说明：`load_user_from_request` 要求 TFA 用户的 `amr` 含 `otp`；纯密码 token 被拒（SEC-02）

- **密码变更失效**（工作树已修复，未发布）
  - 等级：中
  - 说明：JWT 携带 `pwd` 指纹；改密或重置后旧 token 被拒（SEC-08）

- **无撤销列表**
  - 等级：中
  - 说明：无法主动吊销单个 token；只能轮换 `JWT_SECRET_KEY`（全部失效）

- **无 audience/issuer**
  - 等级：中
  - 说明：多服务共享密钥时可能被跨服务重放

- **JWT 密钥配置校验**（工作树已修复，未发布）
  - 等级：低
  - 说明：首次使用 JWT 时校验 `JWT_SECRET_KEY` 已设置、至少 32 字节且不同于 `SECRET_KEY`；缺失或不合规会抛明确的 `RuntimeError`

- **算法配置**（工作树已修复，未发布）
  - 等级：低
  - 说明：`JWT_HASH` 只接受白名单 `HS256`/`HS384`/`HS512`；`none` 或其他算法直接失败，避免配置误用

建议：

- JWT 仅用于 API 场景，并明确 TFA 策略。
- 加入 `jti` + 撤销列表/短期 token + 刷新 token。
- 加入 `aud`/`iss` 校验。
- `pwd` 指纹已覆盖密码变更与重置；如需强制全体下线，再递增 `token_version` 并写入 JWT。
- 使用独立 `JWT_SECRET_KEY`，不要与 `SECRET_KEY` 相同。

## 10. 配置安全清单

### 10.1 必需配置

- `SECRET_KEY`
  - 要求：必填，强随机，并在 `Security.init_app()` 之前配置
  - 说明：派生会话/CSRF/令牌/加密密钥；缺失时初始化直接抛 `RuntimeError`

- `SQLALCHEMY_DATABASE_URI`
  - 要求：必填
  - 说明：数据库连接；生产使用受控账号

- `JWT_SECRET_KEY`
  - 要求：使用 JWT 时必填
  - 说明：独立于 `SECRET_KEY`

- `NOREPLY_EMAIL_SENDER`
  - 要求：使用邮件流程时必填
  - 说明：SMTP 配置；凭据放环境变量/密钥管理

### 10.2 推荐配置

- `CSRF_ENABLED`
  - 推荐值：`True`
  - 说明：生产保持开启

- `CSRF_SECRET_KEY`
  - 推荐值：独立随机值
  - 说明：可选；不设置则从 `SECRET_KEY` 派生

- `CSRF_TIME_LIMIT`
  - 推荐值：`1800`
  - 说明：按业务调整

- `RESET_PASSWORD_MAX_AGE`
  - 推荐值：`1800`
  - 说明：重置令牌 30 分钟

- `VERIFY_EMAIL_MAX_AGE`
  - 推荐值：短于 7 天
  - 说明：邮箱验证令牌

- `CHANGE_EMAIL_MAX_AGE`
  - 推荐值：短于 7 天
  - 说明：改邮箱令牌

- `JWT_ACCESS_TOKEN_MAX_AGE`
  - 推荐值：`900` 或更短
  - 说明：API token

- `JWT_LEEWAY`
  - 推荐值：`0`～`30` 秒
  - 说明：容忍多实例时钟偏差；不要放大到覆盖令牌寿命

- `JWT_HASH`
  - 推荐值：`HS256`（白名单 `HS256`/`HS384`/`HS512` 内的固定值）
  - 说明：不要动态接受用户输入；白名单外的值会直接失败

- `APP_NAME`
  - 推荐值：真实应用名
  - 说明：TOTP issuer

- `SECURITY_HEADERS_ENABLED`
  - 推荐值：`True`
  - 说明：关闭后不再下发默认安全响应头

- `SECURITY_HEADERS`
  - 推荐值：按应用覆盖；至少保留 `Content-Security-Policy: frame-ancestors 'self'`
  - 说明：与默认头合并；单项设为 `None` 可移除

- `SECURITY_HSTS_ENABLED` / `SECURITY_HSTS`
  - 推荐值：`True` / `max-age=31536000; includeSubDomains`
  - 说明：仅 HTTPS 请求下发；确认全站 HTTPS 后再启用

- `SECURITY_REQUIRE_HTTPS`
  - 推荐值：生产 `True`，本地开发/测试 `False`
  - 说明：为 `True` 时要求两个 `*_COOKIE_SECURE` 均为 `True`，否则启动失败

- `SECURITY_COOKIE_DEFAULTS_ENABLED`
  - 推荐值：`True`
  - 说明：设为 `False` 时保留 Flask 原 Cookie 配置，不再套用库的 HttpOnly/SameSite 默认值

- `SESSION_COOKIE_*` / `REMEMBER_COOKIE_*`
  - 推荐值：见 3.3
  - 说明：Secure/HttpOnly/SameSite；库默认 HttpOnly 与 SameSite=Lax，不默认 Secure；跨站需写字符串 `"None"`

### 10.3 禁止配置

- `SECRET_KEY = "demo"` / `"changeme"` / 空值
- 生产 `CSRF_ENABLED=False`
- `SESSION_COOKIE_SECURE=False`（HTTPS 环境）
- 把 `JWT_SECRET_KEY` 设为 `SECRET_KEY`
- 把 SMTP 密码、数据库密码写进仓库
- 使用 demo 的 `admin/admin`
- 给普通业务账号授予 `admin`

### 10.4 密钥轮换决策表

- **怀疑 `SECRET_KEY` 泄露**
  - 操作：轮换 `SECRET_KEY`
  - 影响：所有 session/CSRF/URL 令牌失效；TOTP secret 无法解密
  - 建议：先评估 TOTP 用户，准备重绑/重加密；强制全员重新登录

- **仅怀疑 CSRF 密钥**
  - 操作：轮换 `CSRF_SECRET_KEY`
  - 影响：现有 CSRF token 失效
  - 建议：低风险，可随时轮换

- **怀疑 JWT 密钥**
  - 操作：轮换 `JWT_SECRET_KEY`
  - 影响：所有 JWT 失效
  - 建议：通知 API 客户端重新登录

- **常规密钥轮换**
  - 操作：按周期轮换
  - 影响：同上
  - 建议：建立迁移/通知流程

### 10.5 生产反向代理配置参考（Nginx）

由于框架的账号级失败锁定（SEC-03，`0.4.2` 起）无法覆盖未知用户名、注册与找回密码入口，也没有 IP 维度，公网部署时生产环境的反向代理**必须承载 TLS 终止、安全请求头注入与认证端点限流**。以下为推荐配置片段：

```nginx
# 1. 定义认证端点专用的 IP 限流区域（单 IP 每秒最多 1 次，防止字典攻击）
limit_req_zone $binary_remote_addr zone=auth_limit:10m rate=1r/s;

server {
    listen 443 ssl http2;
    server_name example.com;

    ssl_certificate     /path/to/fullchain.pem;
    ssl_certificate_key /path/to/privkey.pem;

    # 2. 安全响应头基线
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;

    # 3. 对敏感认证端点强制启用突发与限流规则（SEC-03 防护）
    location ~ ^/user/(login|register|verify_tfa|recovery|forgot_password|reset_password)/ {
        limit_req zone=auth_limit burst=5 nodelay;
        limit_req_status 429;
        proxy_pass http://127.0.0.1:8000;

        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto https;  # 保证 Flask 识别 HTTPS，使 Secure Cookie 生效
    }

    # 4. 常规业务转发
    location / {
        proxy_pass http://127.0.0.1:8000;

        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto https;
    }
}
```

## 11. 已知风险与待决策

> 本轮已对照 HEAD `445b03d1fe6c59cd53405c8187de968c687a2909` 静态核实 SEC-01/02/05/17/18/19 的代码观察；其中 SEC-01、SEC-05、SEC-13、SEC-16、SEC-17、SEC-18 与 SEC-19 已在 `0.4.2` 修复，SEC-03 已加入账号级失败锁定（部分修复）；其余风险按各条现有证据边界标记。等级基于“公网 + 默认配置”假设，实际影响取决于部署；这不是完整安全审计或渗透测试。

- `SEC-01`
  - 等级：高（已在 0.4.2 修复）
  - 位置：`security/authorizer/simple_authorizer.py`
  - 现状：`is_active` 检查已移到 `admin` 角色判断之前；`test_deny_inactive_admin_user`、`test_inactive_admin_is_denied` 覆盖
  - 建议：已发布 0.4.1 及更早版本的部署仍需同时移除 admin 角色

- `SEC-02`
  - 等级：高（工作树修复，未发布）
  - 位置：`builtin_extensions/login_ext.py::load_user_from_request`
  - 现状：JWT 载荷含 `pwd` 与 `amr`；TFA 用户必须带 `otp` 声明；`test_tfa_user_requires_otp_claim` 覆盖 JWT 请求加载路径，专用令牌端点的完成态 TFA 用例待补
  - 建议：发布后按退役规则处理；0.4.2 及更早版本仍需网关二次验证

- `SEC-03`
  - 等级：高（部分修复，已在 0.4.2 发布）
  - 位置：登录/注册/找回/TFA/恢复码
  - 现状：`main` 已实现账号级失败锁定（`users.failed_login_count` + `locked_until`，密码与 TFA 共享计数、指数退避）；仍缺 IP 维度、未知用户名计数与注册/找回入口限流
  - 建议：反向代理/WAF 按 IP 限流，与内置账号锁定叠加

- `SEC-05`
  - 等级：中（已修复）
  - 位置：`usercenter/forms/register.py`
  - 现状：注册邮箱已使用 `DataRequired()` + `Email()` + `Length(max=254)`；`test_register_rejects_invalid_email` 覆盖非法格式且不创建用户
  - 建议：保持 `Email()` 与改邮箱表单一致；投递性检查默认关闭

- `SEC-06`
  - 等级：中
  - 位置：密码策略/表单
  - 现状：快照未见常见或泄露密码阻断；服务端 API 可绕过表单长度限制（当前未复核）
  - 建议：按适用标准评估阻断要求并统一校验；不默认要求字符组合

- `SEC-07`
  - 等级：中
  - 位置：`security/keys.py` + `encryptor`
  - 现状：轮换 `SECRET_KEY` 会使 TOTP secret 无法解密
  - 建议：提供重加密迁移或提前重绑

- `SEC-08`
  - 等级：中（工作树修复，未发布）
  - 位置：`login_ext.py`
  - 现状：JWT 携带 `pwd` 指纹；改密或重置后旧 token 被拒；`test_bearer_token_is_rejected_after_password_change` 覆盖
  - 建议：发布后按退役规则处理；主动吊销仍需 `jti` 或撤销列表

- `SEC-09`
  - 等级：低-中
  - 位置：邮件令牌
  - 现状：令牌在 URL query，可能进 Referer/日志
  - 建议：`Referrer-Policy: no-referrer`、日志脱敏、短 TTL

- `SEC-10`
  - 等级：低-中
  - 位置：注册/改邮箱
  - 现状：重复邮箱/用户名可枚举
  - 建议：统一提示或接受取舍并记录

- `SEC-11`
  - 等级：中
  - 位置：全局
  - 现状：无安全审计日志（登录失败、TFA 失败、密码变更、管理员操作）
  - 建议：接入结构化日志/审计系统

- `SEC-12`
  - 等级：中（工作树修复，未发布）
  - 位置：部署 / `SecurityExtension`
  - 现状：`SecurityExtension` 默认设置 HttpOnly 与 SameSite=Lax，并下发低风险安全响应头；`SECURITY_REQUIRE_HTTPS` 可在启动时强制 Secure Cookie；Cookie 默认值可用 `SECURITY_COOKIE_DEFAULTS_ENABLED=False` 关闭，响应头与 HSTS 配置在启动阶段做类型校验
  - 建议：生产显式开启 `SESSION_COOKIE_SECURE`/`REMEMBER_COOKIE_SECURE` 与 `SECURITY_REQUIRE_HTTPS`；反向代理安装 `ProxyFix`；发布后按退役规则处理

- `SEC-13`
  - 等级：低（已在 0.4.2 修复）
  - 位置：`user_view.py::recovery`
  - 现状：只接受 `hasher.verify` 的哈希校验，明文兼容分支已移除；`test_plaintext_recovery_codes_are_rejected` 覆盖
  - 建议：已发布版本仍接受明文兼容值

- `SEC-14`
  - 等级：低
  - 位置：用户模型
  - 现状：`status`、`expired_at` 字段未使用
  - 建议：实现或移除，避免误以为已生效

- `SEC-15`
  - 等级：信息
  - 位置：Admin 视图
  - 现状：匿名访问模型视图返回 403，不是登录重定向
  - 建议：需要登录要求时声明 `login_required_functions`；需要跳转登录页时覆盖 `inaccessible_callback`

- `SEC-16`
  - 等级：中（已在 0.4.2 修复）
  - 位置：`usercenter/user_view.py::enable_tfa`、`rebind_tfa`
  - 现状：关闭 TFA 与重绑 authenticator 均清空 `recovery_codes`；`test_tfa`、`test_recovery` 覆盖
  - 建议：已发布版本旧恢复码仍可能有效

- `SEC-17`
  - 等级：中-高（已在 0.4.2 修复）
  - 位置：`emailer/smtp.py::SmtpSSL`
  - 现状：显式传入 `ssl.create_default_context()`（`CERT_REQUIRED` + `check_hostname=True`）；TLS 失败包装与 context 开关均有测试覆盖
  - 建议：私有 CA 配置到信任库；监控发信失败率

- `SEC-18`
  - 等级：中（已在 0.4.2 修复）
  - 位置：`emailer/base.py::send_email`
  - 现状：找不到 sender 时只记录 `type` 与脱敏收件人，不输出链接/令牌；`test_missing_sender_warning_redacts_payload` 覆盖
  - 建议：已发布版本仍需限制日志访问并过滤敏感载荷

- `SEC-19`（旧别名 `V-01` 已废止）
  - 等级：中（已在 0.4.2 修复）
  - 位置：`admin/model/view.py::ajax_update`
  - 现状：`can_edit=False` 时返回 403；`test_ajax_update_requires_can_edit` 覆盖
  - 建议：已发布版本仍需将 `column_editable_list` 置空

## 12. 测试覆盖与缺口

### 12.1 现有安全相关测试

安全相关测试文件清单与本轮完整套件结果见 [`testing.md` 第 1 节](./testing.md#1-测试现状盘点)。全套测试通过不等同于每条安全风险均有针对性断言；具体覆盖仍按各测试用例和源码证据核实。

### 12.2 测试缺口

表单与 CSRF 场景见 [`testing.md` 第 7.4 节](./testing.md#74-forms)，加密、令牌、认证及安全风险相关测试场景见 [`testing.md` 第 7.5 节](./testing.md#75-security)。风险详情以本文第 11 节为准；风险编号不是测试编号，未分配 TC 或未执行的场景不能当作已覆盖。

### 12.3 运行安全相关测试

命令入口维护在 [`testing.md` 第 0.2 节](./testing.md#02-第一条命令)；应先核实仓库、环境和测试路径，再记录实际结果。

## 13. 安全运营与响应

### 13.1 密钥与配置管理

- 使用环境变量/密钥管理系统注入 `SECRET_KEY`、`JWT_SECRET_KEY`、SMTP 凭据。
- 不同环境使用不同密钥；不要复用开发/测试密钥。
- 限制配置读取权限；不要把 `.env` 提交到仓库。
- 记录密钥版本与轮换时间。

### 13.2 依赖与漏洞

- 定期运行依赖漏洞扫描（如 `pip-audit`，需新增工具）。
- 关注 `Flask`、`SQLAlchemy`、`cryptography`、`PyJWT`、`pyotp`、`itsdangerous`、`WTForms` 的安全公告。
- 升级前跑完整测试，尤其是安全相关用例。

### 13.3 日志与审计

当前没有内置安全审计日志。建议至少记录：

- 登录成功/失败（用户名、IP、时间、User-Agent）
- TFA 成功/失败/恢复码使用
- 密码修改/重置
- 邮箱变更
- Admin 登录与高危操作（删除、导出、批量操作）
- 密钥/配置变更

不要记录：密码、TOTP secret、恢复码、完整令牌、SMTP 密码。

### 13.4 备份与数据库

- 数据库备份加密；限制备份访问。
- 数据库账号最小权限；应用不要用超级用户。
- 生产不要使用 SQLite 文件作为唯一存储（并发/备份/权限限制）。
- 定期验证恢复流程。

### 13.5 事件响应（建议流程）

1. **确认范围**：账号接管、密钥泄露、数据库泄露、令牌泄露。
2. **遏制**：禁用账号（同时移除 admin 角色）、轮换相关密钥、封禁 IP。
3. **清除**：撤销 session/JWT；重置密码；重新绑定 TFA。
4. **恢复**：从干净备份恢复；监控异常登录。
5. **复盘**：记录时间线、根因、改进项；补测试与文档。

### 13.6 漏洞报告

仓库当前没有 `SECURITY.md`。建议增加：

- 私密报告渠道（邮件/安全平台）
- 支持版本范围
- 响应时限
- 披露政策

## 14. 发布前安全检查清单

### 14.1 配置

- [ ] `SECRET_KEY` 为强随机值，未使用 demo 值
- [ ] `JWT_SECRET_KEY` 独立且已设置（如使用 JWT）
- [ ] `CSRF_ENABLED=True`
- [ ] HTTPS 已启用，HSTS 已配置
- [ ] `SESSION_COOKIE_SECURE/HTTPONLY/SAMESITE` 已设置
- [ ] `REMEMBER_COOKIE_*` 已设置
- [ ] 数据库账号最小权限
- [ ] SMTP 凭据在密钥管理系统中
- [ ] SMTP 证书校验未被关闭（私有 CA 已加入信任库）

### 14.2 账号与权限

- [ ] 默认 `admin/admin` 已删除或改密
- [ ] 管理员启用 TFA
- [ ] 禁用管理员时已同时移除 `admin` 角色（规避 SEC-01）
- [ ] 普通用户没有 `admin` 角色
- [ ] 公开视图清单已评审（`allow_access=True`）

### 14.3 网络与限流

- [ ] 登录/注册/找回/TFA/恢复码在反向代理层有限流（`limit_req_status 429`）
- [ ] `USER_LOGIN_MAX_FAILURES` 与退避参数已按业务确认
- [ ] CDN/代理后的真实 IP 已配置（`set_real_ip_from` / `real_ip_header`），否则限流会命中错桶
- [ ] WAF/反向代理已配置
- [ ] 安全响应头已配置（CSP、HSTS、X-Frame-Options、nosniff、Referrer-Policy）
- [ ] 错误页不泄露堆栈/配置
- [ ] 日志已脱敏（无密码/令牌/TOTP secret）

### 14.4 数据与令牌

- [ ] 令牌 TTL 已评审（重置 30 分钟、验证/改邮箱 ≤7 天）
- [ ] 邮件链接使用 HTTPS
- [ ] 数据库备份加密且可恢复
- [ ] TOTP secret 加密存储已确认
- [ ] 恢复码只存哈希
- [ ] 密钥轮换流程已文档化（含 TOTP 迁移）

### 14.5 测试与监控

- [ ] 安全相关测试通过
- [ ] 新增安全用例覆盖本次改动
- [ ] 审计日志/告警已接入
- [ ] 依赖漏洞扫描已运行
- [ ] 已知风险（第 11 节）已评审并接受/修复
