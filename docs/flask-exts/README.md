# Flask-Exts 文档索引

> 本目录是 Flask-Exts 的**架构概览 / 文档驱动 / 测试驱动 / 示例驱动 / 安全治理 / 代码审查**文档集。
>
> - 代码仓库：`flask-exts`
> - 当前版本：`0.4.0`
> - 文档语言：中文；项目代码与项目内文档：英文
> - 本文档集独立存放，不参与项目构建
> - 文档版本：`v0.1`
> - 状态：可用
> - 最后更新：2026-11-08
> - 数据快照：2026-11-07（文档集未附带源码，未复核）

本文只做**索引、职责划分、单一事实源和更新规则**，不复制具体命令、配置、用例或代码细节，避免形成额外的事实源。

> 说明：本文档集用于说明“设计/边界/证据/治理”，不是对代码版本或发布状态的重复记录。代码仓库版本与文档集版本应分别维护：当前仓库版本为 `0.4.0`，文档集当前版本为 `v0.1`。

## 目录

- [1. 文档清单](#1-文档清单)
- [2. 职责边界](#2-职责边界)
- [3. 按角色阅读路径](#3-按角色阅读路径)
- [4. 当前状态](#4-当前状态)
- [5. 单一事实源](#5-单一事实源)
- [6. 推荐工作流](#6-推荐工作流)
- [7. Definition of Done](#7-definition-of-done)
- [8. 当前缺口](#8-当前缺口)
- [9. 常用命令](#9-常用命令)
- [10. 事实源与设计决策](#10-事实源与设计决策)
- [11. 相关仓库文档](#11-相关仓库文档)
- [12. 维护规则](#12-维护规则)

## 1. 文档清单

| 文档 | 类型 | 版本/状态 | 主要读者 |
| --- | --- | --- | --- |
| [`spec.md`](./spec.md) | 总览：项目定位、设计模式、实现边界、审查清单 | `v0.1`；可用 | 维护者、贡献者 |
| [`architecture.md`](./architecture.md) | 架构概览：上下文、模块依赖、扩展/请求生命周期、状态所有权、关键决策、失败边界 | v0.1；可用 | 新贡献者、架构评审 |
| [`database.md`](./database.md) | 数据库规范：连接、session、查询边界、事务与数据所有权 | v0.1；可用 | 数据库/架构开发者 |
| [`plugin.md`](./plugin.md) | 插件机制：扩展契约、依赖排序、生命周期、作者检查清单 | v0.1；可用 | 扩展作者、架构审查 |
| [`testing.md`](./testing.md) | 测试驱动：分层、用例、E2E、性能、覆盖率、CI | v0.1 工作稿；部分待落地 | 测试、贡献者 |
| [`demo.md`](./demo.md) | 示例驱动：`examples/demo` 编写与维护指南 | v0.1；可用 | 示例维护者、贡献者 |
| [`security.md`](./security.md) | 安全治理：威胁模型、认证/授权、令牌、CSRF、TFA、JWT、风险与检查清单 | v0.1；可用 | 维护者、安全评审、部署者 |
| [`view.md`](./view.md) | View/Admin 专题：路由、ModelView、DataBackend、表单、Inline、AJAX、导出、模板 | v0.1；可用 | Admin/View 开发者 |
| [`requirements.md`](./requirements.md) | 行为契约目录：`REQ-*` 编号、前置/输入/行为/错误/不变量/验收 | v0.1（首批 49 条）；可用 | 维护者、测试、贡献者 |
| [`code-review.md`](./code-review.md) | 独立第三方代码审查标准：独立性、严重度、流程、检查清单、证据、报告模板、签核 | v0.1；可用 | 第三方审查者、安全评审、发布负责人 |
| [`glossary.md`](./glossary.md) | 术语统一表：关键概念、英文名、定义与使用规范 | v0.1；可用 | 维护者、AI 代理、审查者 |
| [`release.md`](./release.md) | 版本与发布说明：状态、影响范围、检查清单、回滚条件 | v0.1；可用 | 维护者、发布者、审查者 |
| [`decisions.md`](./decisions.md) | 事实源治理规则、ADR 模板/登记、变更影响、AI 执行协议、文档漂移检测 | v0.1；可用 | 文档维护者、AI 代理、审查者 |
| `README.md`（本文） | 文档索引与治理规则 | v0.1；可用 | 所有人 |
| [`AGENTS.md`](./AGENTS.md) | 文档维护规则：事实源、修改流程、写作规范、验证清单 | v0.1；可用 | AI 代理、文档维护者 |

> 章节编号只在各文档目录中维护；本文不重复记录章节范围，避免索引漂移。

## 2. 职责边界

| 文档 | 回答什么问题 | 不负责什么 |
| --- | --- | --- |
| `spec.md` | 项目是什么、设计模式、实现细节、代码为什么这样写、关键风险与注意事项 | 不是逐行 API 参考，不是测试执行手册，不是示例教程 |
| `architecture.md` | 系统边界、模块依赖、生命周期、请求路径、状态所有权、关键决策、失败边界 | 不重复实现细节与安全清单 |
| `database.md` | 数据库边界、session 生命周期、查询/过滤/分页与数据所有权 | 不重复业务需求与安全策略 |
| `plugin.md` | 扩展注册、依赖排序、初始化/后初始化/关闭、扩展作者契约 | 不重复业务需求与具体页面行为 |
| `testing.md` | 测什么、怎么分层、用例 ID、fixtures、E2E/性能方案、覆盖率与 CI 门禁 | 不重复架构说明；不代替实际测试代码 |
| `demo.md` | `examples/demo` 如何运行、如何组织、如何扩展、如何排错 | 不是库的完整 API 文档，不是生产部署指南 |
| `security.md` | 安全边界是什么、威胁模型、控制措施、已知风险、配置基线与发布检查 | 不代替安全审计/渗透测试；不重复测试执行细节 |
| `view.md` | View/Admin 如何路由、配置列/表单/筛选/排序/搜索、Inline/AJAX/导出、实现自定义后端 | 不重复项目架构与安全策略；不代替测试代码 |
| `requirements.md` | 每条行为契约的 `REQ-*`、前置/输入/行为/输出/错误/不变量/验收 | 不写实现细节；不代替测试代码与安全威胁模型 |
| `code-review.md` | 独立第三方审查的独立性、范围、严重度、流程、检查清单、证据、报告与签核 | 不替代当前缺陷清单；不是法律/合规认证 |
| `README.md` | 各文档如何配合、事实以谁为准、改动如何闭环 | 不承载具体技术细节 |

关系：

```text
requirements.md  ──定义契约/验收──▶  testing.md  ──验证契约──▶  代码与测试
       ▲                                                        │
       │                                                        ▼
       ├──────────────  demo.md（可运行示例/验收） ◀────────────┘
       │
       ├──────────────  architecture.md（系统边界/模块依赖） ◀─────┘
       │
       ├──────────────  database.md（数据库边界/数据所有权） ◀──────┘
       │
       ├──────────────  plugin.md（扩展契约/生命周期） ◀────────────┘
       │
       ├──────────────  view.md（View/Admin 实现与配置） ◀────────┘
       │
       ├──────────────  security.md（安全边界/风险/检查） ◀──────┘
       │
       └──────────────  spec.md（项目总览/设计背景） ◀─────────────┘
```

## 3. 按角色阅读路径

| 角色/任务 | 建议顺序 |
| --- | --- |
| 第一次接触项目 | 本文 → `architecture.md` 1–4 章 → `spec.md` 1 章 → `demo.md` 0 章 |
| 写新功能 | `requirements.md` 对应 `REQ-*` → `testing.md` 第 7 章用例 → 代码 → `demo.md` 对应 recipe |
| 修缺陷 | `requirements.md` 相关契约 → `view.md` 第 16 章 / `security.md` 第 11 节 → `testing.md` 相关用例 → 先写失败测试 → 修复 |
| 写测试 | `requirements.md` 的 REQ → `testing.md` 4–7 章、15 章 → 现有 `tests/` 模式 |
| 写契约/需求 | `requirements.md` 1–2 章 → 补充 `REQ-*` 与验收映射 |
| 改 demo | `demo.md` 2–9 章 → `examples/demo` → 按 11 章验证 |
| 改 View/Admin | `view.md` 1–15 章 → `architecture.md` 2/4 章 → `testing.md` 7.3 节 |
| 做架构评审 | `architecture.md` 1–8 章 → `requirements.md` → `security.md` → `view.md` |
| 做第三方代码审查 | `code-review.md` 0–10 章 → `requirements.md` → `architecture.md` → `security.md` → `testing.md` |
| 做安全评审 | `security.md` 1–11 章 → `testing.md` 第 7.5/7.12 节 → 第 12 章缺口 |
| 做发布 | `testing.md` 10–11、16 章 → `security.md` 第 14 章 → 本文第 7 节 |
| 做质量门禁 | `testing.md` 10–11 章 → `security.md` 第 12、14 章 → 本文第 5、8 节 |

## 4. 当前状态

| 项目 | 状态 |
| --- | --- |
| 文档集 | 总览 + 多个扩展专题文档 + 索引 + `AGENTS.md` 已建立 |
| `spec.md` | 可用；承担项目总览角色，View/Admin 细节已迁至 `view.md` |
| `architecture.md` | v0.1；系统上下文、模块依赖、生命周期、请求路径、状态所有权、关键决策 |
| `testing.md` | **v0.1 工作稿**；用例设计完整，但 fixtures、markers、`tests/e2e/`、`tests/performance/`、覆盖率基线尚未落地 |
| `demo.md` | v0.1；已按 `examples/demo` 实际代码校准，并记录已知问题 |
| `security.md` | v0.1；已按当前安全实现校准，列出 SEC-01～SEC-19 风险与测试缺口 |
| `view.md` | v0.1；已承接原 3.7、3.8、4.3、5.5、5.6 与 Admin API 速查 |
| `requirements.md` | v0.1；49 条首批契约，31 implemented / 13 partial / 5 known-gap |
| `code-review.md` | v0.1；独立第三方审查标准、严重度、检查清单、报告模板与签核 |
| 项目代码 | 未因本轮文档工作修改 |
| 文档构建 | 主文档不在 Sphinx `flask-exts/docs/` 内，不参与构建 |
| 源码复核 | 未复核（文档集未附带 `flask-exts` 源码快照） |

**已知的文档级限制：**

- 文档集未附带 `flask-exts` 源码快照；2026-11-07 的代码/测试事实（文件路径、函数名、46/193/916 等）未在当前环境复核。
- `requirements.md` 已建立 49 条首批契约，但 `testing.md` 的用例尚未全部标注 `REQ-*`（当前仅引用 10 个唯一 `REQ-*`）。
- `spec.md` 的 3.7/3.8/4.3/5.5/5.6 已改为指针，View/Admin 细节以 `view.md` 为准。
- `requirements.md` 12.1a 的 `REQ → CASE` 映射仅覆盖 14/49 条，其余条目以各契约的“验收”字段为准。
- `demo.md` 与 `examples/README.rst` 仍各有一份启动命令；对外命令以 `examples/README.rst` 为准。
- `demo.md` 的冒烟步骤是手工脚本，尚未进入 CI。
- `security.md` 中标记为“风险/待决策”的 SEC-01～SEC-03 仍需代码或部署层处理。
- API 参考尚未由 Sphinx 自动生成。

## 5. 单一事实源

同一事实只允许一个权威来源；其他文档只引用，不复制。

本表是事实源映射的唯一维护位置；`decisions.md`、`AGENTS.md` 只保留规则与指针。

| 事实 | 权威来源 | 说明 |
| --- | --- | --- |
| 项目定位、设计模式、实现细节 | `spec.md` | 说明“为什么这样设计/当前怎么实现” |
| 系统边界、模块依赖、运行时架构 | `architecture.md` | 稳定的架构一页纸；不重复实现细节 |
| 数据库边界、session、事务、数据所有权 | `database.md` | 不重复业务需求与安全策略 |
| 扩展注册、依赖排序、生命周期、作者契约 | `plugin.md` | 不重复具体页面行为 |
| 行为契约、REQ 编号、验收标准 | `requirements.md` | 说明“系统应该怎样”；修改契约必须先改这里 |
| 第三方代码审查标准/流程 | `code-review.md` | 独立性、严重度、证据、报告、签核；不替代缺陷清单 |
| 当前实际行为 | 源码 + 测试 | 实现层；与契约冲突时按第 6 节处理 |
| 测试策略、用例、门禁 | `testing.md` | 测试未落地时标“待补”，不能写成“已实现” |
| 安全边界、威胁模型、风险清单 | `security.md` | 安全配置与发布前安全检查以本文为准；发布流程门禁见 `release.md` |
| 认证/授权/令牌的契约边界 | `security.md` + `requirements.md` | 冲突时以需求为行为契约、安全为边界 |
| View/Admin 实现与配置 | `view.md` | 原 `spec.md` 3.7/3.8/4.3/5.5/5.6 与 Admin API 速查已迁入 |
| 可执行示例代码 | `flask-exts/examples/demo` | `demo.md` 镜像完整 demo 类；`view.md` 只保留最小 API 片段 |
| 示例运行命令（对外） | `flask-exts/examples/README.rst` | 被 `flask-exts/docs/examples.rst` 引用；`demo.md` 只展开说明 |
| Demo 内部结构、recipes、排错 | `demo.md` | 命令与 `examples/README.rst` 冲突时，以 README 的对外命令为准 |
| 配置项 | `flask-exts/docs/configure.rst` | `demo.md` 只说明 demo 显式设置与差异 |
| 公开 API 参考 | Sphinx `autosummary`（目标） | 当前未生成；不要用 `spec.md` 冒充 API 参考 |
| 开发规范、边界 | `flask-exts/AGENTS.md` | 提交、依赖、格式化、变更许可 |
| 版本号 | `flask-exts/src/flask_exts/__about__.py` | 不在文档中手工维护版本号 |

**禁止：**

- 在 `testing.md` 里重复完整的架构说明；应链接 `spec.md`。
- 在 `demo.md` 里重复完整配置表；应链接 `flask-exts/docs/configure.rst`。
- 在 `spec.md` 里重复测试执行细节；应链接 `testing.md`。
- 在不同文档里维护互相矛盾的启动命令、配置默认值或测试计数。

**来源边界：** 本文档集只允许两类事实来源：本目录 Markdown 文档与 `flask-exts` 仓库（含其 Sphinx 文档与运行产物）。不得引入第三方文档、外部链接或未登记的历史材料；确需外部引用时，先在本节登记名称、路径与可达性，否则只能标为“待确认”。

### 兼容性与发布门禁

发布前门禁、兼容性策略、回滚条件与发布说明模板统一在 [`release.md`](./release.md) 维护；本节不复制清单。涉及发布或兼容性判断时，按 `release.md` 第 3、4、6 节执行。

## 6. 推荐工作流

不是单向瀑布，而是闭环：

```text
1. 契约/需求 + 架构/安全影响
   requirements.md（REQ-*）+ architecture.md + security.md
        │
        ▼
2. 测试设计（先红）
   testing.md 用例 + tests/ 失败测试
        │
        ▼
3. 实现（转绿）
   src/flask_exts/
        │
        ▼
4. Demo 验收
   examples/demo + demo.md
        │
        ▼
5. 文档与发布准备
   requirements.md / architecture.md / spec.md / testing.md / demo.md / security.md / view.md
        │
        ▼
6. CI 与验收
   unit + integration + coverage + docs + demo smoke
   + 发布/安全变更按 code-review.md 做第三方审查
        │
        └──────────────▶ 下一轮
```

| 步骤 | 必须产出 | 检查点 |
| --- | --- | --- |
| 1. 契约 | `REQ-*`、行为、边界、错误路径、架构/安全影响 | 是否与现有契约冲突？是否新增/修改 `REQ-*`？模块边界是否变化（同步 `architecture.md`）？是否改变认证/授权/令牌/CSRF/TFA？ |
| 2. 测试 | 用例 ID、失败测试 | 测试是否先于实现失败？是否覆盖错误路径与安全用例？ |
| 3. 实现 | 代码 + 通过测试 | 是否保持 Python 3.10+、公共 API 兼容？View/Admin 变更是否同步 `view.md`？是否引入新秘密/日志泄露？ |
| 4. Demo | 可运行示例/配置 | `demo.md` 第 11 章是否通过？是否使用 demo 默认凭据？ |
| 5. 文档 | 相关文档 | 是否出现新的事实源或过期数字？安全风险是否登记？ |
| 6. CI | 绿灯 + 报告 | 覆盖率、文档构建、demo 冒烟是否通过？发布/安全变更是否按 `code-review.md` 完成独立审查？ |

### 冲突处理规则

当“文档说 A、代码做 B”时：

1. **先判断哪边错**：是契约写错，还是实现偏离契约。
2. 契约错：更新 `requirements.md`，同步 `architecture.md`（边界/依赖）、`spec.md`、`view.md`（View/Admin）、`testing.md` 用例、`demo.md` 与 `security.md`。
3. 实现错：保留契约，先写失败测试，再修代码。
4. **禁止**直接把代码现状抄进文档来“消除冲突”。
5. 无法立即修复时，在 `spec.md` 第 7 章登记风险，在 `view.md` 第 16 章登记已知问题，在 `testing.md` 标“待补/待修”，安全相关风险登记到 `security.md` 第 11 节。

## 7. Definition of Done

任何用户可见改动，合并前至少确认：

- [ ] 契约已更新，或明确说明“契约不变”
- [ ] 测试已新增/更新，并能在失败时定位问题
- [ ] 代码实现通过测试
- [ ] 安全影响已评估，`security.md` 的风险/检查清单已更新（如适用）
- [ ] 用户可见行为变化已更新 `demo.md` / `examples/demo`
- [ ] 文档构建 / 链接检查通过
- [ ] CI 绿灯（unit + integration + coverage + docs）
- [ ] 没有提交 `demo.sqlite`、上传文件、日志、密钥

**纯文档改动**至少确认：

- [ ] 事实与当前源码/测试一致，或明确标注“目标/待补”
- [ ] 不产生新的事实源或重复维护
- [ ] 交叉链接有效
- [ ] 数据快照日期已更新（如统计数字变化）

## 8. 当前缺口

### P0：优先补齐

| # | 缺口 | 影响 | 建议 |
| --- | --- | --- | --- |
| P0-1 | `REQ-*` 初版已建立，但测试未全部标注 | 测试仍可能只验证“代码现状” | 在 `testing.md` 用例中补 `REQ-*` 列/注释 |
| P0-2 | `REQ → CASE` 映射仅 14/49 | 无法快速判断每条契约是否被测试/demo 覆盖 | 把 `requirements.md` 12.1a 补齐到全部 `REQ`，并关联 `CASE` 与 demo |
| P0-3 | Demo 无自动冒烟 | `demo.md` 与实际 demo 可能漂移 | 把 `demo.md` 11.3 脚本变成 CI 用例 |
| P0-4 | CI 未覆盖文档/demo | 文档死链、demo 启动失败无法拦截 | CI 增加 `sphinx -W`、链接检查、demo smoke |
| P0-5 | 覆盖率无基线 | `testing.md` 的 85/75/90 无法验收 | 先测基线，再设增量门槛 |
| P0-6 | 安全高风险项未处理 | `security.md` SEC-01/02/03/17 可导致权限绕过、暴力破解或 SMTP MITM | 优先修复 inactive admin、JWT/TFA、限流、SMTP 证书校验 |

### P1：公开发布前

| # | 缺口 | 建议 |
| --- | --- | --- |
| P1-1 | 无自动生成的 API 参考 | 用 Sphinx `autosummary`/`automodule` 生成 |
| P1-2 | 发布流程未固化 | 增加版本号、迁移说明、废弃策略、发布检查清单 |
| P1-3 | 兼容矩阵缺失 | 明确 Python/Flask/SQLAlchemy/数据库/浏览器支持范围 |
| P1-4 | 安全运营未落地 | 审计日志、依赖漏洞扫描、漏洞报告渠道（`security.md` 已给方案，代码/流程待接入） |
| P1-5 | 部署/运维文档缺失 | 生产配置、备份、日志、反向代理、迁移 |
| P1-6 | 性能基线缺失 | 按 `testing.md` 9.7 记录 p50/p95/查询数 |

### P2：长期质量

| # | 缺口 | 建议 |
| --- | --- | --- |
| P2-1 | 无正式 ADR 记录（仅有模板） | 用 `ADR-001…` 记录分层、单例 `db`、不用 `backref` 等决策 |
| P2-2 | 无废弃策略 | 公开 API 变更保留周期与迁移指南 |
| P2-3 | 文档新鲜度靠人工 | 定期跑计数脚本、链接检查、demo 重建 |
| P2-4 | 无浏览器 E2E | Tom Select、模态框、Flatpickr 等 JS 交互 |
| P2-5 | 示例代码块不可执行 | 关键片段纳入 doctest 或示例测试 |

## 9. 常用命令

命令只在权威来源维护，本文不复制：

| 场景 | 权威来源 |
| --- | --- |
| 环境、测试、覆盖率 | `testing.md` 第 0 章 |
| 文档构建 | `testing.md` 第 0.1、11 章 |
| 运行 demo | `flask-exts/examples/README.rst`；内部结构见 `demo.md` 第 0、3 章 |
| 仓库开发规范 | `flask-exts/AGENTS.md` |

## 10. 事实源与设计决策

`decisions.md` 是本目录的治理层，用于统一：

- 事实源治理规则（完整映射表见本文第 5 节）
- 设计决策记录（ADR）模板与登记
- 变更影响评估
- AI 执行协议
- 文档漂移检测

术语定义只在 `glossary.md` 维护；发布门禁、兼容性与回滚只在 `release.md` 维护。

它的目标不是重复领域实现细节，而是维护文档体系的稳定性与可追溯性。

## 11. 相关仓库文档

| 文件 | 用途 |
| --- | --- |
| `AGENTS.md` | 本目录文档维护规则（代理/贡献者） |
| `flask-exts/AGENTS.md` | 项目代码开发规范、变更边界、依赖与提交规则 |
| `flask-exts/docs/configure.rst` | 配置项权威说明 |
| `flask-exts/docs/advanced/modelview.rst` | ModelView/DataBackend/Admin 视图细节 |
| `flask-exts/docs/advanced/database.rst` | 数据库绑定与会话 |
| `flask-exts/docs/advanced/authentication.rst` | 认证与用户中心 |
| `flask-exts/docs/examples.rst` | 示例入口（引用 `examples/README.rst`） |
| `flask-exts/docs/testing.rst` | 项目内英文测试说明 |
| `flask-exts/examples/README.rst` | 示例运行命令的对外权威来源 |
| `flask-exts/pyproject.toml` | 依赖、pytest、Ruff、djLint 配置 |

## 12. 维护规则

### 12.1 更新顺序

1. 契约变化：先改 `requirements.md`，再同步 `spec.md` 与领域文档。
2. 测试变化：再改 `testing.md` 与测试代码。
3. 示例变化：再改 `demo.md` 与 `examples/demo`。
4. 发布变化：最后核对版本与文档一致性。
5. 本索引只在文档职责、状态、单一事实源或缺口变化时更新；具体编辑规则见 `AGENTS.md`。

### 12.2 状态标签

| 标签 | 含义 |
| --- | --- |
| 可用 | 与当前仓库校准，可作为工作依据 |
| 工作稿 | 结构完整，但部分基础设施/数据未落地 |
| 目标 | 尚未实现，不能当作现状 |
| 待补 | 尚无用例/实现 |
| 待修 | 已有测试/实现但不足或未触发缺陷 |
| 待更新 | 已知与源码/测试不一致，需要校准 |

### 12.3 版本与日期

- 每份文档顶部保留“文档版本 / 状态 / 最后更新”；涉及源码/测试事实的文档另加“数据快照”，治理类文档可标“不适用”。
- 版本号跟仓库版本或文档自身版本，不要混用。
- 统计数据变化时，必须同步更新快照日期。
- 发布时检查各文档的版本是否一致。

### 12.4 链接与事实检查

- 交叉链接使用相对路径（本目录内）或绝对仓库路径。
- 不复制大段配置表、命令、用例；使用“见某文档某节”。
- 新增事实前先查第 5 节：是否已有权威来源。
- 无法确认的事实标“待确认”，不要写成确定结论。
