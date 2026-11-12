# Flask-Exts 安全指南（Security）

> 本文是 Flask-Exts 的**安全单一事实源**：威胁模型、认证/授权、密码与令牌、CSRF、TFA、JWT、配置基线、已知风险、测试覆盖与发布前检查。
>
> | 项目 | 内容 |
> | --- | --- |
> | 文档版本 | v0.1 |
> | 状态 | 可用 |
> | 最后更新 | 2026-11-13 |
> | 数据快照 | 2026-11-13（发布版本 `0.4.2`；HEAD `445b03d1fe6c59cd53405c8187de968c687a2909`；内容核对基线 `171b40968f309c04ae3ad423696227c2767b0055`；`0.4.2` 已包含 SEC-01/SEC-05/SEC-13/SEC-16/SEC-17/SEC-18/SEC-19 修复，SEC-03 为部分修复） |
> | 适用仓库 | `flask-exts` |
> | 配套文档 | `architecture.md`（架构）、`spec.md`（设计/实现）、`requirements.md`（契约）、`testing.md`（测试）、`demo.md`（示例）；View/Admin 见 `spec.md` 第 10 章 |
>
> **重要说明**：本文选定风险已对照 HEAD `171b40968f309c04ae3ad423696227c2767b0055` 做静态源码核对；这不是完整安全审计或渗透测试，也不能证明运行配置、风险可利用性或修复已验证。标记为“风险/待决策”的内容仍需结合部署环境评估；代码修复须先评审、补测试，再实施。

## 目录

- [0. 快速安全基线](#0-快速安全基线)
  - [0.1 五条必须做到](#01-五条必须做到)
  - [0.2 五条不要做](#02-五条不要做)
  - [0.3 代码未修复时的临时配置阻断（Workarounds）](#03-代码未修复时的临时配置阻断workarounds)
- [1. 范围与威胁模型](#1-范围与威胁模型)
- [2. 安全架构与密钥](#2-安全架构与密钥)
- [3. 认证与会话](#3-认证与会话)
- [4. 授权](#4-授权)
- [5. 密码与凭据](#5-密码与凭据)
- [6. 令牌与邮件流程](#6-令牌与邮件流程)
- [7. CSRF 与浏览器安全](#7-csrf-与浏览器安全)
- [8. 双因素认证（TFA）](#8-双因素认证tfa)
- [9. JWT / API 认证](#9-jwt--api-认证)
- [10. 配置安全清单](#10-配置安全清单)
  - [10.1 必需配置](#101-必需配置)
  - [10.2 推荐配置](#102-推荐配置)
  - [10.3 禁止配置](#103-禁止配置)
  - [10.4 密钥轮换决策表](#104-密钥轮换决策表)
  - [10.5 生产反向代理配置参考（Nginx）](#105-生产反向代理配置参考nginx)
- [11. 已知风险与待决策](#11-已知风险与待决策)
- [12. 测试覆盖与缺口](#12-测试覆盖与缺口)
- [13. 安全运营与响应](#13-安全运营与响应)
- [14. 发布前安全检查清单](#14-发布前安全检查清单)

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

| 风险项 | 缺陷根因 | 临时阻断要求（运维/管理） |
| --- | --- | --- |
| **SEC-01**（禁用 admin 仍有效） | 已在 `0.4.2` 修复；0.4.1 及更早版本仍优先放行 `admin` 角色 | 对 0.4.1 及更早的部署：**禁止单纯设置 `is_active=False`**；禁用或离职处理管理员时，必须同时移除其 `admin` 角色，或直接删除账号。 |
| **SEC-02**（JWT 绕过 TFA） | `load_user_from_request` 仅检查 `is_active`，未验证 TFA 完成标记 | 对开启双因素认证的高权限账号，**切勿为其发放纯密码换取的长期 JWT**；必须在 API 网关处要求二次验证凭据，或只允许会话认证。 |
| **SEC-03**（认证端点缺限流） | `0.4.2` 已加入账号级失败锁定（部分修复）：密码与第二因子共享计数、指数退避；但未知用户名、注册与找回密码入口仍无应用层计数 | **反向代理硬性限流仍然必须**：Nginx / Envoy / WAF 对 `/user/login/`、`/user/register/`、`/user/verify_tfa/`、`/user/forgot_password/`、`/user/reset_password/` 按来源 IP 限流（如单 IP 每分钟 ≤5 次），与内置账号锁定叠加。 |
| **SEC-18**（未配置 sender 泄露令牌）（已在 0.4.2 修复） | `0.4.2` 的 `send_email` 只记录 sender 类型与脱敏收件人，不再输出 `data` | 已发布 0.4.1 及更早版本仍会把完整载荷写入 warning；这些版本的日志需限制访问并过滤验证/重置链接。 |
| **SEC-19 / V-01**（内联编辑绕过只读开关） | 已在 `0.4.2` 修复；0.4.1 及更早版本仅检查 `column_editable_list` | 对 0.4.1 及更早的部署：若模型需全局只读，务必在 ModelView 中将 `column_editable_list` 显式置空 `()`，不要仅依赖 `can_edit = False`。 |

## 1. 范围与威胁模型

### 1.1 范围

本文覆盖：

- 用户认证、登录会话、登出、密码修改
- 授权（admin、`super_admin`、`role_need`、公开视图、激活状态）
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

| 资产 | 位置 | 泄露/篡改影响 |
| --- | --- | --- |
| 用户密码哈希 | `users.password` | 离线破解、撞库 |
| 会话 | Flask signed cookie（`_user_id` 等） | 账号接管 |
| `SECRET_KEY` | 配置/环境 | 伪造会话、令牌、CSRF |
| `JWT_SECRET_KEY` | 配置/环境 | 伪造 Bearer token |
| 邮箱/重置令牌 | URL query、邮件 | 账号接管、邮箱变更 |
| TOTP secret | `users.totp_secret`（AES-GCM 加密） | 生成 2FA 验证码 |
| 恢复码 | `users.recovery_codes`（哈希） | 绕过 TFA |
| Admin 数据 | 数据库/后台 | 数据泄露、篡改、删除 |
| SMTP 凭据 | `NOREPLY_EMAIL_SENDER` | 冒名发信、钓鱼 |

### 1.3 参与者与信任边界

| 参与者 | 能力 | 信任假设 |
| --- | --- | --- |
| 匿名访问者 | 访问公开页面、登录/注册/找回 | 不可信 |
| 普通用户 | 登录、管理自己的资料 | 已通过密码认证 |
| Admin | 访问 Admin 模型视图、批量操作、导出 | 高权限，必须重点保护 |
| 被禁用用户 | 旧 session 在下一次请求即失效（`user_loader` 返回 `None` 并清理 session） | 不应访问任何登录保护页 |
| 数据库读取者 | 读取表数据 | 不应能直接伪造 TOTP/密码 |
| 网络攻击者 | 窃听、篡改、重放 | HTTPS 应阻止 |
| 邮件拦截者 | 获取令牌链接 | 令牌必须有 TTL 且可失效 |

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

| 等级 | 含义 |
| --- | --- |
| 高 | 可导致账号接管、权限提升或大规模数据泄露；公网部署前必须处理或明确接受 |
| 中 | 需要特定条件或组合利用；应尽快修复/补偿 |
| 低 | defense-in-depth、信息泄露或运维风险；按计划处理 |
| 信息 | 设计取舍或文档差异，不直接构成漏洞 |

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

| 用途 | 算法/结果 | 使用位置 |
| --- | --- | --- |
| `hasher` | HMAC-SHA256 派生密钥 + BLAKE2b（16 字节摘要） | 邮箱、已存储密码哈希的指纹、恢复码；用户密码存储算法见第 5.1 节 |
| `url-token` | HMAC-SHA256 派生密钥 + itsdangerous | 邮箱验证、改邮箱、重置密码令牌 |
| `encryptor` | HMAC-SHA256 派生密钥（32 字节）+ AES-256-GCM | TOTP secret |
| `csrf` | 派生密钥或 `CSRF_SECRET_KEY` | CSRF token 签名 |
| JWT | `JWT_SECRET_KEY`（独立配置） | Bearer token |

要点：

- `SECRET_KEY` 为 `None`/空时，`derive_key` 抛 `RuntimeError`/`ValueError`。
- 不同 purpose 的密钥互不相等，避免“一处泄露、处处可用”。
- 派生上下文带 `v1`，为未来迁移留出版本位。
- **JWT 使用独立密钥**，不要复用 `SECRET_KEY`。

### 2.3 密钥轮换的影响

| 轮换对象 | 影响 |
| --- | --- |
| `SECRET_KEY` | 现有 session、CSRF token、URL 令牌全部失效；**已加密的 TOTP secret 将无法解密**（当前无迁移机制） |
| `CSRF_SECRET_KEY` | 现有 CSRF token 失效 |
| `JWT_SECRET_KEY` | 现有 Bearer token 失效 |
| 数据库中的 TOTP secret | 需要重新绑定 TFA；当前没有批量重加密工具 |

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
- 该机制只保护 **session**，不保护 JWT（JWT 路径在 `load_user_from_request` 单独检查 `is_active`，见 9.3）。

### 3.3 会话 Cookie 建议

库本身不强制设置 Cookie 安全属性。生产至少显式配置：

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
)
```

注意：

- `SameSite=None` 必须配合 `Secure=True`，且仅在确实需要跨站 Cookie 时使用。
- 不要依赖 Flask 默认值；不同版本/部署可能不同。
- 反向代理要正确传递 `X-Forwarded-Proto`，否则 `Secure` Cookie 可能不生效。

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
       ├─ 若标记 @login_required 且未登录 → 交给 Flask-Login（重定向登录）
       └─ self.allow(...)
            └─ Admin.allow / current_security.authorize_allow(...)
                 └─ SimpleAuthorizer.authorize(...)
```

### 4.2 `SimpleAuthorizer` 判定顺序

当前实现按以下顺序返回：

```python
def allow(self, *args, **kwargs):
    user = kwargs.get("user")
    view = kwargs.get("view")

    # 1. allow_access 公开视图 → 放行
    if view is not None and getattr(view, "allow_access", False):
        return True

    # 2. 非激活 → 拒绝（管理员角色也不例外）
    if not getattr(user, "is_active", True):
        return False

    # 3. admin 角色 → 放行
    if hasattr(user, "get_roles") and "admin" in user.get_roles():
        return True

    # 4. role_need 匹配 → 放行
    if "role_need" in kwargs and hasattr(user, "get_roles") and kwargs["role_need"] in user.get_roles():
        return True

    # 5. super_admin → 放行
    return bool(hasattr(user, "get_roles") and "super_admin" in user.get_roles())
```

### 4.3 判定结果与风险

| 场景 | 结果 | 说明 |
| --- | --- | --- |
| 匿名 + 普通视图（`allow_access=False`） | 拒绝 → 403 | Admin 模型视图默认行为 |
| 匿名 + `@login_required` | 重定向登录 | `login_required` 在 `allow` 之前处理 |
| 匿名 + `allow_access=True` | 放行 | 公开登录/注册/门户 |
| 普通用户 + 无角色 | 拒绝 | 默认拒绝 |
| 普通用户 + `role_need` 匹配 | 放行 | 需 active |
| `super_admin` + active | 放行 | active 检查在最后一步之前 |
| `super_admin` + inactive | 拒绝 | 会先被 active 检查拦截 |
| **`admin` + inactive** | **拒绝** | 先检查 `is_active`，再判断 `admin` |
| `admin` + 任意视图（active） | 放行 | 高权限，需重点保护 |

**SEC-01（高，已在 0.4.2 修复）**：`0.4.2` 已把 `is_active` 检查移到 `admin` 角色判断之前；`is_active=False` 的管理员访问 Admin 返回 403，公开 `allow_access` 视图行为不变。回归测试见 `tests/unit/security/test_authorizer.py::test_deny_inactive_admin_user` 与 `tests/integration/admin/test_admin.py::test_inactive_admin_is_denied`。

对已发布的 0.4.1 及更早版本，仍需按第 0.3 节执行临时阻断：禁用管理员时**同时移除 admin 角色**或删除账号。

### 4.4 公开视图与禁用账号

`UserView.allow_access = True` 让登录/注册等公开端点可匿名访问；账号功能使用 `@login_required`：

```python
@login_required
@expose_url("/change_password/", methods=("GET", "POST"))
def change_password(self): ...
```

`is_active=False` 的账号无法登录（`REQ-AUTH-009`），既有会话在下一次请求由 `user_loader` 失效（`REQ-AUTH-010`），因此授权器不会收到已认证的禁用用户。未验证邮箱（`email_verified=False`）的账号本身是 active，可登录并使用资料页重发验证邮件。

### 4.5 Admin 视图

> View/ModelView 的路由与配置见 [`spec.md` 第 10 章](./spec.md#10-view-与-admin-专题)；本节只讨论访问控制。

- `Admin` 默认 URL：`/admin`。
- 模型视图默认 `allow_access=False`。
- 匿名访问 `/admin/author/` 默认返回 **403**，不是登录重定向；需要跳转登录时给方法加 `@login_required`。
- `/admin/` 门户由 `PortalExtension.IndexView` 提供，`allow_access=True`，匿名可访问；不要把它误认为“后台已公开”。
- Admin 视图的 `can_create`/`can_edit`/`can_delete` 是**视图级功能开关**，不是用户授权；用户授权仍由 `SimpleAuthorizer` 决定。

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

| 表单 | 规则 |
| --- | --- |
| 注册 | 密码 8–50；重复密码必须一致；用户名 6–50 |
| 修改密码 | 旧密码 3–50；新密码 8–50；重复一致 |
| 重置密码 | 新密码 8–50；重复一致 |
| 改邮箱 | 当前密码 3–50 |
| 登录 | 仅 `DataRequired`，无长度限制 |

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
- 修改密码**不会**使已签发的 JWT 失效（SEC-08，中）。
- 重置密码同样改变密码哈希 → 旧 session 失效；JWT 仍有效直到过期。

建议：

- 高安全场景缩短 JWT 有效期，或引入 token 版本号/撤销列表。
- 在密码变更后要求重新登录所有设备（JWT 需额外机制）。

## 6. 令牌与邮件流程

### 6.1 令牌类型

| 流程 | serializer | 邮件 `type` | 链接字段 | 令牌字段 | 默认有效期 |
| --- | --- | --- | --- | --- | --- |
| 邮箱验证 | `verify_email` | `verify_email` | `verification_link` | `verification_token` | 7 天 |
| 改邮箱 | `change_email` | `verify_email` | `verification_link` | `verification_token` | 7 天 |
| 重置密码 | `reset_password` | `reset_password` | `reset_password_link` | `reset_password_token` | 30 分钟 |

`get_within()`：

```python
default_max_age = 1800 if serializer_name == "reset_password" else 86400 * 7
return self.app.config.get(f"{serializer_name.upper()}_MAX_AGE", default_max_age)
```

可覆盖配置：`RESET_PASSWORD_MAX_AGE`、`VERIFY_EMAIL_MAX_AGE`、`CHANGE_EMAIL_MAX_AGE`。

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
    session[csrf_field_name] = hashlib.sha1(os.urandom(64)).hexdigest()

csrf_secret_key = csrf_key(current_app.secret_key, current_app.config)
s = URLSafeTimedSerializer(csrf_secret_key, salt=CSRF_SALT)
csrf_token = s.dumps(session[csrf_field_name])
```

校验：

- 从表单/ JSON 取 `csrf_token`
- 用同一派生密钥和 salt 解析
- 检查最大年龄（默认 1800 秒）
- `hmac.compare_digest(session token, token)` 防时序攻击

### 7.2 配置

| 配置 | 默认 | 安全建议 |
| --- | --- | --- |
| `CSRF_ENABLED` | `True` | 生产保持 `True` |
| `CSRF_SECRET_KEY` | 派生 | 可选独立密钥；轮换会使现有 token 失效 |
| `CSRF_FIELD_NAME` | `csrf_token` | 不要随意改名，前后端需一致 |
| `CSRF_TIME_LIMIT` | `1800` | 按业务调整；越长暴露窗口越大 |

> 测试 `tests/conftest.py` 默认 `CSRF_ENABLED=False`，仅用于简化测试；不要把测试配置带到生产。

### 7.3 JSON / AJAX

- `FlaskMeta.wrap_formdata` 支持 `request.form`、`request.files`、JSON。
- 前端从 `<meta name="csrf-token">` 读取 token，AJAX 请求以 `csrf_token` 字段提交。
- `editable.js`、`form.js` 已处理 CSRF 字段；自定义 AJAX 必须显式带上 token。
- 登出是 `GET /user/logout/`，未加 CSRF；影响通常仅为“强制登出”（低），但高安全场景可改为带 CSRF 的 POST。

### 7.4 Cookie 与安全响应头

库不设置安全响应头；生产应在反向代理/应用层补充：

| 响应头 | 建议 |
| --- | --- |
| `Strict-Transport-Security` | `max-age=31536000; includeSubDomains`（确认全站 HTTPS 后） |
| `Content-Security-Policy` | 按实际资源收紧；至少限制 `frame-ancestors` |
| `X-Frame-Options` | `DENY` 或 `SAMEORIGIN` |
| `X-Content-Type-Options` | `nosniff` |
| `Referrer-Policy` | `no-referrer` 或 `strict-origin-when-cross-origin` |
| `Permissions-Policy` | 按需关闭不需要的浏览器能力 |

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
- 富文本字段若允许 HTML，需要单独的白名单清洗（当前库不提供）。

## 8. 双因素认证（TFA）

### 8.1 TOTP secret 加密存储

```python
def get_or_create_totp_secret(self):
    if self.totp_secret is None:
        plaintext = tfa.generate_totp_secret()
        self.totp_secret = current_security.encryptor.encrypt(plaintext)
        db.session.commit()
        return plaintext
    return self.get_totp_secret()

def get_totp_secret(self):
    if self.totp_secret is None:
        return None
    return current_security.encryptor.decrypt(self.totp_secret)
```

- 使用 AES-256-GCM；每次加密使用随机 nonce，密文为 `nonce || ciphertext` 的 URL-safe base64。
- 数据库泄露时，攻击者不能直接读取 TOTP secret。
- 但 `SECRET_KEY` 泄露或轮换会影响解密（见 10.4）。

### 8.2 启用 / 关闭 / 重绑

| 操作 | 要求 | 说明 |
| --- | --- | --- |
| `setup_tfa` | 登录 + active | 生成/返回 TOTP secret 与 provisioning URI；页面 no-cache |
| `enable_tfa` | 登录 + active + 有效 TOTP | 启用后设置 `SESSION_KEY_TFA_VERIFIED=True` |
| 关闭 TFA | 登录 + active + 有效 TOTP | 清空 `totp_secret` 与 TFA session 标记 |
| `rebind_tfa` | 登录 + active + `tfa_verified` + `tfa_recovery` | 用于恢复码登录后重新绑定 authenticator |
| `recovery_codes` | 登录 + active + `tfa_verified` | 生成并展示一次恢复码；数据库只存哈希 |

注意：

- 启用/关闭 TFA 需要当前 TOTP 验证码，但**不要求重新输入密码**。
- 关闭 TFA 会同时清空 `totp_secret` 与 `recovery_codes`；重新启用后必须重新生成恢复码（SEC-16）。
- `rebind_tfa` 的 pending secret 在 session 中加密保存；重绑成功会清空未使用的恢复码，需要重新生成。

### 8.3 登录时的 TFA

- 密码正确且 `tfa_enabled=True` → 只写 `pending_tfa_user_id`，**不建立登录会话**。
- `/user/verify_tfa/` 故意不加 `@login_required`；它靠 session 中的 pending id 识别用户。
- 验证通过后才 `login_user`，并清理 pending 状态。
- 恢复码登录同样完成第二因子，并消耗一个恢复码。
- 登出清理所有 TFA 相关 session key。

### 8.4 TFA 缺口

| 缺口 | 等级 | 说明 |
| --- | --- | --- |
| JWT 绕过 TFA | 高（启用 JWT 时） | `load_user_from_request` 只检查 active，不检查 TFA（SEC-02） |
| 无限流/锁定 | 高（公网） | 6 位 TOTP 可被在线暴力尝试；`0.4.2` 已加入内置失败锁定，仍缺注册/找回入口限流与验证码（SEC-03） |
| 无 TOTP 重放防护 | 低-中 | 同一 30 秒窗口内验证码可重复使用；pyotp 默认窗口 |
| `TFA_EXEMPT_ENDPOINTS` 未实现 | 中 | `flask-exts/docs/configure.rst` 有文档，代码中无引用（SEC-04） |

建议：

- 启用 JWT API 时，在 JWT 载荷加入 `amr`/`tfa` 声明，或在 `load_user_from_request` 中强制 TFA。
- 在反向代理/WAF 对登录/TFA/恢复码接口限流，与内置账号锁定叠加。
- 评估 TOTP `valid_window` 与重放缓存。
- 实现或移除 `TFA_EXEMPT_ENDPOINTS` 文档承诺。

### 8.5 失败登录锁定（v0.4.1 之后）

`main` 在 `users` 表上新增两个字段，并在 `SqlaUserStore` 中实现账号级失败计数：

| 字段 | 类型 | 作用 |
| --- | --- | --- |
| `failed_login_count` | `int NOT NULL DEFAULT 0` | 连续失败次数，密码错误与第二因子错误共用 |
| `locked_until` | `timestamp NULL` | 锁定截止时间，过期后自动恢复 |

行为：

- 失败达到 `USER_LOGIN_MAX_FAILURES`（默认 5）后开始锁定，延迟从 `USER_LOGIN_LOCKOUT_BASE_SECONDS`（默认 60 秒）起按 2 的幂增长，上限 `USER_LOGIN_LOCKOUT_MAX_SECONDS`（默认 3600 秒）。
- 锁定期间密码校验不会执行，登录页返回剩余等待时间。
- 锁定的账号无法继续进行 pending TFA 校验；`_get_pending_tfa_user` 会清理 pending 状态。
- 只有完整登录成功（密码，或密码 + 第二因子）或成功重置密码才清零计数；仅密码正确不会清零。
- 锁定状态与 `is_active` 分离：前者自动过期，后者是管理员禁用。
- 计数存在数据库中，因此与客户端 IP 无关，并在共享同一数据库的多进程/多实例间一致。

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
def jwt_encode(payload, key=None, delta=None, algorithm=None):
    if delta is None:
        delta = current_app.config.get("JWT_ACCESS_TOKEN_MAX_AGE", 900)
    exp = datetime.datetime.now(tz=datetime.timezone.utc) + datetime.timedelta(seconds=delta)
    token_payload = dict(payload)
    token_payload["exp"] = exp
    token_payload["token_use"] = "access"
    return jwt.encode(
        token_payload,
        key=key if key is not None else current_app.config.get("JWT_SECRET_KEY"),
        algorithm=algorithm or current_app.config.get("JWT_HASH", "HS256"),
    )
```

- 默认有效期 900 秒。
- 必须包含 `exp`、`token_use`。
- `jwt_decode` 固定算法列表，要求 `exp`/`token_use`。
- `Authorization: Bearer <token>`。

### 9.2 请求加载

```python
if "Authorization" in request.headers:
    payload = authorization_decoder(authstr)
    if "id" in payload:
        user = current_userstore.get_user_by_id(int(payload["id"]))
        if user is not None and user.is_active:
            return user
    identity = payload.get(current_userstore.identity_name)
    if identity is not None:
        user = current_userstore.get_user_by_identity(identity)
        if user is not None and user.is_active:
            return user
```

安全点：

- 只接受 `Bearer`，拒绝 Basic。
- 不读取 `api_key` 查询参数或其他请求参数；认证只来自 `Authorization` 头。
- 只接受 `token_use="access"`。
- 检查 `is_active`。

### 9.3 JWT 缺口

| 缺口 | 等级 | 说明 |
| --- | --- | --- |
| 不检查 TFA | 高（启用 JWT 时） | 启用 TFA 的用户仍可用 Bearer token 直接访问（SEC-02） |
| 密码变更不失效 | 中 | JWT 不包含密码指纹，改密后旧 token 仍有效至过期（SEC-08） |
| 无撤销列表 | 中 | 无法主动吊销单个 token；只能轮换 `JWT_SECRET_KEY`（全部失效） |
| 无 audience/issuer | 中 | 多服务共享密钥时可能被跨服务重放 |
| `JWT_SECRET_KEY` 未设置时 | 中 | demo 未配置；调用 JWT 功能会失败，需显式配置 |
| `JWT_HASH` 可配置 | 低 | 必须限制为可信算法（HS256/RS256 等），不要让用户输入控制 |

建议：

- JWT 仅用于 API 场景，并明确 TFA 策略。
- 加入 `jti` + 撤销列表/短期 token + 刷新 token。
- 加入 `aud`/`iss` 校验。
- 密码变更时递增 `token_version` 并写入 JWT。
- 使用独立 `JWT_SECRET_KEY`，不要与 `SECRET_KEY` 相同。

## 10. 配置安全清单

### 10.1 必需配置

| 配置 | 要求 | 说明 |
| --- | --- | --- |
| `SECRET_KEY` | 必填，强随机 | 派生会话/CSRF/令牌/加密密钥 |
| `SQLALCHEMY_DATABASE_URI` | 必填 | 数据库连接；生产使用受控账号 |
| `JWT_SECRET_KEY` | 使用 JWT 时必填 | 独立于 `SECRET_KEY` |
| `NOREPLY_EMAIL_SENDER` | 使用邮件流程时必填 | SMTP 配置；凭据放环境变量/密钥管理 |

### 10.2 推荐配置

| 配置 | 推荐值 | 说明 |
| --- | --- | --- |
| `CSRF_ENABLED` | `True` | 生产保持开启 |
| `CSRF_SECRET_KEY` | 独立随机值 | 可选；不设置则从 `SECRET_KEY` 派生 |
| `CSRF_TIME_LIMIT` | `1800` | 按业务调整 |
| `RESET_PASSWORD_MAX_AGE` | `1800` | 重置令牌 30 分钟 |
| `VERIFY_EMAIL_MAX_AGE` | 短于 7 天 | 邮箱验证令牌 |
| `CHANGE_EMAIL_MAX_AGE` | 短于 7 天 | 改邮箱令牌 |
| `JWT_ACCESS_TOKEN_MAX_AGE` | `900` 或更短 | API token |
| `JWT_HASH` | `HS256`（或固定白名单） | 不要动态接受用户输入 |
| `APP_NAME` | 真实应用名 | TOTP issuer |
| `SESSION_COOKIE_*` / `REMEMBER_COOKIE_*` | 见 3.3 | Secure/HttpOnly/SameSite |
| `TFA_EXEMPT_ENDPOINTS` | **当前未实现** | 文档有描述，代码未读取（SEC-04） |

### 10.3 禁止配置

- `SECRET_KEY = "demo"` / `"changeme"` / 空值
- 生产 `CSRF_ENABLED=False`
- `SESSION_COOKIE_SECURE=False`（HTTPS 环境）
- 把 `JWT_SECRET_KEY` 设为 `SECRET_KEY`
- 把 SMTP 密码、数据库密码写进仓库
- 使用 demo 的 `admin/admin`
- 给普通业务账号授予 `admin`

### 10.4 密钥轮换决策表

| 场景 | 操作 | 影响 | 建议 |
| --- | --- | --- | --- |
| 怀疑 `SECRET_KEY` 泄露 | 轮换 `SECRET_KEY` | 所有 session/CSRF/URL 令牌失效；TOTP secret 无法解密 | 先评估 TOTP 用户，准备重绑/重加密；强制全员重新登录 |
| 仅怀疑 CSRF 密钥 | 轮换 `CSRF_SECRET_KEY` | 现有 CSRF token 失效 | 低风险，可随时轮换 |
| 怀疑 JWT 密钥 | 轮换 `JWT_SECRET_KEY` | 所有 JWT 失效 | 通知 API 客户端重新登录 |
| 常规密钥轮换 | 按周期轮换 | 同上 | 建立迁移/通知流程 |

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

| ID | 等级 | 位置 | 现状 | 建议 |
| --- | --- | --- | --- | --- |
| SEC-01 | 高（已在 0.4.2 修复） | `security/authorizer/simple_authorizer.py` | `is_active` 检查已移到 `admin` 角色判断之前；`test_deny_inactive_admin_user`、`test_inactive_admin_is_denied` 覆盖 | 已发布 0.4.1 及更早版本的部署仍需同时移除 admin 角色 |
| SEC-02 | 高（启用 JWT） | `builtin_extensions/login_ext.py::load_user_from_request` | JWT 只检查 `is_active`，不检查 TFA | 在 JWT 中携带 `amr`/`tfa` 声明并校验，或返回前强制 TFA |
| SEC-03 | 高（部分修复，已在 0.4.2 发布） | 登录/注册/找回/TFA/恢复码 | `main` 已实现账号级失败锁定（`users.failed_login_count` + `locked_until`，密码与 TFA 共享计数、指数退避）；仍缺 IP 维度、未知用户名计数与注册/找回入口限流 | 反向代理/WAF 按 IP 限流，与内置账号锁定叠加 |
| SEC-04 | 中 | `flask-exts/docs/configure.rst` vs 代码 | `TFA_EXEMPT_ENDPOINTS` 有文档但未实现 | 实现该配置，或从文档移除并说明 |
| SEC-05 | 中（已修复） | `usercenter/forms/register.py` | 注册邮箱已使用 `DataRequired()` + `Email()` + `Length(max=254)`；`test_register_rejects_invalid_email` 覆盖非法格式且不创建用户 | 保持 `Email()` 与改邮箱表单一致；投递性检查默认关闭 |
| SEC-06 | 中 | 密码策略/表单 | 快照未见常见或泄露密码阻断；服务端 API 可绕过表单长度限制（当前未复核） | 按适用标准评估阻断要求并统一校验；不默认要求字符组合 |
| SEC-07 | 中 | `security/keys.py` + `encryptor` | 轮换 `SECRET_KEY` 会使 TOTP secret 无法解密 | 提供重加密迁移或提前重绑 |
| SEC-08 | 中 | `login_ext.py` | JWT 不随密码变更失效 | 加入 `token_version` 或缩短 TTL |
| SEC-09 | 低-中 | 邮件令牌 | 令牌在 URL query，可能进 Referer/日志 | `Referrer-Policy: no-referrer`、日志脱敏、短 TTL |
| SEC-10 | 低-中 | 注册/改邮箱 | 重复邮箱/用户名可枚举 | 统一提示或接受取舍并记录 |
| SEC-11 | 中 | 全局 | 无安全审计日志（登录失败、TFA 失败、密码变更、管理员操作） | 接入结构化日志/审计系统 |
| SEC-12 | 中 | 部署 | 未默认设置安全 Cookie/响应头 | 按 3.3/7.4 显式配置 |
| SEC-13 | 低（已在 0.4.2 修复） | `user_view.py::recovery` | 只接受 `hasher.verify` 的哈希校验，明文兼容分支已移除；`test_plaintext_recovery_codes_are_rejected` 覆盖 | 已发布版本仍接受明文兼容值 |
| SEC-14 | 低 | 用户模型 | `status`、`expired_at` 字段未使用 | 实现或移除，避免误以为已生效 |
| SEC-15 | 信息 | Admin 视图 | 匿名访问模型视图返回 403，不是登录重定向 | 需要跳转登录时加 `@login_required` |
| SEC-16 | 中（已在 0.4.2 修复） | `usercenter/user_view.py::enable_tfa`、`rebind_tfa` | 关闭 TFA 与重绑 authenticator 均清空 `recovery_codes`；`test_tfa`、`test_recovery` 覆盖 | 已发布版本旧恢复码仍可能有效 |
| SEC-17 | 中-高（已在 0.4.2 修复） | `emailer/smtp.py::SmtpSSL` | 显式传入 `ssl.create_default_context()`（`CERT_REQUIRED` + `check_hostname=True`）；TLS 失败包装与 context 开关均有测试覆盖 | 私有 CA 配置到信任库；监控发信失败率 |
| SEC-18 | 中（已在 0.4.2 修复） | `emailer/base.py::send_email` | 找不到 sender 时只记录 `type` 与脱敏收件人，不输出链接/令牌；`test_missing_sender_warning_redacts_payload` 覆盖 | 已发布版本仍需限制日志访问并过滤敏感载荷 |
| SEC-19（V-01 别名） | 中（已在 0.4.2 修复） | `admin/model/view.py::ajax_update` | `can_edit=False` 时返回 403；`test_ajax_update_requires_can_edit` 覆盖 | 已发布版本仍需将 `column_editable_list` 置空 |

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
- [ ] 普通用户没有 `admin`/`super_admin`
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
