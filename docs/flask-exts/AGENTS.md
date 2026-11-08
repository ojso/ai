# AGENTS.md — flask-exts 文档维护指南

> 本文件是**本目录文档**的项目级规则，面向 AI 代理与人类贡献者。
> **本目录**：指**本文件所在目录**；不依赖外层目录名（`ai/`、`docs/`）是否存在或可见。
>
> **适用范围**：仅本目录下的 Markdown 文档，边界见第 1 节。项目代码、测试、示例、Sphinx 文档以仓库 `flask-exts/AGENTS.md` 和仓库内文档为准。
>
> **冲突处理**：涉及代码/依赖/提交/测试以仓库 `AGENTS.md` 为准；仅涉及本目录文档以本文件为准；无法判断时先询问，不自行扩大修改范围。仓库 `AGENTS.md` 不可见时，仅按本文件执行，且不跨目录修改。
>
> | 项目 | 内容 |
> | --- | --- |
> | 文档版本 | v0.1 |
> | 状态 | 可用 |
> | 最后更新 | 2026-11-08 |

## 1. 适用范围与边界

允许修改：

- `README.md`
- `architecture.md`
- `database.md`
- `plugin.md`
- `requirements.md`
- `code-review.md`
- `spec.md`
- `view.md`
- `security.md`
- `testing.md`
- `demo.md`
- `glossary.md`
- `release.md`
- `decisions.md`
- `AGENTS.md`（本文件）

禁止修改（除非用户明确要求）：

- `flask-exts/` 下的任何源码、测试、示例、配置、Sphinx 文档
- `venv/`、`node_modules/`、`dist/`、`flask-exts/docs/_build/`
- git 历史、标签、远程分支

默认只做**文档编辑**。如果文档与代码不一致，先记录问题；需要改代码时，必须得到用户确认。

## 2. 文档角色与依赖

```text
spec.md 第 1 章（范围/非目标）
        ↓
requirements.md（行为契约 / REQ-*）
        ↓
architecture.md（系统边界/模块依赖/生命周期）
        ↓
spec.md（设计/实现）
view.md（View/Admin 领域）
security.md（安全边界/风险）
        ↓
testing.md（验证）
        ↓
demo.md（可运行验收）
        ↓
README.md（索引/状态）
```

| 文档 | 负责 | 不负责 |
| --- | --- | --- |
| `README.md` | 索引、职责边界、单一事实源、更新规则 | 不承载具体技术事实 |
| `glossary.md` | 术语统一、英文/代码名、定义与使用规范 | 不替代实现细节 |
| `release.md` | 版本状态、影响范围、发布检查和回滚 | 不替代需求/安全文档 |
| `decisions.md` | 事实源治理规则、ADR 模板、变更影响、AI 执行协议、文档漂移检测（映射/术语/发布明细分别见 `README.md`/`glossary.md`/`release.md`） | 不替代领域实现文档 |
| `requirements.md` | `REQ-*`、前置/输入/行为/输出/错误/不变量/验收 | 不写实现细节 |
| `architecture.md` | 系统上下文、模块依赖、生命周期、请求路径、状态所有权、关键决策、失败边界 | 不重复实现细节与安全清单 |
| `database.md` | 数据库边界、session 生命周期、查询规则、数据所有权、事务约束 | 不重复业务需求与安全策略 |
| `plugin.md` | 扩展注册、依赖排序、初始化/后初始化/关闭、扩展作者契约 | 不重复业务需求与具体页面行为 |
| `code-review.md` | 独立第三方审查的独立性、范围、严重度、流程、清单、证据、报告、签核 | 不替代缺陷清单；不是法律/合规认证 |
| `spec.md` | 项目全景、设计模式、实现细节、审查 | 不重复完整契约/架构概览/测试用例 |
| `view.md` | View/ModelView/DataBackend、表单、Inline、AJAX、导出、模板 | 不重复安全威胁模型 |
| `security.md` | 威胁模型、认证/授权、令牌、CSRF、TFA、JWT、风险与发布检查 | 不代替安全审计/渗透测试 |
| `testing.md` | 测试策略、用例、E2E、性能、覆盖率、CI | 不定义契约；不代替测试代码 |
| `demo.md` | `examples/demo` 的运行、结构、扩展、排错 | 不是生产模板，不是完整 API 文档 |

## 3. 事实源与冲突处理

完整的事实源映射表只在 `README.md` 第 5 节维护；本节不复制。

冲突处理：

1. 先判断是“契约错”还是“实现错”。
2. 契约错：改 `requirements.md`，同步 `architecture.md`（边界/依赖）、`spec.md`、`view.md`、`security.md`、`testing.md`、`demo.md`。
3. 实现错：保留契约，先在 `testing.md` 补失败用例，再改代码（需用户确认）。
4. 不允许把代码现状直接抄进文档来“消除冲突”。
5. 无法立即修复：状态标 `known-gap`，关联 `SEC-*` / `C*` / `V-*`。

## 4. 修改前必须做

1. 阅读 `README.md` 与相关文档的目录。
2. 找到对应的 `REQ-*`；没有就判断是否需要新增契约。
3. 涉及当前行为时，只读查看源码/测试，不要修改。
4. 明确本次是：
   - 契约变更
   - 架构/设计说明
   - View/安全领域说明
   - 测试方案
   - 示例指南
   - 纯索引/状态更新
5. 确认不会新增重复事实源。

## 5. 修改规则

### 5.1 契约

- 一个 `REQ-*` 只描述一个可验证行为。
- 编号永不复用；废弃保留编号并标 `deprecated`。
- 必须包含：状态、前置、输入、行为、输出/副作用、错误、不变量、验收。
- 状态只使用：
  - `implemented`
  - `implemented-partial`
  - `known-gap`
  - `proposed`
  - `deprecated`
- `known-gap` 必须关联 `security.md` 的 `SEC-*` 或 `view.md` 的 `C*`/`V-*`。
- 不要把“计划/应该”写成“已实现”。

### 5.2 架构与领域文档

- `spec.md` 负责“为什么这样设计/当前怎么实现”。
- `view.md`/`security.md` 负责领域细节；只链接契约，不复制整条 `REQ`。
- 模块行为变化时，先改契约，再改架构/领域说明。
- 代码审查结论与历史审查结论必须分开标注。

### 5.3 测试文档

- 用例从 `REQ-*` 推导，不从实现反推。
- 每个用例尽量标注 `REQ-*`。
- 区分“现有 / 待补 / 待修 / 目标 / 规划”。
- 不把“测试计划”写成“测试已实现”。
- 覆盖率、性能目标必须注明是“基线”还是“目标”。

### 5.4 示例文档

- `demo.md` 的命令必须能实际执行；不能凭猜测写。
- 默认凭据必须标明“仅本地演示”。
- 不把 demo 当生产模板。
- 示例行为变化时，同步 `examples/README.rst`（需用户确认）。

### 5.5 索引文档

- `README.md` 只做索引、职责、单一事实源、状态和更新规则。
- 不复制具体命令、配置表、用例或代码细节。
- 文档角色/状态变化时更新 `README.md`。

## 6. 写作规范

- 文档用中文；代码、命令、标识符用英文。
- 长文档必须有一级标题、目录、章节编号。
- 代码块必须标注语言；围栏必须闭合。
- 表格列数保持一致。
- 内部链接使用相对路径；仓库文件用绝对路径。
- 术语首次出现时给出英文/代码名。
- 不用“显然”“大家都知道”等模糊表述。
- 不写无法从源码/文档验证的结论；不确定时标“待确认”。
- 不写入密钥、令牌、密码、真实用户数据。
- 不粘贴大段三方文档；引用链接即可。
- 统计数据必须注明快照日期与统计口径。

## 7. 验证清单

修改后至少检查：

- [ ] 标题层级与目录锚点一致
- [ ] 代码围栏成对闭合
- [ ] 表格列数一致
- [ ] 本地链接目标存在
- [ ] 新/改的 `REQ-*` 有验收依据
- [ ] `known-gap` 已关联风险编号
- [ ] 没有把“计划”写成“已实现”
- [ ] 没有新增重复事实源
- [ ] 数据快照日期已更新（如统计变化）
- [ ] 仓库 `git status` 为空（除非用户要求改代码）

可用只读命令：

```bash
# 查看文档规模
wc -l -c *.md

# 检查仓库是否被改动
cd flask-exts && git status --short

# 检查 Markdown 围栏数量（应为偶数）
python3 - <<'PY'
from pathlib import Path

for path in sorted(Path("docs").glob("*.md")):
    lines = path.read_text(encoding="utf-8").splitlines()
    fences = sum(1 for line in lines if line.strip().startswith("```"))
    print(f"{path.name}: fences={fences}")
PY
```

不要为了检查而安装新工具；需要新依赖时先询问。

## 8. 禁止行为

- 未经确认修改仓库代码、测试、示例或配置。
- 删除/覆盖用户已有的文档内容而不说明。
- 重写 git 历史、force-push、回滚他人工作。
- 提交密钥、凭据、`.env`、真实用户数据。
- 把 `demo.sqlite`、上传文件、日志加入文档或仓库。
- 声称“已通过安全审计/渗透测试”。
- 把 `known-gap` 或 `proposed` 说成已完成。
- 为了让数字好看而删除测试/契约。
- 在多个文档中维护互相矛盾的启动命令、配置默认值或测试计数。

## 9. 输出格式

完成文档修改后，回复至少包含：

1. **改了哪些文件**
2. **核心变更**（按文档分组）
3. **验证结果**（TOC/围栏/链接/仓库状态）
4. **未解决项/风险**
5. **建议的下一步**（如有）

如果只改了文档，明确说明：

> 未修改任何项目代码，仓库 `git status` 为空。

## 10. 相关文件

| 文件 | 用途 |
| --- | --- |
| `README.md` | 文档索引与治理规则 |
| `architecture.md` | 系统边界、模块依赖、生命周期与关键决策 |
| `requirements.md` | 行为契约目录 |
| `code-review.md` | 独立第三方代码审查标准 |
| `flask-exts/AGENTS.md` | 项目代码/测试/提交规则 |
| `flask-exts/docs/configure.rst` | 配置项权威说明 |
| `flask-exts/docs/advanced/modelview.rst` | ModelView/DataBackend 详细说明 |
| `flask-exts/examples/README.rst` | 示例运行命令对外来源 |
