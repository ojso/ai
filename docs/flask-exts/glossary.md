# 术语表

> 本文档用于统一本目录中的关键术语与英文/代码名，避免 AI 或维护者在不同文档中产生“同词不同义”的偏差。
>
> 适用范围：本目录所有文档、AI 协作与工程评审
> 更新时间：2026-11-19 08:12:16 +08:00

## 1. 术语与定义

本节是术语定义的唯一事实源；其他文档只引用，不复制。

- **扩展**
  - 英文/代码名：`Extension`
  - 定义：可注册、可初始化、可按依赖顺序组装的基础模块
  - 适用位置：`architecture.md` / `spec.md`

- **扩展管理器**
  - 英文/代码名：`ExtensionManager`
  - 定义：管理扩展生命周期、注册和依赖解析的核心对象
  - 适用位置：`architecture.md`

- **扩展注册器**
  - 英文/代码名：`ExtensionRegistry`（源码类名；概念文档中称 `Registry`）
  - 定义：保存扩展注册表并执行初始化/关闭顺序的注册表对象
  - 适用位置：`architecture.md` / `spec.md` 第 11 章

- **视图层**
  - 英文/代码名：`View`
  - 定义：页面入口、权限判断、页面动作与渲染
  - 适用位置：`spec.md` 第 10 章

- **模型视图**
  - 英文/代码名：`ModelView`
  - 定义：以模型为中心的 CRUD 视图与表单入口
  - 适用位置：`spec.md` 第 10 章

- **数据后端**
  - 英文/代码名：`DataBackend`
  - 定义：提供查询、筛选、排序、导出等数据访问能力
  - 适用位置：`spec.md` 第 10 章

- **用户存储**
  - 英文/代码名：`UserStore`
  - 定义：负责用户对象的读取、写入与身份相关操作
  - 适用位置：`security.md` / `spec.md`

- **Admin**
  - 英文/代码名：`Admin`
  - 定义：后台管理入口或后台框架层
  - 适用位置：`spec.md` 第 10 章

- **安全边界**
  - 英文/代码名：`security boundary`
  - 定义：认证、授权、CSRF、令牌、TFA 与敏感配置的控制边界
  - 适用位置：`security.md`

- **需求条目**
  - 英文/代码名：`REQ-*`
  - 定义：需求契约编号，见 `requirements.md`
  - 适用位置：`requirements.md`

- **测试用例**
  - 英文/代码名：`TC-*`
  - 定义：测试设计用例的编号，见 `testing.md`；历史用例保留旧编号别名
  - 适用位置：`testing.md`

- **令牌动作**
  - 英文/代码名：`TokenBasedAction`
  - 定义：依赖令牌的安全动作，如重置密码、邮箱验证、2FA
  - 适用位置：`security.md`

- **JWT**
  - 英文/代码名：`JWT`
  - 定义：JSON Web Token，用于令牌风格认证或会话声明
  - 适用位置：`security.md`

- **TOTP**
  - 英文/代码名：`TOTP`
  - 定义：Time-based One-Time Password，时间一次性密码
  - 适用位置：`security.md`

- **CSRF**
  - 英文/代码名：`CSRF`
  - 定义：Cross-Site Request Forgery，跨站请求伪造
  - 适用位置：`security.md`

- **TFA**
  - 英文/代码名：`TFA`
  - 定义：Two-Factor Authentication，双因素认证
  - 适用位置：`security.md`

### 1.1 契约与测试编号的领域词表

本节是 `REQ-<领域>-<序号>` 和 `TC-<领域>-<序号>` 的领域词表；契约编号规则见 [`requirements.md`](./requirements.md) 第 1.1 节，测试用例规则及历史映射见 [`testing.md`](./testing.md) 第 6.3 节。领域按文档中被验证的主要能力划分；测试和契约可跨领域关联，不能仅凭编号推定一对一关系。

- `EXT`
  - 范围与边界：扩展注册、依赖与生命周期
  - 主要测试入口：[`testing.md` 第 7.1 节](./testing.md#71-extension-系统)

- `DATA`
  - 范围与边界：数据库连接、session、查询和事务
  - 主要测试入口：[`testing.md` 第 7.2 节](./testing.md#72-datastore--query)

- `AUTH`
  - 范围与边界：认证、会话及账号中心用户流程；已有注册、重置契约分别保留 `REG`、`RESET`
  - 主要测试入口：[`testing.md` 第 7.5 节](./testing.md#75-security)、[第 7.7 节](./testing.md#77-usercenter)

- `AUTHZ`
  - 范围与边界：通用角色匹配与访问授权契约
  - 主要测试入口：[`testing.md` 第 7.3 节](./testing.md#73-admin)、[第 7.5 节](./testing.md#75-security)

- `REG`
  - 范围与边界：已有注册、邮箱验证与修改契约
  - 主要测试入口：[`testing.md` 第 7.7 节](./testing.md#77-usercenter)、[第 7.5 节](./testing.md#75-security)

- `RESET`
  - 范围与边界：已有密码找回与重置契约
  - 主要测试入口：[`testing.md` 第 7.7 节](./testing.md#77-usercenter)、[第 7.5 节](./testing.md#75-security)

- `TOKEN`
  - 范围与边界：邮箱验证、修改及密码重置使用的动作令牌契约
  - 主要测试入口：[`testing.md` 第 7.5 节](./testing.md#75-security)

- `CSRF`
  - 范围与边界：CSRF 防护契约；表单组件测试可归 `FORM`
  - 主要测试入口：[`testing.md` 第 7.4 节](./testing.md#74-forms)

- `ADMIN`
  - 范围与边界：后台列表、表单、CRUD、导出与操作开关
  - 主要测试入口：[`testing.md` 第 7.3 节](./testing.md#73-admin)

- `VIEW`
  - 范围与边界：通用自定义视图和页面契约；后台行为见 `ADMIN`
  - 主要测试入口：[`testing.md` 第 7.3 节](./testing.md#73-admin)、[`demo.md`](./demo.md)

- `FORM`
  - 范围与边界：通用表单、字段、校验与 CSRF 表单测试
  - 主要测试入口：[`testing.md` 第 7.4 节](./testing.md#74-forms)

- `SEC`
  - 范围与边界：安全基础组件及安全相关测试；具体认证和授权契约见 `AUTH`、`AUTHZ` 等
  - 主要测试入口：[`testing.md` 第 7.5 节](./testing.md#75-security)

- `USER`
  - 范围与边界：UserStore 用户、角色和持久化测试
  - 主要测试入口：[`testing.md` 第 7.6 节](./testing.md#76-userstore)

- `EMAIL`
  - 范围与边界：邮件发送器与邮件内容测试
  - 主要测试入口：[`testing.md` 第 7.8 节](./testing.md#78-emailer)

- `FRONTEND`
  - 范围与边界：前端插件、资源和模板集成测试
  - 主要测试入口：[`testing.md` 第 7.9 节](./testing.md#79-frontend)

- `CLI`
  - 范围与边界：命令行功能测试
  - 主要测试入口：[`testing.md` 第 7.10 节](./testing.md#710-commands)

- `ERROR`
  - 范围与边界：错误处理和错误页面测试
  - 主要测试入口：[`testing.md` 第 7.12 节](./testing.md#712-错误处理与信号契约)

- `SIGNAL`
  - 范围与边界：应用信号及邮件信号载荷测试
  - 主要测试入口：[`testing.md` 第 7.12 节](./testing.md#712-错误处理与信号契约)

- `I18N`
  - 范围与边界：语言、时区和复数形式测试
  - 主要测试入口：[`testing.md` 第 7.13 节](./testing.md#713-i18n时区与复数)

契约能力及其 `REQ-*` 映射以 `requirements.md` 为准；本节只维护编号领域边界。

### 1.2 缺陷与安全条目编号

本节是 `CR-*`、`SEC-*` 前缀语义、分配与别名规则的唯一维护位置；条目的状态流转与退役判据见 [`AGENTS.md`](./AGENTS.md) 第 5.7 节。

- `SEC-*`
  - 含义：安全风险与待决策项
  - 分配与登记位置：`security.md` 第 11 节
  - 说明：安全类问题的**唯一主记录**；同一问题出现在其他文档时只作别名引用

- `CR-*`
  - 含义：代码审查发现（Code Review）
  - 分配与登记位置：`spec.md` 第 10.16 节
  - 说明：不区分模块；模块归属由清单“位置”字段承载，不编入编号

**编号规则**：

- 格式 `CR-<序号>`；序号 `001`～`999` 使用三位，超过 `999` 使用自然位数，不使用 `000`，与 `requirements.md` 第 1.1 节一致。
- 新编号取该前缀已分配的最大序号加一；分配前须检查现有条目、已废止编号与空洞说明，避免同一问题重复登记。
- 编号一经分配永不复用，也不因条目退役或换号而回收。
- 前缀语义不因后续认知变化而回改：条目类型一旦发布即保持原判定，需要重新定性时另立记录并说明关系。
- 历史原因导致的缺号必须在该文档表下注明原因；无法确认时标“待核实”，同时声明该编号不得复用。

## 2. 术语使用规则

- 首次出现时，优先写成中文 + 英文/代码名，例如：ModelView（`ModelView`）。
- 若术语有多个常见写法，必须在本节中统一，以避免 AI 生成不同版本的名称。
- 对无法确认的术语，必须标注为 `待确认`，不得直接写成已定论。
- 对安全相关术语，必须以 `security.md` 为准，不能在其他文档中自行扩展定义。

## 3. 术语维护方式

- 新增术语时，先补充到本节，再在其他文档中使用。
- 对外部依赖、第三方库名称，优先使用官方术语，不在本节中重复发明缩写。
- 若同一术语在不同文档中含义不一致，须修正文档或登记待处理问题；仅在确认涉及具体契约实现缺口时，按 `requirements.md` 第 2 节关联对应问题。

## 4. 适用示例

```text
ModelView（`ModelView`）是后台中以模型为中心的 CRUD 视图入口；
它的行为边界由 spec.md 第 10 章说明。
```