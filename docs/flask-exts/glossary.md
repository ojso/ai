# 术语表

> 本文档用于统一本目录中的关键术语与英文/代码名，避免 AI 或维护者在不同文档中产生“同词不同义”的偏差。
>
> | 项目 | 内容 |
> | --- | --- |
> | 文档版本 | v0.1 |
> | 状态 | 可用 |
> | 最后更新 | 2026-11-08 |
> | 数据快照 | 不适用（治理/术语文档） |
> | 适用范围 | 本目录所有文档、AI 协作与工程评审 |

## 1. 术语与定义

本节是术语定义的唯一事实源；其他文档只引用，不复制。

| 术语 | 英文/代码名 | 定义 | 适用位置 |
| --- | --- | --- | --- |
| 扩展 | `Extension` | 可注册、可初始化、可按依赖顺序组装的基础模块 | `architecture.md` / `spec.md` |
| 扩展管理器 | `ExtensionManager` | 管理扩展生命周期、注册和依赖解析的核心对象 | `architecture.md` |
| 扩展注册器 | `Registry`（概念名） | 保存扩展注册表并执行初始化/关闭顺序的注册表对象；具体类名以源码为准 | `architecture.md` / `plugin.md` |
| 视图层 | `View` | 页面入口、权限判断、页面动作与渲染 | `view.md` |
| 模型视图 | `ModelView` | 以模型为中心的 CRUD 视图与表单入口 | `view.md` |
| 数据后端 | `DataBackend` | 提供查询、筛选、排序、导出等数据访问能力 | `view.md` |
| 用户存储 | `UserStore` | 负责用户对象的读取、写入与身份相关操作 | `security.md` / `spec.md` |
| Admin | `Admin` | 后台管理入口或后台框架层 | `view.md` |
| 安全边界 | `security boundary` | 认证、授权、CSRF、令牌、TFA 与敏感配置的控制边界 | `security.md` |
| 需求条目 | `REQ-*` | 需求契约编号，见 `requirements.md` | `requirements.md` |
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

## 2. 术语使用规则

- 首次出现时，优先写成中文 + 英文/代码名，例如：ModelView（`ModelView`）。
- 若术语有多个常见写法，必须在本表中统一，以避免 AI 生成不同版本的名称。
- 对无法确认的术语，必须标注为 `待确认`，不得直接写成已定论。
- 对安全相关术语，必须以 `security.md` 为准，不能在其他文档中自行扩展定义。

## 3. 术语维护方式

- 新增术语时，先补充到本表，再在相关文档中使用。
- 对外部依赖、第三方库名称，优先使用官方术语，不在本表中重复发明缩写。
- 若同一术语在不同文档中含义不一致，必须修正文档或提升为 `known-gap`。

## 4. 适用示例

```text
ModelView（`ModelView`）是后台中以模型为中心的 CRUD 视图入口；
它的行为边界由 view.md 说明，而不是由 spec.md 重复扩写。
```

## 5. 说明

本文件是“语义统一层”，不是实现细节层；它的目标是减少术语漂移，提升 AI 对项目的理解一致性。
