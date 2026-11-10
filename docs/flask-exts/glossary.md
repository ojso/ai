# 术语表

> 本文档用于统一本目录中的关键术语与英文/代码名，避免 AI 或维护者在不同文档中产生“同词不同义”的偏差。
>
> | 项目 | 内容 |
> | --- | --- |
> | 文档版本 | v0.1 |
> | 状态 | 可用 |
> | 最后更新 | 2026-11-09 |
> | 数据快照 | 不适用（治理/术语文档） |
> | 适用范围 | 本目录所有文档、AI 协作与工程评审 |

## 1. 术语与定义

本节是术语定义的唯一事实源；其他文档只引用，不复制。

| 术语 | 英文/代码名 | 定义 | 适用位置 |
| --- | --- | --- | --- |
| 扩展 | `Extension` | 可注册、可初始化、可按依赖顺序组装的基础模块 | `architecture.md` / `spec.md` |
| 扩展管理器 | `ExtensionManager` | 管理扩展生命周期、注册和依赖解析的核心对象 | `architecture.md` |
| 扩展注册器 | `Registry`（概念名） | 保存扩展注册表并执行初始化/关闭顺序的注册表对象；具体类名以源码为准 | `architecture.md` / `spec.md` 第 11 章 |
| 视图层 | `View` | 页面入口、权限判断、页面动作与渲染 | `spec.md` 第 10 章 |
| 模型视图 | `ModelView` | 以模型为中心的 CRUD 视图与表单入口 | `spec.md` 第 10 章 |
| 数据后端 | `DataBackend` | 提供查询、筛选、排序、导出等数据访问能力 | `spec.md` 第 10 章 |
| 用户存储 | `UserStore` | 负责用户对象的读取、写入与身份相关操作 | `security.md` / `spec.md` |
| Admin | `Admin` | 后台管理入口或后台框架层 | `spec.md` 第 10 章 |
| 安全边界 | `security boundary` | 认证、授权、CSRF、令牌、TFA 与敏感配置的控制边界 | `security.md` |
| 需求条目 | `REQ-*` | 需求契约编号，见 `requirements.md` | `requirements.md` |
| 测试用例 | `TC-*` | 测试设计用例的编号，见 `testing.md`；历史用例保留旧编号别名 | `testing.md` |
| 令牌动作 | `TokenBasedAction` | 依赖令牌的安全动作，如重置密码、邮箱验证、2FA | `security.md` |
| JWT | `JWT` | JSON Web Token，用于令牌风格认证或会话声明 | `security.md` |
| TOTP | `TOTP` | Time-based One-Time Password，时间一次性密码 | `security.md` |
| CSRF | `CSRF` | Cross-Site Request Forgery，跨站请求伪造 | `security.md` |
| TFA | `TFA` | Two-Factor Authentication，双因素认证 | `security.md` |
| 设计总纲 | `spec` | 项目定位、背景、设计动机、边界与取舍 | `spec.md` |
| 架构骨架 | `architecture` | 模块依赖、生命周期、运行时边界 | `architecture.md` |
| 行为契约 | `requirements` | 系统“应该如何表现”的明确规则 | `requirements.md` |
| 术语已确认 | `confirmed` | 可由源码/测试/文档证实 | 本表 |
| 术语待确认 | `pending` | 仍需要验证或决策 | 本表 |

<a id="11-契约与测试编号的领域与能力词表"></a>

### 1.1 契约与测试编号的领域词表

本表是 `REQ-<领域>-<序号>` 和 `TC-<领域>-<序号>` 的领域词表；契约编号规则见 [`requirements.md`](./requirements.md) 第 1.1 节，测试用例规则及历史映射见 [`testing.md`](./testing.md) 第 6.3 节。领域按文档中被验证的主要能力划分；测试和契约可跨领域关联，不能仅凭编号推定一对一关系。

| 领域 | 范围与边界 |
| --- | --- |
| `EXT` | 扩展注册、依赖与生命周期 |
| `DATA` | 数据库连接、session、查询和事务 |
| `AUTH` | 认证、会话及账号中心用户流程；已有注册、重置契约分别保留 `REG`、`RESET` |
| `AUTHZ` | 通用角色匹配与访问授权契约 |
| `REG` | 已有注册、邮箱验证与修改契约 |
| `RESET` | 已有密码找回与重置契约 |
| `TOKEN` | 邮箱验证、修改及密码重置使用的动作令牌契约 |
| `CSRF` | CSRF 防护契约；表单组件测试可归 `FORM` |
| `ADMIN` | 后台列表、表单、CRUD、导出与操作开关 |
| `VIEW` | 通用自定义视图和页面契约；后台行为见 `ADMIN` |
| `FORM` | 通用表单、字段、校验与 CSRF 表单测试 |
| `SEC` | 安全基础组件及安全相关测试；具体认证和授权契约见 `AUTH`、`AUTHZ` 等 |
| `USER` | UserStore 用户、角色和持久化测试 |
| `EMAIL` | 邮件发送器与邮件内容测试 |
| `FRONTEND` | 前端插件、资源和模板集成测试 |
| `CLI` | 命令行功能测试 |
| `ERROR` | 错误处理和错误页面测试 |
| `SIGNAL` | 应用信号及邮件信号载荷测试 |
| `I18N` | 语言、时区和复数形式测试 |

### 1.2 现有契约能力参考

下表保留依据历史契约归纳的能力描述，供理解和检索使用；能力**不是编号的一部分**，也不是新旧编号映射。历史契约可能包含多个行为，不代表已拆分。涉及多个领域时引用相关契约与安全约束，不重复登记同一行为。

| 领域 | 能力 | 范围与边界 | 依据的历史契约 |
| --- | --- | --- | --- |
| `EXT` | `REGISTRY` | 扩展注册和名称校验 | `REQ-EXT-001` |
| `EXT` | `DEPENDENCY` | 扩展依赖及其排序、错误 | `REQ-EXT-002` |
| `EXT` | `LIFECYCLE` | 初始化、后初始化和关闭 | `REQ-EXT-003`、`REQ-EXT-004` |
| `DATA` | `CONNECTION` | 数据库绑定、session 与释放 | `REQ-DATA-001` |
| `DATA` | `QUERY` | 通用查询、关系 JOIN、搜索、筛选和排序 | `REQ-DATA-002` |
| `AUTH` | `LOGIN` | 登录凭据校验和登录结果 | `REQ-AUTH-001`、`REQ-AUTH-002` |
| `AUTH` | `TFA` | 登录过程中的第二因子验证 | `REQ-AUTH-003`、`REQ-AUTH-004` |
| `AUTH` | `SESSION` | 已认证会话的失效与登出清理 | `REQ-AUTH-005`、`REQ-AUTH-006` |
| `AUTH` | `ACCOUNT` | 未激活账号的账号功能边界 | `REQ-AUTH-007` |
| `AUTH` | `REDIRECT` | 认证流程中的安全重定向 | `REQ-AUTH-008` |
| `AUTHZ` | `ROLE` | 角色匹配与角色授权 | `REQ-AUTHZ-001`、`REQ-AUTHZ-006` |
| `AUTHZ` | `ACCESS` | 匿名、公开视图与账号状态的访问控制 | `REQ-AUTHZ-002`、`REQ-AUTHZ-003`、`REQ-AUTHZ-004`、`REQ-AUTHZ-005` |
| `REG` | `SIGNUP` | 注册创建账号及注册输入校验 | `REQ-REG-001`、`REQ-REG-002`、`REQ-REG-006` |
| `REG` | `VERIFY` | 邮箱验证和重发验证邮件 | `REQ-REG-003`、`REQ-REG-004` |
| `REG` | `CHANGE` | 登录用户修改邮箱及确认 | `REQ-REG-005` |
| `RESET` | `PASSWORD` | 找回、重置密码及旧凭据失效 | `REQ-RESET-001`、`REQ-RESET-002`、`REQ-RESET-003` |
| `TOKEN` | `ACTION` | 邮箱验证、修改与密码重置所用动作令牌的生成、校验及失效；不泛指 JWT | `REQ-TOKEN-001`、`REQ-TOKEN-002`、`REQ-TOKEN-003`、`REQ-TOKEN-004` |
| `CSRF` | `PROTECTION` | CSRF 令牌生成、校验及启用配置 | `REQ-CSRF-001`、`REQ-CSRF-002`、`REQ-CSRF-003` |
| `ADMIN` | `PAGINATION` | 后台列表的分页与页大小 | `REQ-ADMIN-001` |
| `ADMIN` | `SEARCH` | 后台列表搜索 | `REQ-ADMIN-002` |
| `ADMIN` | `FILTER` | 后台列表筛选 | `REQ-ADMIN-003` |
| `ADMIN` | `SORT` | 后台列表排序 | `REQ-ADMIN-004` |
| `ADMIN` | `COUNT` | 后台列表搜索、筛选结果的计数 | `REQ-ADMIN-005` |
| `ADMIN` | `CRUD` | 后台创建、编辑和删除的业务结果 | `REQ-ADMIN-006` |
| `ADMIN` | `INLINE` | 后台父子记录与内联表单 | `REQ-ADMIN-007` |
| `ADMIN` | `AJAX` | 后台 AJAX 外键查询和内联更新 | `REQ-ADMIN-008` |
| `ADMIN` | `EXPORT` | 后台导出与导出限制 | `REQ-ADMIN-009` |
| `ADMIN` | `ACCESS` | 后台视图级操作开关及对应路由的约束；通用角色与访问判断见 `AUTHZ` | `REQ-ADMIN-010` |
| `ADMIN` | `URL` | 后台列表参数的 URL 编码与回放 | `REQ-ADMIN-011` |
| `ADMIN` | `KEY` | 后台记录主键编码、解析与定位 | `REQ-ADMIN-012` |
| `VIEW` | `PAGE` | 自定义页面、路由和模板渲染；后台列表能力见 `ADMIN` | `REQ-VIEW-001` |

边界重叠时，先判断主要行为：例如通用查询归 `DATA`，后台列表筛选归 `ADMIN`；认证成功归 `AUTH`，通用角色授权契约归 `AUTHZ`。涉及多个边界时在条目中显式关联，而不是按文件路径重复编号。

新领域出现时，先核对现有范围；确需扩展时在第 1.1 节新增定义及依据后再分配编号。不以迁就旧条目为由自动拆分或更名。

## 2. 术语使用规则

- 首次出现时，优先写成中文 + 英文/代码名，例如：ModelView（`ModelView`）。
- 若术语有多个常见写法，必须在本表中统一，以避免 AI 生成不同版本的名称。
- 对无法确认的术语，必须标注为 `待确认`，不得直接写成已定论。
- 对安全相关术语，必须以 `security.md` 为准，不能在其他文档中自行扩展定义。

## 3. 术语维护方式

- 新增术语时，先补充到本表，再在相关文档中使用。
- 对外部依赖、第三方库名称，优先使用官方术语，不在本表中重复发明缩写。
- 若同一术语在不同文档中含义不一致，须修正文档或登记待处理问题；仅在确认涉及具体契约实现缺口时，按 `requirements.md` 第 2 节关联对应问题。

## 4. 适用示例

```text
ModelView（`ModelView`）是后台中以模型为中心的 CRUD 视图入口；
它的行为边界由 spec.md 第 10 章说明。
```

## 5. 说明

本文件是“语义统一层”，不是实现细节层；它的目标是减少术语漂移，提升 AI 对项目的理解一致性。
