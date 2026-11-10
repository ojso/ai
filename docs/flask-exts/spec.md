# Flask-Exts 项目设计总纲

> | 项目 | 内容 |
> | --- | --- |
> | 文档版本 | v0.1 |
> | 状态 | 可用 |
> | 最后更新 | 2026-11-09 |
> | 数据快照 | 2026-11-07（仓库版本 `0.4.0`；未复核） |
> | 目的 | 说明项目定位、设计边界与关键取舍，并维护 View/Admin、插件和数据库专题；不重复写需求、安全和测试细节 |

## 目录

### 第一部分：设计总纲与背景

- [1. 项目定位](#1-项目定位)
- [2. 文档职责边界](#2-文档职责边界)
  - [2.1 扩展专题与归属](#21-扩展专题与归属)
- [3. 设计目标](#3-设计目标)
  - [3.1 首版缺口与优先级（历史快照）](#31-首版缺口与优先级历史快照)
- [4. 关键设计取舍与架构定位](#4-关键设计取舍与架构定位)
- [5. 当前结构概览](#5-当前结构概览)
- [6. 当前状态判断](#6-当前状态判断)
- [7. 关键风险与注意事项](#7-关键风险与注意事项)
- [8. 适合的阅读顺序](#8-适合的阅读顺序)
- [9. 设计总纲小结](#9-设计总纲小结)

### 第二部分：核心领域实现规范

- [10. View 与 Admin 专题](#10-view-与-admin-专题)
- [11. 插件与扩展机制](#11-插件与扩展机制)
- [12. 数据库与持久化](#12-数据库与持久化)

## 1. 项目定位

Flask-Exts 是一个面向 Flask 的扩展集合，用于把常见的 Web 基础能力拆成可组合模块：

- 扩展注册与生命周期管理
- SQLAlchemy 数据访问
- Admin / ModelView / DataBackend
- WTForms 表单与 CSRF
- 用户存储与认证
- 令牌、2FA、加密与安全控制
- 邮件、前端资源、国际化、门户页面

它不是一个固定的大型 CMS，也不是只有单一“一体化”框架，而是“基础能力 + 可插拔扩展”的组合式设计。

## 2. 文档职责边界

本文件说明项目设计背景，并分别在第 10、11、12 章维护 View/Admin、插件机制和数据库的领域细节；行为契约、安全、测试、示例和发布内容请转到对应专题文档：

- 行为契约：[`requirements.md`](./requirements.md)
- 架构与依赖：[`architecture.md`](./architecture.md)
- 安全边界：[`security.md`](./security.md)
- 测试方法：[`testing.md`](./testing.md)
- 示例与验收：[`demo.md`](./demo.md)
- 术语统一：[`glossary.md`](./glossary.md)
- 发布门禁与回滚：[`release.md`](./release.md)

### 2.1 扩展专题与归属

本文件承担项目总览及 View/Admin、插件、数据库专题；[`security.md`](./security.md) 和 [`architecture.md`](./architecture.md) 分别维护安全边界及系统架构。

规则是：

- 本文前九章负责项目定位和设计背景，第 10 章负责 View/Admin，第 11 章负责插件与扩展机制，第 12 章负责数据库与持久化领域说明。
- 领域说明负责“这个域如何做、边界是什么、风险是什么”，不替代需求契约和测试代码。
- 若文档之间冲突，按 `README.md` 的事实源和冲突处理规则核对，不以现有实现自动覆盖契约。

## 3. 设计目标

1. 把通用能力拆成独立扩展，便于按需组合。
2. 把初始化过程从“业务感知”中分离出来，形成稳定的扩展生命周期。
3. 在后台视图、数据访问和表单层之间做解耦，减少单点耦合。
4. 将认证、安全、用户存储、Admin 等能力尽量标准化，复用同一套应用上下文。
5. 让工程在早期仍可演进，同时保留对测试、审查和扩展的可验证性。

## 3.1 首版缺口与优先级（历史快照）

> 本节是 v0.1 建立时的缺口清单；其中扩展作者契约、约束、依赖原则、范围外声明等已在本文第 11、12 章及 `architecture.md` 展开。本节保留为历史优先级记录，未逐项复核，阅读时以相关专题为准。

如果只问“还缺什么”，优先级建议如下：

1. 扩展作者的最小契约：定义扩展必须提供什么接口、如何注册、如何初始化、如何关闭。
2. 约束与不变式：明确禁止做什么、必须满足什么语义约束，例如依赖不能循环、初始化前后状态必须稳定。
3. 模块依赖方向/分层原则：明确哪些模块可依赖哪些模块，避免“可组合”变成隐藏耦合。
4. 范围外声明：说明哪些能力不属于本项目，避免无边界扩张。
5. 版本与兼容性策略：说明预期的发布节奏、兼容方式和升级约束。
6. 关键决策的替代方案与理由：让设计取舍可追溯，而不是只留结论。
7. 非功能需求的归属与优先级：如安全、性能、可观测性、可维护性应该落在哪一层文档中。
8. 设计成功标准：定义什么时候可以认为本设计“够成熟”，便于验证和复盘。

这些项不是“可选增强”，而是让扩展集合真正具备可审查、可维护、可扩展的最小工程性要求。

## 4. 关键设计取舍与架构定位

> 架构级的系统决策矩阵（决策、原因与代价）以 [`architecture.md` 第 7 节](./architecture.md#7-关键决策与取舍) 为单一事实源。本节说明各核心设计在规范体系中的归属与承接关系，避免多处重复维护具体实现规则。

### 4.1 扩展生命周期与组装

采用“注册 + 依赖排序 + 两阶段初始化”解耦各扩展的启动顺序：

- **全局运行时调度**（Manager 编排时序、Signal 与异常隔离）：详见 [`architecture.md` 第 3 章](./architecture.md#3-扩展生命周期)。
- **扩展作者规范**（插件契约、`init_app` / `post_init` / `shutdown` 编写约定与检查清单）：详见本文 [第 11 章（插件与扩展机制）](#11-插件与扩展机制)。

### 4.2 Registry / Manager 模式

通过抽象注册表与管理器屏蔽业务对具体扩展实现的直接依赖：

- 模块依赖关系与职责边界见 [`architecture.md` 第 2 章](./architecture.md#2-模块与依赖)。
- 扩展注册器协议、约束与作者检查清单见本文 [第 11.2/11.6 节](#112-核心原则)。

### 4.3 Admin 与 DataBackend 解耦

将后台交互与数据存储分离，使视图逻辑不绑定具体持久化机制：

- 数据层分层约束、session 生命周期与查询规范见本文 [第 12 章（数据库与持久化）](#12-数据库与持久化)。
- View / ModelView 与 DataBackend 的协议交互、表单与已知问题见本文 [第 10 章（View 与 Admin 专题）](#10-view-与-admin-专题)。

### 4.4 安全控制集中化

安全能力不分散在各个业务扩展中，统一收敛到安全扩展与用户存储抽象：

- 完整威胁模型、密钥派生、认证会话、CSRF 与 TFA 等详见 [`security.md`](./security.md)。
- 用户凭据契约与授权规则详见 [`requirements.md`](./requirements.md)。

## 5. 当前结构概览

> 本节反映当前仓库的源码目录结构。各模块在系统中的职责划分与“不应承担”的明确边界，以 [`architecture.md` 第 2 章](./architecture.md#2-模块与依赖) 为权威来源。

```text
flask_exts/
├── extension_core/     # 生命周期与扩展注册
├── builtin_extensions/ # 内置扩展集合
├── datastore/          # 数据库、会话和查询抽象
├── admin/              # 后台、视图与 DataBackend
├── forms/              # 表单与 CSRF
├── security/           # 认证、授权、令牌、2FA
├── userstore/          # 用户存储接口与实现
├── usercenter/         # 用户中心和账户相关视图
├── emailer/            # 邮件发送能力
├── frontend/           # 模板与脚本资源管理
├── portal/             # 门户页
├── commands.py         # CLI
├── proxies.py          # 应用上下文代理
├── signals.py          # 事件信号
└── __about__.py        # 版本信息
```

## 6. 当前状态判断

- 版本：0.4.0
- 文档版本：v0.1
- 目标：作为工程基线和协作入口，而不是最终发布说明
- 当前适用场景：设计评审、扩展开发、测试规划、风险梳理

说明：文档与代码版本应分开维护，不能默认“文档等于实现完成”。

## 7. 关键风险与注意事项

- 运行时隐式依赖可能存在于扩展之间，不能只看依赖声明。
- 早期 API 仍在演进，模块边界可能需要继续细化。
- 历史审查结论不能直接替代当前源码事实。
- View/Admin、插件和数据库细节分别见本文第 10、11、12 章；用户存储与安全边界按对应领域文档核对。

## 8. 适合的阅读顺序

推荐顺序：

1. [README.md](./README.md)
2. [architecture.md](./architecture.md)
3. [requirements.md](./requirements.md)
4. [security.md](./security.md)
5. 本文第 10～12 章（按需查阅 View/Admin、插件、数据库专题）
6. [testing.md](./testing.md)
7. [demo.md](./demo.md)

## 9. 设计总纲小结

这是项目设计以及 View/Admin、插件、数据库领域的工程基线，帮助维护者和 AI 快速回答：

- 这个项目是什么
- 它设计成什么样
- 关键模块如何协作
- 细节去哪看
- 何时该追到安全、测试、发布和 demo 文档

后续演进时，行为契约、架构、安全、测试和 demo 仍以各自的权威来源为准；本文除项目总览外，负责维护第 10～12 章的 View/Admin、插件和数据库领域说明。

## 10. View 与 Admin 专题

> 本章维护 View、ModelView、DataBackend、Inline、AJAX、导出、模板及相关已知问题。数据快照为 2026-11-07，未在当前环境复核；安全边界以 `security.md` 为准，测试策略以 `testing.md` 为准。

### 专题目录

- [10.0 快速开始](#100-快速开始)
- [10.1 View 体系总览](#101-view-体系总览)
- [10.2 Admin 与视图注册](#102-admin-与视图注册)
- [10.3 View 基类与路由](#103-view-基类与路由)
- [10.4 ModelView](#104-modelview)
- [10.5 DataBackend 协议](#105-databackend-协议)
- [10.6 SqlaModelView 与 SqlaBackend](#106-sqlamodelview-与-sqlabackend)
- [10.7 列、格式化、筛选、排序、搜索](#107-列格式化筛选排序搜索)
- [10.8 表单生成](#108-表单生成)
- [10.9 Inline 模型](#109-inline-模型)
- [10.10 AJAX 外键](#1010-ajax-外键)
- [10.11 导出](#1011-导出)
- [10.12 分页与列表参数](#1012-分页与列表参数)
- [10.13 CRUD 与请求流程](#1013-crud-与请求流程)
- [10.14 模板与自定义页面](#1014-模板与自定义页面)
- [10.15 Recipes](#1015-recipes)
- [10.16 已知问题与回归](#1016-已知问题与回归)
- [10.17 测试与追溯入口](#1017-测试与追溯入口)
- [10.18 API 速查](#1018-api-速查)

### 10.0 快速开始

> 本章代码片段只保留**最小 API 签名与用法示例**；内部实现细节不在此复制，以源码为准。完整 demo 类见 `demo.md` 第 5 章与 `flask-exts/examples/demo`。

#### 10.0.1 最小模型视图

```python
from flask_exts.admin.sqla.view import SqlaModelView

from .models.author import Author


class AuthorView(SqlaModelView):
    column_list = ("id", "name", "email")
    column_searchable_list = ("name", "email")
    column_sortable_list = ("id", "name")
    column_default_sort = ("id", True)
    page_size = 20


authorview = AuthorView(Author)
```

注册：

```python
admin = app.extensions["exts"].get_extension("admin").get_admin()
admin.register_view(authorview)
```

访问：

```text
http://localhost:5000/admin/author/
```

#### 10.0.2 最小自定义页面

```python
from flask_exts.admin import View, expose_url, login_required


class AboutView(View):
    @login_required
    @expose_url("/")
    def index(self):
        return self.render_string("<h1>About</h1>")


aboutview = AboutView(name="About", url="about")
admin.register_view(aboutview)
```

- `url="about"` → `/admin/about/`
- `url="/about"` → `/about/`（绝对路径，不加 `/admin` 前缀）
- `allow_access = True` 可公开；否则默认需要 admin 权限

#### 10.0.3 最小 Inline / AJAX 配置

```python
from flask_exts.admin.sqla.inline.inline_model_convert import InlineForm


class AuthorView(SqlaModelView):
    inline_models = (InlineForm(Post, form_columns=("title", "text", "date")),)


class PostView(SqlaModelView):
    ajax_refs = {
        "author": {"fields": ("first_name", "last_name")},
    }
```

> Inline 子模型再配置 `ajax_refs` 会触发已知缺陷 C1（见第 10.16 节）。

### 10.1 View 体系总览

```text
Admin
  └─ 注册多个 View（每个 View 一个 Blueprint）
       ├─ View（自定义页面/动作）
       └─ ModelView（模型驱动）
            ├─ 持有 DataBackend（组合，不是继承）
            └─ SqlaModelView
                 └─ SqlaBackend（SQLAlchemy 实现）
```

| 层 | 职责 | 不负责 |
| --- | --- | --- |
| `Admin` | 视图集合、菜单、Blueprint 注册、渲染上下文 | 具体模型查询 |
| `View` | 路由、访问控制、模板渲染、自定义动作 | 模型 CRUD |
| `ModelView` | 列/筛选/排序/搜索/表单/分页/导出配置与请求编排 | 数据源细节 |
| `DataBackend` | 列/过滤/表单脚手架、列表/单条/CRUD、主键 | 路由、模板 |
| `SqlaModelView` | 用 `SqlaBackend` 实现 SQLAlchemy 模型视图 | 非 SQLAlchemy 数据源 |
| `SqlaBackend` | SQL 查询、自动 JOIN、事务、Inline、AJAX | 视图配置解析 |

设计要点：

- **组合优于继承**：`ModelView` 通过 `DataBackend` 解耦数据源，而不是 `SqlaModelView` 继承一整套后端基类。
- **工厂而非实例**：backend 需要读取 `view` 的配置，所以传 `backend_factory`，等 `self` 构造完成后再创建 backend。
- **配置即类属性**：列、表单、分页、导出等通过类属性声明，构造时解析成内部映射。
- **请求层与数据层分离**：`ModelView` 负责参数解析与渲染，`SqlaBackend` 负责 SQL。

#### 10.1.1 Handler 拆分

`ModelView` 本身很大，但把职责拆给了多个 Handler：

| Handler | 职责 |
| --- | --- |
| `PaginationHandler` | 解析分页/排序/搜索参数，生成列表 URL |
| `FilterHandler` | 解析、应用、生成筛选参数 |
| `FormHandler` | 创建/编辑/删除/列表表单 |
| `RowActionHandler` | 单行操作按钮（查看/编辑/删除/链接） |
| `RowsActionHandler` | 选中多行的批量操作（`@expose_action`） |
| `ExportHandler` | CSV/tablib 导出 |
| `ValueHandler` | 列表/详情/导出的值格式化 |

> **命名注意**：`RowActionHandler`（单数 Row）负责“单行按钮”，`RowsActionHandler`（Rows）负责“批量操作”。两者只差一个 `s`，文件名也只差 `s` 的位置（`rowactions.py` / `rowsaction.py`），非常容易混淆；建议重构时改名为 `RowActionHandler` / `BulkActionHandler`，见第 10.16 节 V-02。

`ModelView` 通过显式转发方法暴露 Handler 能力（如 `get_list_args()`、`get_list_url()`），转发方法本身不在此复制。

优点：

- 每个 Handler 可以独立测试
- `ModelView` 不再无限膨胀
- 转发方法是显式的，便于发现和类型提示

注意：

- Handler 与 View 之间仍有较多属性访问（`self.view.xxx`），改 View 属性名会影响多个 Handler。
- 继承链中 Mixin/Handler 的调用顺序需要保持文档化。

### 10.2 Admin 与视图注册

```python
class Admin:
    def __init__(self, app=None, name="Admin", url="/admin", endpoint="admin", ...): ...
    def init_app(self, app): ...
    def register_view(self, view, is_menu=True, category=None): ...
    def render(self, template, **kwargs): ...
    def render_string(self, source, **kwargs): ...
```

- 每个 `View` 创建自己的 Blueprint；`Admin` 负责注册。
- `register_view` 会设置 `view.admin = self`，并生成 `view_name = name.lower().replace(" ", "")`。
- 同名视图重复注册会抛 `ValueError`。
- `is_menu=False` 可隐藏菜单项（内置 usercenter/portal 使用）。
- `category` 用于菜单分组。
- `render()` 会注入 `admin=self` 与 `get_url`。

示例：

```python
admin.register_view(authorview)
admin.register_view(tagview, is_menu=False)
```

### 10.3 View 基类与路由

#### 10.3.1 构造参数

```python
View(
    name=None,
    endpoint=None,
    url=None,
    template_folder=None,
    static_folder=None,
    static_url_path=None,
)
```

- `name`：显示名，默认类名按 PascalCase 拆分。
- `endpoint`：Flask endpoint 基名，默认类名小写。
- `url`：
  - `None` → `/admin/<endpoint>`
  - `"about"` → `/admin/about`
  - `"/about"` → `/about`（绝对路径）
- `template_folder` / `static_folder`：视图专属模板/静态目录。

#### 10.3.2 路由装饰器

```python
@login_required
@requires_active
@expose_url("/", methods=("GET",))
def index(self): ...
```

| 装饰器 | 作用 |
| --- | --- |
| `expose_url(url, methods=("GET",))` | 登记 URL 与允许方法 |
| `login_required` | Flask-Login 包装，并标记 `_login_required` |
| `requires_active` | 标记需要激活账号（`is_active=True`） |
| `expose_action(name, text, confirmation=None)` | 登记批量/行操作 |

**装饰器顺序**（自上而下）：

```python
@login_required
@requires_active
@expose_url("/settings/", methods=("GET", "POST"))
def settings(self): ...
```

`login_required` 先处理匿名用户（重定向登录），`requires_active` 再由授权器检查 active。

#### 10.3.3 ViewMeta 与访问控制

`ViewMeta` 在类创建时扫描带 `_urls` 的方法，并逐个用访问控制包装（`_wrap_view_func_with_access`）。

包装顺序：

1. 若标记 `_login_required` 且未登录 → 交给 Flask-Login（重定向登录）。
2. `view.allow()` → `admin.allow()` → `current_security.authorize_allow()`。
3. 不允许 → `inaccessible_callback()`，默认 `abort(403)`。

`allow_access = True`：

- 让整个视图可匿名访问（如登录/注册/门户）。
- 绕过授权器的 `is_active` 检查。
- 账号级功能仍需 `@requires_active` 单独保护。

> 授权细节与已知风险（如 inactive admin 绕过）见 [`security.md`](./security.md) 第 4 章。

#### 10.3.4 渲染

```python
def render(self, template, **kwargs): ...
def render_string(self, source, **kwargs): ...
```

- `render()` 用于模板文件；可追加任意关键字参数。
- `render_string()` 用于小页面/内联模板。
- `View` 的 `template_folder` 会加入 Jinja 搜索路径。
- `_headers` 参数可用于设置响应头（如 `NO_CACHE_HEADER`）。

### 10.4 ModelView

#### 10.4.1 构造与初始化顺序

```python
class ModelView(View):
    def __init__(
        self, model, backend_factory, name=None, endpoint=None, url=None, **kwargs
    ): ...
```

- `model`：模型类。
- `backend_factory`：接收 `(model, view, **kwargs)` 的 callable；通常是 `SqlaBackend`。
- `_init_columns()`：解析列/排序/筛选/导出列配置。
- `_init_handlers()`：创建分页、导出、表单、值、行操作等 Handler。
- `_init_components()`：后端自动 JOIN、表单 choices 等。

#### 10.4.2 配置属性

##### 列与展示

| 属性 | 说明 |
| --- | --- |
| `column_list` | 列表列；支持 `"author.email"` 点号路径 |
| `column_details_list` | 详情列；默认同 `column_list` |
| `column_export_list` | 导出列；默认同 `column_list` |
| `column_labels` | `{字段: 显示名}` |
| `column_descriptions` | `{字段: 描述}` |
| `column_choices` | `{字段: {db_value: display_value}}` |
| `column_formatters` | 列表列格式化器 |
| `column_formatters_detail` | 详情列格式化器；默认回退到列表 |
| `column_formatters_export` | 导出列格式化器；默认回退到列表 |
| `column_type_formatters` | 按值类型格式化（列表） |
| `column_type_formatters_detail` | 详情类型格式化 |
| `column_type_formatters_export` | 导出类型格式化 |

格式化优先级：

1. `column_formatters[name]`（列级）
2. `column_choices` 映射
3. `column_type_formatters`（类型级）

格式化器签名：

```python
def formatter(view, model, name):
    return ...
```

类型格式化器签名：

```python
def type_formatter(view, value, name):
    return ...
```

##### 筛选、排序、搜索

| 属性 | 说明 |
| --- | --- |
| `column_filters` | 列名或 `BaseFilter` 实例 |
| `column_sortable_list` | 可排序列；支持 `(label, path)`、`(label, (path1, path2))` |
| `column_default_sort` | 字符串、`(column, desc)` 或 `[(column, desc), ...]` |
| `column_searchable_list` | 可搜索列；支持点号路径 |
| `column_editable_list` | 列表页可内联编辑的列 |

注意：

- `column_default_sort` 多列排序必须是 **list of tuples**；单个 tuple 会被当成一个排序规格。
- `sort` 请求参数是**列表列索引**，不是列名。
- 搜索词支持 `=` 精确、`^` 前缀、`$` 后缀，否则 `%contains%`；多个空格分隔词是 AND，列之间是 OR。

##### 表单

| 属性 | 说明 |
| --- | --- |
| `form_columns` | 创建/编辑表单字段 |
| `create_form_columns` | 仅创建表单字段；默认回退到 `form_columns` |
| `form_excluded_columns` | 排除字段 |
| `form_args` | WTForms 字段参数（label/validators/format 等） |
| `form_widget_args` | 控件渲染参数（rows/readonly/data-* 等） |
| `form_extra_fields` | 无模型列对应的额外字段 |
| `form_choices` | `{字段: [(value, label), ...]}` |
| `base_form_class` | 表单基类，默认 `FlaskForm` |
| `ajax_refs` | AJAX 外键配置 |
| `inline_models` | Inline 子模型配置 |

##### 分页、权限、导出、模板

| 属性 | 默认 | 说明 |
| --- | --- | --- |
| `page_size` | `20` | 默认页大小 |
| `can_set_page_size` | `True` | 是否允许 `?page_size=` |
| `page_size_options` | `(5, 10, 20, 50, 100)` | 允许的页大小白名单 |
| `can_create` | `True` | 是否允许创建 |
| `can_edit` | `True` | 是否允许编辑 |
| `can_delete` | `True` | 是否允许删除 |
| `can_export` | `False` | 是否启用导出 |
| `export_max_rows` | `10000` | 导出最大行数 |
| `export_types` | `("csv",)` | 导出格式 |
| `action_disallowed_list` | `()` | 禁用的批量/行操作名 |
| `list_template` | `admin/model/list.html` | 列表模板 |
| `create_template` | `admin/model/create.html` | 创建模板 |
| `edit_template` | `admin/model/edit.html` | 编辑模板 |
| `details_template` | `admin/model/details.html` | 详情模板 |

#### 10.4.3 列解析

- 列名会解析成 `(字段名, 显示标签)`。
- 未设置时由 backend 脚手架推断。
- 点号路径用于关联列（如 `author.email`）。

#### 10.4.4 权限开关

`can_create` / `can_edit` / `can_delete` 是**视图级功能开关**：

- `False` 时路由重定向回列表，而不是 403。
- 用户是否能进入视图，由 `SimpleAuthorizer` 决定；两者不同。
- `action_disallowed_list` 只影响批量/行操作，不影响单条 CRUD。

### 10.5 DataBackend 协议

```python
class DataBackend(ABC):
    def __init__(self, model, view): ...

    def scaffold_list_columns(self) -> list[str]: ...
    def scaffold_sortable_columns(self) -> dict[str, str | list[str]]: ...
    def scaffold_filter(self, column_path: str) -> list | None: ...
    def scaffold_form(self, form_type: str | None = None) -> type: ...
    def scaffold_list_form(self, validators=None) -> type: ...

    def get_list(
        self, search, filters, sort_field, sort_desc, page, page_size=None
    ) -> tuple[int, list]: ...
    def get_one(self, id): ...
    def get_pk_value(self, obj) -> str: ...

    def create_model(self, model): ...
    def update_model(self, model) -> bool: ...
    def delete_model(self, model) -> bool: ...
    def delete_model_by_pk_ids(self, ids: list) -> int: ...

    def create_ajax_loader(self, name, options): ...  # 可选
```

| 方法 | 责任 |
| --- | --- |
| `scaffold_list_columns` | 默认列表列 |
| `scaffold_sortable_columns` | 默认可排序列 |
| `scaffold_filter` | 某列的过滤器 |
| `scaffold_form` | 创建/编辑表单类 |
| `scaffold_list_form` | 列表内联编辑表单 |
| `get_list` | 返回 `(count, rows)` |
| `get_one` | 按主键取单条 |
| `get_pk_value` | 主键字符串表示 |
| `create_model` / `update_model` / `delete_model` | 单条写操作 |
| `delete_model_by_pk_ids` | 批量删除 |
| `create_ajax_loader` | AJAX 外键加载器（可选） |

自定义后端的最小骨架：

```python
from flask_exts.admin.model.backend import DataBackend


class JsonBackend(DataBackend):
    def scaffold_list_columns(self): ...
    def scaffold_sortable_columns(self): ...
    def scaffold_filter(self, column_path): ...
    def scaffold_form(self, form_type=None): ...
    def scaffold_list_form(self, validators=None): ...
    def get_list(
        self, search, filters, sort_field, sort_desc, page, page_size=None
    ): ...
    def get_one(self, id): ...
    def get_pk_value(self, obj): ...
    def create_model(self, model): ...
    def update_model(self, model): ...
    def delete_model(self, model): ...
    def delete_model_by_pk_ids(self, ids): ...
```

然后用 `ModelView(Model, JsonBackend)` 或自定义 `ModelView` 子类。

> 自定义后端的抽象方法较多；如果只是 SQLAlchemy，优先用 `SqlaModelView`。

### 10.6 SqlaModelView 与 SqlaBackend

#### 10.6.1 构造

```python
class SqlaModelView(ModelView):
    column_type_formatters = SQLA_FORMATTERS
    inline_models = None

    def __init__(self, model, session=None, name=None, endpoint=None, url=None):
        super().__init__(model, SqlaBackend, name, endpoint, url, session=session)
```

- `session` 默认 `db.session`。
- 模型必须有主键；否则 `SqlaBackend` 构造时抛 `ValueError`。
- 复合主键用逗号编码成字符串（`get_pk_value` / `get_one`）。

#### 10.6.2 脚手架规则

| 脚手架 | 规则 |
| --- | --- |
| `scaffold_list_columns` | 包含多对一/多对多关系列；标量列跳过外键 |
| `scaffold_sortable_columns` | 只含单列属性；跳过外键与复合列 |
| `scaffold_filter` | 按列类型生成过滤器；使用 `column_choices` 作为 options |
| `scaffold_form` | 跳过主键、外键、下划线开头字段；关系字段保留 |
| `scaffold_list_form` | 按 `column_editable_list` 生成 |

#### 10.6.3 列表查询顺序

顺序很重要：

1. 搜索/筛选加入 JOIN 条件。
2. 自动 eager load 加入 `joinedload`/`selectinload`。
3. **先计数**，再分页/排序；计数查询会带上 JOIN。
4. 分页 `offset = page * page_size`。
5. 排序支持单列与多列。

#### 10.6.4 自动 eager load

- 多对一：`joinedload`
- 多对多/一对多：`selectinload`
- 目的：减少列表页 N+1。

#### 10.6.5 CRUD 事务

```python
def create_model(self, model): ...
def update_model(self, model): ...
def delete_model(self, model): ...
```

- 写操作失败返回 `None`/`False`，视图层 flash 错误。
- 批量删除失败会 `rollback` 后重新抛异常。
- 视图层不直接操作 session。

#### 10.6.6 已知问题

| 问题 | 说明 |
| --- | --- |
| C2 计数偏大 | `build_count()` 应用 JOIN 但未去重；一对多搜索/筛选时 `count` 大于根记录数 |
| 复合主键 | 使用逗号编码；主键值本身含逗号时会歧义 |
| 自动 JOIN | 只根据 `column_list` 的根关系推断；复杂路径可能需要手动配置 |

### 10.7 列、格式化、筛选、排序、搜索

#### 10.7.1 列与标签

```python
class PostView(SqlaModelView):
    column_list = ("id", "author", "author.email", "title", "tags")
    column_labels = {
        "title": "Post Title",
        "tags.name": "Tags Name",
        "author.first_name": "Author's first name",
    }
    column_descriptions = {"color": "favorite color"}
```

#### 10.7.2 自定义格式化器

```python
from markupsafe import Markup


def phone_number_formatter(view, model, name):
    return Markup(f"<nobr>{model.phone_number}</nobr>") if model.phone_number else None


class AuthorView(SqlaModelView):
    column_formatters = {"phone_number": phone_number_formatter}
```

注意：

- `Markup` 绕过 Jinja 转义；仅用于可信数据。
- 格式化器返回 `None` 时按空值处理。
- 导出/详情可分别用 `column_formatters_export` / `column_formatters_detail`。

#### 10.7.3 类型格式化器

```python
from flask_exts.admin.model.type_formatters import BASE_FORMATTERS

MY_FORMATTERS = dict(BASE_FORMATTERS)
MY_FORMATTERS[type(None)] = lambda view, value, name: "—"


class AuthorView(SqlaModelView):
    column_type_formatters = MY_FORMATTERS
```

优先级低于列级格式化器。

#### 10.7.4 自定义过滤器

```python
from flask_exts.admin.sqla.filter.filters import BaseSQLAFilter


class FilterNameBrown(BaseSQLAFilter):
    def __init__(self, column_type, column, name, data_type=None, options=None):
        super().__init__(
            column_type,
            column,
            name,
            data_type,
            options=(("1", "Yes"), ("0", "No")),
        )

    def apply(self, query, value):
        if value == "1":
            return query.add_filter(self.column, "==", "Brown")
        return query.add_filter(self.column, "!=", "Brown")

    def operation(self):
        return "is Brown"
```

要点：

- `apply()` 必须调用 `query.add_filter(...)`；后端忽略返回值。
- `operation()` 是筛选下拉显示的操作名。
- `options` 是 `(value, label)` 列表。
- 可直接混用列名与过滤器实例。

#### 10.7.5 排序

```python
class PostView(SqlaModelView):
    column_default_sort = ("date", True)
    column_sortable_list = (
        "id",
        "title",
        "date",
        ("author", ("author.last_name", "author.first_name")),
    )
```

- `column_default_sort` 多列用 list：
  ```python
  column_default_sort = [("last_name", False), ("first_name", False)]
  ```
- `sort` 是列表列索引；`desc=1` 表示降序。
- 多列排序通过 `(label, (path1, path2))` 表达。

#### 10.7.6 搜索

```python
class PostView(SqlaModelView):
    column_searchable_list = ("title", "author.first_name", "author.last_name")
```

- 支持点号路径。
- 搜索词：
  - `=foo` 精确
  - `^foo` 前缀
  - `foo$` 后缀
  - `foo` 包含
- 空格分隔多个词 = AND；列之间 = OR。

#### 10.7.7 内联编辑

```python
class PostView(SqlaModelView):
    column_editable_list = ("color",)
```

- 列表页通过 `/ajax/update/` 保存。
- 需要字段可编辑、表单可生成、CSRF 正确。

### 10.8 表单生成

#### 10.8.1 转换器组合

```python
class ModelFieldConverter(
    BasicFieldConverter,
    TemporalFieldConverter,
    SpecialFieldConverter,
    BaseFormFieldConverter,
): ...
```

职责：

- 按 SQLAlchemy 列类型选 WTForms 字段。
- 处理布尔、日期/时间、枚举、JSON、关系。
- 应用 `form_args`、`form_choices`、`form_widget_args`。
- 生成标签、描述、校验器（如 `Unique`）。
- 关系字段用 `QuerySelectField` / `QuerySelectMultipleField` 或 AJAX 字段。

#### 10.8.2 字段选择

```python
class AuthorView(SqlaModelView):
    create_form_columns = ("type", "last_name", "first_name", "email")
    form_columns = ("id", "type", "last_name", "first_name", "email")
    form_excluded_columns = ("posts",)
    form_args = {
        "email": {"validators": [DataRequired()]},
    }
    form_widget_args = {"id": {"readonly": True}}
```

规则：

- `create_form_columns` 只影响创建；未设置时回退 `form_columns`。
- 未设置 `form_columns` 时由 backend 推断：跳过主键、外键、下划线字段。
- `form_excluded_columns` 优先级高于自动推断。
- `form_extra_fields` 可加入无模型列的字段；必要时配合 `form_columns` 控制顺序。

#### 10.8.3 关系字段与编辑页过滤

```python
def edit_form(self, *args, **kwargs):
    return self._filtered_posts(super().edit_form(*args, **kwargs))


def _filtered_posts(self, form):
    form.featured_post.query_factory = lambda: (
        self._backend.session.execute(
            select(Post).where(Post.author_id == form.id._value())
        )
        .scalars()
        .all()
    )
    return form
```

- 关系字段默认加载全部候选；可通过 `query_factory` 限制。
- 注意在 `edit_form` 中做，而不是 `create_form`。

> 该历史示例在 View 中直接访问 backend 的 session，与第 12.4 节的分层约束存在张力；具体边界待核实。

#### 10.8.4 CSRF

- 表单默认使用 `FlaskForm`，CSRF 由全局 `CSRF_ENABLED` 控制。
- 测试中常关闭 CSRF；生产保持开启。
- 自定义 AJAX 保存必须携带 `csrf_token`。

### 10.9 Inline 模型

#### 10.9.1 配置形式

```python
inline_models = (
    Post,
    (Post, {"form_columns": ("title", "text")}),
    InlineForm(
        Post, form_columns=("title", "text"), form_args={"title": {"label": "Title"}}
    ),
)
```

#### 10.9.2 转换流程

1. `get_inline_form(prop)`：把模型/元组/`InlineForm` 统一成 `InlineForm`。
2. `process_ajax_refs(inline_form)`：处理 AJAX 外键。
3. `_calculate_mapping_key_pair(model, info)`：找父子关系的前向/反向属性。
4. `contribute(model, form_class, inline_model)`：生成子表单并加入父表单。

关系发现：

- 从子模型出发遍历 `iterate_properties`，筛选指向父模型的 `MANYTOONE` / `MANYTOMANY` 关系。
- 优先 `back_populates`；找不到再遍历候选；仍找不到抛 `ValueError`。
- 支持一对多、一对一、多对多。

#### 10.9.3 AJAX 保存

- `POST /admin/<view>/ajax/create-parent/`
- `POST /admin/<view>/ajax/inline/<relationship_name>/`
  - `action=save` 保存子记录
  - `action=delete` 删除子记录
- 需要 CSRF token；后端会校验。

#### 10.9.4 已知缺陷 C1

`process_ajax_refs` 调用 `self.view.create_ajax_loader(...)` 时传 5 个参数，但签名是 `(name, options)`；完整复现证据见第 10.16 节 C1。

后果：Inline 子模型配置 `ajax_refs` 时直接 `TypeError`。修复方向：

- 统一 `create_ajax_loader` 签名；或
- Inline 里先构造 `AjaxSqlaModelLoader` 并赋值。

修复后补测试：`tests/integration/admin/sqla/test_inline_ajax.py`。

### 10.10 AJAX 外键

#### 10.10.1 配置

```python
class PostView(SqlaModelView):
    ajax_refs = {
        "author": {
            "fields": ("first_name", "last_name"),
            "placeholder": "Please select",
            "minimum_input_length": 0,
            "page_size": 10,
        },
    }
```

- 键：外键字段名。
- `fields`：搜索匹配的关联模型列。
- `minimum_input_length`：输入多少字符后查询。
- `page_size`：下拉分页大小。
- `placeholder`：控件提示。

#### 10.10.2 路由

- `GET /admin/<view>/ajax/lookup/?name=author&query=...`
- `POST /admin/<view>/ajax/update/`（列表内联编辑）

`AjaxModelLoader` 接口：

```python
def get_one(pk): ...
def get_list(term, offset=0, limit=DEFAULT_PAGE_SIZE): ...
def format(model):
    return (id, text)
```

`SqlaBackend.create_ajax_loader(name, options)` 返回 `AjaxSqlaModelLoader`。

#### 10.10.3 注意事项

- 关联模型的 Admin 视图最好已注册，便于前端跳转/权限一致。
- `ajax_refs` 与 Inline 同时使用时注意 C1。
- AJAX 更新需要 CSRF。

### 10.11 导出

#### 10.11.1 配置

```python
class PostView(SqlaModelView):
    can_export = True
    export_types = ("csv", "xls")
    export_max_rows = 1000
    column_export_list = ("id", "title", "author", "date")
    column_formatters_export = {"date": lambda v, m, n: m.date.date()}
```

- `can_export=False`（默认）时没有导出按钮/路由。
- `export_max_rows` 限制导出查询。
- `column_export_list` 未设置时回退 `column_list`。
- `column_formatters_export` 未设置时回退 `column_formatters`。

#### 10.11.2 行为

- CSV 使用流式 `Response`。
- 其他格式走 tablib；`xls`/`xlsx` 需要额外依赖（如 `tablib[xls]`）。
- 不支持的格式会 flash 错误并重定向回列表。
- 导出格式化器不支持宏（`inner` 名称会抛 `NotImplementedError`）。
- 文件名经过 `secure_filename`。

### 10.12 分页与列表参数

#### 10.12.1 请求参数

| 参数 | 含义 |
| --- | --- |
| `page` | 页码，**从 0 开始** |
| `page_size` | 页大小；必须在白名单内 |
| `sort` | 排序列索引（列表列下标） |
| `desc` | `1` 表示降序 |
| `search` | 搜索词 |
| `flt*` | 过滤器参数 |
| 其他 | 放入 `extra_args`，分页/排序时保留（`url`、`flt*` 除外） |

#### 10.12.2 解析

```python
ViewArgs(
    page=request.args.get("page", 0, type=int),
    page_size=request.args.get("page_size", 0, type=int),
    sort=request.args.get("sort", None, type=int),
    sort_desc=request.args.get("desc", None, type=int),
    search=request.args.get("search", None),
    filters=self.view.get_active_filters(),
    extra_args={...},
)
```

`get_safe_page_size`：仅当 `can_set_page_size` 为真且请求值在 `page_size_options` 白名单内时采用，否则回退到 `page_size`。

#### 10.12.3 已知问题 C5/C6

- `hasattr(self, "get_url")` 在 `PaginationHandler` 上永远为假，因为 `get_url` 在 `View` 上；这是死分支（C5）。
- 手写查询字符串没有 URL 编码；搜索词含 `&`、`#`、空格、中文时可能出错（C6）。
- 建议改用 `url_for` + `urlencode`，并补 TC-ADMIN-032 测试。

### 10.13 CRUD 与请求流程

#### 10.13.1 列表请求

```text
GET /admin/<endpoint>/?page=1&sort=0&desc=1&search=foo&flt...
  ├─ ViewMeta 包装后的 index_view
  ├─ get_list_args()
  │    ├─ page/page_size/sort/desc/search
  │    ├─ get_active_filters()
  │    └─ extra_args
  ├─ get_safe_page_size()
  ├─ get_list()
  │    ├─ Query(model)
  │    ├─ apply search
  │    ├─ apply filters
  │    ├─ apply auto joins
  │    ├─ build_count → count
  │    ├─ apply pagination
  │    ├─ apply sorting
  │    └─ build → execute → rows
  ├─ 计算 num_pages
  └─ render(list.html)
```

#### 10.13.2 创建

```text
GET /admin/<endpoint>/new/
  └─ create_form() → scaffold_form("create")

POST /admin/<endpoint>/new/
  ├─ form.validate_on_submit()
  ├─ form.populate_obj(model_instance)
  ├─ create_model(model_instance)
  │    ├─ add
  │    ├─ commit
  │    └─ 失败 rollback
  └─ 重定向
```

`_add_another` / `_continue_editing` 控制提交后行为。

#### 10.13.3 编辑 / 详情 / 删除

- 编辑：`GET/POST /edit/?id=...`；`edit_form(obj=model)`；`update_model`。
- 详情：`GET /details/?id=...`；`get_one`。
- 删除：`POST /delete/`；`delete_form` 校验；`delete_model`。
- `get_redirect_target()` 使用 `safe_redirect_target` 处理 `url` 参数，防止开放重定向。

#### 10.13.4 批量/行操作

- `POST /action/`：批量操作（如批量删除）。
- `action_disallowed_list` 禁用操作。
- `can_delete` 等是视图级开关，不是用户授权。

#### 10.13.5 Inline 表单提交

```text
编辑带 Inline：
  ├─ scaffold_inline_models_form()
  ├─ 子表单字段加入父表单
  ├─ 提交时校验父/子
  ├─ 保存父记录
  ├─ 处理子记录新增/修改/删除
  └─ 失败抛 InlineModelError
```

### 10.14 模板与自定义页面

#### 10.14.1 默认模板

| 模板 | 用途 |
| --- | --- |
| `admin/model/list.html` | 列表 |
| `admin/model/create.html` | 创建 |
| `admin/model/edit.html` | 编辑 |
| `admin/model/details.html` | 详情 |
| `admin/master.html` | 布局/菜单/消息 |

#### 10.14.2 覆盖模板

```python
class TreeView(SqlaModelView):
    list_template = "tree_list.html"

    def render(self, template, **kwargs):
        return super().render(template, foo="bar", **kwargs)
```

```jinja
{% extends "admin/model/list.html" %}

{% block main %}
  <p>Passed from the view: <b>{{ foo }}</b></p>
  {{ super() }}
{% endblock %}
```

常用块：

- `main`
- `model_menu_bar_before_filters` / `model_menu_bar_after_filters`
- `list_table`
- `list_header` / `list_row`
- `empty_list_message`
- `list_pager`
- `tail`

#### 10.14.3 自定义页面

自定义页面的最小示例见第 10.0.2 节；`render_string` 适合小页面，复杂页面用模板 + `render`。`allow_access=True` 公开，否则需要 admin 权限。

### 10.15 Recipes

#### 10.15.1 新增一个模型视图

1. 定义模型。
2. 定义 `SqlaModelView` 子类。
3. `admin.register_view(view_instance)`。
4. 访问 `/admin/<endpoint>/`。

#### 10.15.2 自定义格式化器

见第 10.7.2 节。

#### 10.15.3 自定义过滤器

见第 10.7.4 节。

#### 10.15.4 Inline 子表单

见第 10.9.1 节。

#### 10.15.5 AJAX 外键

见第 10.10.1 节。

#### 10.15.6 自定义列表模板

见第 10.14.2 节。

#### 10.15.7 自定义后端

```python
from flask_exts.admin.model.view import ModelView
from .backend import JsonBackend


class JsonModelView(ModelView):
    column_list = ("id", "name")


jsonview = JsonModelView(MyRecord, JsonBackend)
admin.register_view(jsonview)
```

`JsonBackend` 实现第 10.5 节的协议；不需要 SQLAlchemy。

#### 10.15.8 自定义页面

见第 10.14.3 节。

### 10.16 已知问题与回归

| ID | 严重度 | 位置 | 问题 | 建议 |
| --- | --- | --- | --- | --- |
| C1 | 高 | `admin/sqla/inline/inline_model_convert.py::process_ajax_refs` | 调用 `create_ajax_loader` 传 5 个参数，签名是 `(name, options)` | 统一签名或直接构造 loader |
| C2 | 中 | `datastore/sqla/query.py::build_count` | JOIN 未去重，一对多搜索/筛选计数偏大 | `count(distinct(pk))` 或子查询 |
| C5 | 低 | `admin/model/handlers/pagination.py::get_list_url` | `hasattr(self, "get_url")` 永远为假 | 改用 `url_for` |
| C6 | 低 | 同上 | 手写查询字符串未 URL 编码 | `urlencode` |
| C7 | 低 | `datastore/sqla/query_builders/` | 运行时未使用，和 `Query` 形成两套抽象 | 删除或合并 |
| C10 | 低 | `AdminExtension.post_init` | 晚注册 `AdminViewMixin` 不会被重新扫描 | 文档化/提供刷新方法 |
| V-01 | 中 | `admin/model/view.py::ajax_update` | 只检查 `column_editable_list`，未检查 `can_edit` | 内联编辑可能绕过视图级编辑开关；补 `can_edit` 检查与测试 |
| V-02 | 低 | `admin/model/handlers/rowactions.py` / `rowsaction.py` | `RowActionHandler`（单行）与 `RowsActionHandler`（批量）命名只差一个 `s`，文件名也近似 | 重命名为 `RowActionHandler` / `BulkActionHandler`，文件 `row_actions.py` / `bulk_actions.py` |

其他注意：

- `column_default_sort` 多列必须是 list，不是 tuple。
- 自定义 `apply()` 必须 `query.add_filter(...)`；返回值会被忽略。
- `export_types` 含 `xls` 时需要可选依赖。
- `column_formatters` 用 `Markup` 时注意 XSS。

#### 10.16.1 详细说明

##### C1：Inline AJAX 加载器参数不匹配

当前调用：

```python
# admin/sqla/inline/inline_model_convert.py
loader = self.view.create_ajax_loader(
    inline_form.model, self.session, new_name, name, opts
)
```

当前签名：

```python
# admin/model/view.py
def create_ajax_loader(self, name, options):
    return self._backend.create_ajax_loader(name, options)
```

**复现：** 给 `inline_models` 的子模型配置 `ajax_refs`，访问创建/编辑页。

**建议：** 统一签名。要么让 `create_ajax_loader` 接受 `(model, session, name, field_name, options)`，要么在 Inline 里先构造 `AjaxSqlaModelLoader` 并直接赋值。修复后补测试 `tests/integration/admin/sqla/test_inline_ajax.py`。

##### C2：`build_count` 一对多重复计数

```python
def build_count(self):
    stmt = select(func.count()).select_from(self.root_model)
    stmt = self._apply(stmt)
    return stmt
```

`_apply` 会应用 `_joins`。搜索/筛选涉及一对多关系时，JOIN 后父记录出现多行，`count` 统计的是 JOIN 后的行数。

**复现：**

```python
# Parent 有多个 Child；搜索 Child.name
query = Query(Parent)
query.add_search_term("match", ["children.name"])
count = session.scalar(query.build_count())
# 期望 len(parents)，实际可能是匹配 child 的数量
```

**建议：**

- 对根模型主键做 `count(distinct(pk))`
- 或用子查询：先 `select(distinct(root.pk))` 再 `count(*)`
- 复合主键用 `tuple_` 去重
- 增加一对多搜索的计数测试

##### C5 / C6：`get_list_url`

`PaginationHandler` 没有 `get_url`，所以分支永远走 `else`。同时手写查询字符串没有编码。

**建议：**

- 删除死分支，或在 Handler 中显式持有 view 并调用 `self.view.get_url(".index_view", **kwargs)`
- 使用 `urllib.parse.urlencode` 生成查询字符串
- 补测试：搜索词含空格/`&`/中文时 URL 正确

##### C7：未使用的 query builders

`FilterBuilder`、`JoinBuilder`、`SortBuilder`、`PaginationBuilder` 没有被 `SqlaBackend` 使用。

**建议：** 二选一：

- 接入 `Query`，让 builder 成为唯一查询构造方式
- 删除，减少误导

##### C10：晚注册扩展

`AdminExtension.post_init` 只在初始化阶段扫描一次。`register_extension` 的文档已说明这一点。

**建议：**

- 如果确实需要动态注册，提供显式的 `admin.rescan_views()` 或事件
- 或在 `register_extension` 中对新扩展触发相关扩展的 `post_init`（需要设计幂等与重复注册保护）

##### V-02：RowAction 与 RowsAction 命名混淆

当前有两套很相似但职责不同的处理器：

| 文件 | 类 | 职责 | 主要方法 |
| --- | --- | --- | --- |
| `handlers/rowactions.py` | `RowActionHandler` | 单行按钮：查看/编辑/删除/链接 | `get_row_actions()` |
| `handlers/rowsaction.py` | `RowsActionHandler` | 选中多行的批量操作 | `get_list_actions()`、`get_rows_action()`、`action_form()` |

`ModelView` 中的属性也只差一个字母：`_rowactions_handler`（单行）与 `_rowsaction_handler`（批量）。

`RowsAction` 的命名既不是 `RowActions`，也不是 `BulkActions`，容易让人误以为是“多个单行操作”。建议重构为：

```text
RowActionHandler   → 保持（单行）
RowsActionHandler  → BulkActionHandler
get_rows_action    → get_bulk_action
get_list_actions   → get_bulk_actions
rowsaction.py      → bulk_actions.py
rowactions.py      → row_actions.py（可选）
```

如果 `RowsActionHandler` 是公开 API，先加别名/弃用说明，再在下一个主版本移除旧名。该重构不影响数据库或行为，但需要同步模板 `admin/model/list.html` 中的 `view.get_list_actions()` 与 `view.get_row_actions()`。

<a id="1017-测试映射"></a>

### 10.17 测试与追溯入口

View/Admin 用例、测试缺口与状态以 [`testing.md` 第 7.3 节](./testing.md#73-admin)为准；历史测试文件快照见 [`testing.md` 第 1.2.1 节](./testing.md#121-admin-测试文件快照)，安全相关缺口见 [`testing.md` 第 7.5 节](./testing.md#75-security)。具体 `REQ → TC → 测试入口` 在 [`requirements.md` 对应契约](./requirements.md#11-admin--view)的“验收”字段维护。

问题复现与技术细节仍见第 10.16 节；测试文件或用例引用不代表相关断言存在或执行通过，当前状态须以实际证据核实。

### 10.18 API 速查

> 本节是速查表，只列常用入口；语义见第 10.7～10.15 节，不在本节重复解释。

```python
from flask_exts.admin import Admin, View, expose_url, login_required, requires_active
from flask_exts.admin.sqla.view import SqlaModelView


class MyView(SqlaModelView):
    column_list = ("id", "name")
    column_searchable_list = ("name",)
    column_sortable_list = ("name",)
    form_columns = ("name",)


admin = app.extensions["exts"].get_extension("admin").get_admin()
admin.register_view(MyView(MyModel, name="My", endpoint="my", url="/my"))
```

常用属性：

```text
column_list / column_details_list / column_export_list
column_labels / column_descriptions / column_choices
column_formatters / column_formatters_detail / column_formatters_export
column_type_formatters / column_type_formatters_detail / column_type_formatters_export
column_filters / column_sortable_list / column_default_sort
column_searchable_list / column_editable_list

form_columns / create_form_columns / form_excluded_columns
form_args / form_widget_args / form_extra_fields / form_choices / base_form_class

ajax_refs / inline_models
page_size / can_set_page_size / page_size_options
can_create / can_edit / can_delete / can_export
export_max_rows / export_types
action_disallowed_list
list_template / create_template / edit_template / details_template
```

## 11. 插件与扩展机制

> 本章规范扩展的注册、依赖、生命周期、作者契约和接口边界，不重复业务需求和安全策略。适用范围为扩展集合、扩展注册器、插件约定和内置扩展装配；数据快照为 2026-11-07（仓库版本 `0.4.0`；未复核）。

### 专题目录

- [11.1 适用范围](#111-适用范围)
- [11.2 核心原则](#112-核心原则)
- [11.3 最小作者契约](#113-最小作者契约)
- [11.4 生命周期规范](#114-生命周期规范)
- [11.5 依赖与分层原则](#115-依赖与分层原则)
- [11.6 约束与不变式](#116-约束与不变式)
- [11.7 扩展作者检查清单](#117-扩展作者检查清单)
- [11.8 设计风险](#118-设计风险)
- [11.9 说明](#119-说明)

### 11.1 适用范围

本规范覆盖：

- 扩展注册机制
- 依赖排序与循环依赖检测
- `init_app` / `post_init` / `shutdown` 的生命周期
- 扩展作者最小接口要求
- 扩展之间的隐式协作与显式边界

不覆盖：

- 具体业务功能实现（见本文其他章节 / `requirements.md`）
- 安全控制细节（见 `security.md`）
- View/Admin 细节（见本文第 10 章）

### 11.2 核心原则

1. 扩展必须是可注册、可排序、可初始化、可关闭的组件。
2. 扩展机制要保证“解耦”而不是“隐式强耦合”。
3. 依赖关系必须清晰可审查，不能靠隐式导入和运行时偶然成功。
4. 任何扩展都应具备最小契约：名称、依赖、初始化、后初始化、关闭。
5. 插件机制的职责是“组装”，而不是“替代”业务逻辑。

### 11.3 最小作者契约

扩展作者至少应遵守以下约定：

- 提供唯一名称。
- 遵守依赖声明规则。
- 实现 `init_app(app)`。
- 如需要跨扩展协作，则在 `post_init(app)` 中完成。
- 提供可逆的 `shutdown()` 支持。
- 在初始化前后保持状态稳定。

如果扩展依赖其他扩展，依赖应显式声明，而不是通过全局变量隐式读取。

### 11.4 生命周期规范

> 本节面向扩展编写者，规范扩展自身在各阶段的实现责任；框架整体调度时序与异常隔离详见 [`architecture.md` 第 3 章](./architecture.md#3-扩展生命周期)。

#### 11.4.1 初始化阶段

- `init_app()` 负责绑定扩展到 app。
- 只做扩展自身的初始化，不假设其他扩展都已经准备就绪。

#### 11.4.2 后初始化阶段

- `post_init()` 用于跨插件组装。
- 允许扩展发现其他扩展并建立连接。
- 但此阶段不能制造未声明的强耦合。

#### 11.4.3 关闭阶段

- `shutdown()` 应按逆序释放资源。
- 单个扩展失败不能直接导致整个系统关闭流失控。

### 11.5 依赖与分层原则

- 底层扩展不应依赖上层业务视图。
- 高层扩展可通过声明式接口依赖底层抽象。
- 如果模块之间必须通信，优先选择：
  - 扩展 registry
  - app extensions
  - signals
  - 明确的接口/协议

不推荐：

- 直接从一个扩展导入另一个扩展的实现细节
- 在模块顶层隐式访问全局扩展状态
- 把初始化顺序完全依赖于注册顺序

### 11.6 约束与不变式

- 依赖图不能出现自循环或环路。
- 任何扩展在 `post_init` 前都必须完成 `init_app`。
- 初始化必须幂等，重复调用不得产生重复副作用。
- 扩展名称必须唯一且合法。
- 运行时协作必须可追踪，不应依赖“碰巧可用”的全局对象。

### 11.7 扩展作者检查清单

扩展作者在设计新插件时，至少应回答：

- 我是否有唯一且稳定的名称？
- 我是否声明了显式依赖？
- 我是否在初始化后会做附加连接？
- 我是否会在注册阶段做副作用？
- 我是否在 shutdown 中释放资源？
- 我的接口是否能在测试中单独验证？

### 11.8 设计风险

以下情况应被视为插件机制的高风险：

- 依赖隐藏在全局对象里，而不是接口声明中
- 插件依赖初始化顺序而不是依赖图
- 扩展在 `post_init` 里循环访问其他扩展状态
- 组件没有幂等性或清理路径

### 11.9 说明

本专题不替代行为契约，也不替代数据库、视图和安全领域说明。插件机制属于核心架构能力，故它比普通实现细节更需要被单独说明；其可验证行为会落到 `requirements.md`，而具体实现和设计动机则见 `architecture.md` 和本文其他章节。

## 12. 数据库与持久化

> 本章规范数据库边界、生命周期、约束和责任分工，不重复业务需求或安全细节。适用范围为 SQLAlchemy 数据层、数据访问扩展和持久化约束；数据快照为 2026-11-07（仓库版本 `0.4.0`；未复核）。

### 专题目录

- [12.1 适用范围](#121-适用范围)
- [12.2 核心原则](#122-核心原则)
- [12.3 生命周期规范](#123-生命周期规范)
- [12.4 约束与不变式](#124-约束与不变式)
- [12.5 查询规范](#125-查询规范)
- [12.6 兼容性与扩展性](#126-兼容性与扩展性)
- [12.7 设计风险](#127-设计风险)
- [12.8 说明](#128-说明)

### 12.1 适用范围

本规范覆盖：

- `datastore/sqla` 的连接、会话和查询边界
- `db` 单例的绑定与释放
- 查询构造、筛选、排序、分页和比对规则
- 事务/上下文边界
- 默认数据库选型与可扩展性约束

不覆盖：

- 业务实体设计细节（见本文其他章节 / `requirements.md`）
- 安全策略细节（见 `security.md`）
- 管理后台表现（见本文第 10 章）

### 12.2 核心原则

1. 数据层必须与视图层、认证层、业务层分离。
2. 一个 `db` 实例应绑定到一个 Flask app；跨 app 共享不做默认假设。
3. 数据访问必须在 app context 内进行，使用统一的 session lifecycle。
4. 查询构造应遵守单一入口和可审查职责，不把数据库细节散落到 UI 或扩展逻辑中。
5. 默认数据库是 SQLite；生产部署应以 PostgreSQL 或等价关系数据库为主。

### 12.3 生命周期规范

#### 12.3.1 初始化

- `db.init_app(app)` 用于绑定数据库到 Flask app。
- 每个 app 只允许一个绑定。
- 数据层的初始化必须在扩展注册与依赖排序之后发生。

#### 12.3.2 会话管理

- session 生命周期应与 app context 绑定。
- 请求结束时需清理/移除会话，避免泄漏。
- 不应在 app context 外访问共享 session。

#### 12.3.3 关闭与重绑定

- `dispose()` 或等价释放动作必须在重绑定前调用。
- 关闭失败应被隔离，不应影响其他扩展的清理。

### 12.4 约束与不变式

- 一个进程中的数据库实例不能默认同时表示多个 app。
- session 不能被长期持有在全局变量中。
- 查询和过滤必须在数据层决定，不允许 View 层直接手写数据库访问逻辑。
- 相关字段的排序、过滤和分页必须由统一的查询层处理。
- 直接使用裸 SQL 只能作为受控例外，不应成为主路径。

> 待澄清：第 10.8.3 节的历史示例在 View 方法中通过 backend 的 session 构造和执行查询，与本节分层约束存在张力。示例和规则均保留；具体边界及实现是否符合要求须结合源码与契约核实。

### 12.5 查询规范

#### 12.5.1 搜索与过滤

- 查询必须统一处理关系路径、字段名和过滤符。
- 过滤规则应在查询层中定义，避免 UI 或控制器层对 SQL 语义做隐式假设。
- 对于缺失或无效字段，必须明确返回错误或安全降级，而不是静默转换。

#### 12.5.2 排序与分页

- 排序字段必须来自已定义字段集合。
- 分页应使用统一的 page/page_size 规则。
- 计数必须和查询结果保持语义一致，避免重复计数或 JOIN 误差。

> 历史快照中一对多 JOIN 计数存在 C2 问题记录，见第 10.16 节；该记录未在当前环境复核，不能仅凭本节规范推断现状或修复状态。

### 12.6 兼容性与扩展性

- 数据库层应优先通过抽象接口扩展，而非直接写死实现细节。
- 未来如果增加多个后端，应该只替换数据访问实现，而不改动上层 View/Controller 逻辑。
- 数据模型与持久化层必须明确区分“接口”和“实现”。

### 12.7 设计风险

以下问题属于本规范重点关注：

- 多 app/多 context 下 session 重用错误
- 查询层与后台层双重职责导致的耦合
- 过滤条件和分页条件字段不一致
- 依赖于隐式全局状态而不是显式 context

### 12.8 说明

本专题是数据库层的核心规范，其重点是“边界、生命周期、查询合规和可扩展性”。详细行为契约仍放在 `requirements.md`；具体实现细节和为什么这样做见 `architecture.md` 和本文其他章节。
