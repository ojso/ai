# Flask-Exts View 与 Admin 编写指南（View）

> 本文是 Flask-Exts 的 **View / ModelView / Admin 专题文档**：路由与访问控制、列/筛选/排序/搜索、表单生成、Inline、AJAX、导出、分页、CRUD、模板与自定义后端。
>
> | 项目 | 内容 |
> | --- | --- |
> | 文档版本 | v0.1 |
> | 状态 | 可用 |
> | 最后更新 | 2026-11-08 |
> | 数据快照 | 2026-11-07（仓库版本 `0.4.0`；未复核） |
> | 适用仓库 | `flask-exts` |
> | 配套文档 | `architecture.md`（架构）、`spec.md`（设计/实现）、`requirements.md`（契约）、`testing.md`（测试）、`demo.md`（示例）、`security.md`（安全） |
>
> **定位**：`spec.md` 保留项目全景；本文承接其中原 3.7、3.8、4.3、5.5、5.6 与 Admin API 速查的 View 内容，作为 View/Admin 的**单一事实源**。安全边界与风险见 `security.md`，测试用例见 `testing.md` 第 7.3 节。

## 目录

- [0. 快速开始](#0-快速开始)
- [1. View 体系总览](#1-view-体系总览)
- [2. Admin 与视图注册](#2-admin-与视图注册)
- [3. View 基类与路由](#3-view-基类与路由)
- [4. ModelView](#4-modelview)
- [5. DataBackend 协议](#5-databackend-协议)
- [6. SqlaModelView 与 SqlaBackend](#6-sqlamodelview-与-sqlabackend)
- [7. 列、格式化、筛选、排序、搜索](#7-列格式化筛选排序搜索)
- [8. 表单生成](#8-表单生成)
- [9. Inline 模型](#9-inline-模型)
- [10. AJAX 外键](#10-ajax-外键)
- [11. 导出](#11-导出)
- [12. 分页与列表参数](#12-分页与列表参数)
- [13. CRUD 与请求流程](#13-crud-与请求流程)
- [14. 模板与自定义页面](#14-模板与自定义页面)
- [15. Recipes](#15-recipes)
- [16. 已知问题与回归](#16-已知问题与回归)
- [17. 测试映射](#17-测试映射)
- [18. API 速查](#18-api-速查)

## 0. 快速开始

> 本文代码片段只保留**最小 API 签名与用法示例**；内部实现细节不在此复制，以源码为准。完整 demo 类见 `demo.md` 第 5 章与 `flask-exts/examples/demo`。

### 0.1 最小模型视图

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

### 0.2 最小自定义页面

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

### 0.3 最小 Inline / AJAX 配置

```python
from flask_exts.admin.sqla.inline.inline_model_convert import InlineForm


class AuthorView(SqlaModelView):
    inline_models = (InlineForm(Post, form_columns=("title", "text", "date")),)


class PostView(SqlaModelView):
    ajax_refs = {
        "author": {"fields": ("first_name", "last_name")},
    }
```

> Inline 子模型再配置 `ajax_refs` 会触发已知缺陷 C1（见第 16 章）。

## 1. View 体系总览

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

### 1.1 Handler 拆分

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

> **命名注意**：`RowActionHandler`（单数 Row）负责“单行按钮”，`RowsActionHandler`（Rows）负责“批量操作”。两者只差一个 `s`，文件名也只差 `s` 的位置（`rowactions.py` / `rowsaction.py`），非常容易混淆；建议重构时改名为 `RowActionHandler` / `BulkActionHandler`，见第 16 章 V-02。

`ModelView` 通过显式转发方法暴露 Handler 能力（如 `get_list_args()`、`get_list_url()`），转发方法本身不在此复制。

优点：

- 每个 Handler 可以独立测试
- `ModelView` 不再无限膨胀
- 转发方法是显式的，便于发现和类型提示

注意：

- Handler 与 View 之间仍有较多属性访问（`self.view.xxx`），改 View 属性名会影响多个 Handler。
- 继承链中 Mixin/Handler 的调用顺序需要保持文档化。

## 2. Admin 与视图注册

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

## 3. View 基类与路由

### 3.1 构造参数

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

### 3.2 路由装饰器

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

### 3.3 ViewMeta 与访问控制

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

### 3.4 渲染

```python
def render(self, template, **kwargs): ...
def render_string(self, source, **kwargs): ...
```

- `render()` 用于模板文件；可追加任意关键字参数。
- `render_string()` 用于小页面/内联模板。
- `View` 的 `template_folder` 会加入 Jinja 搜索路径。
- `_headers` 参数可用于设置响应头（如 `NO_CACHE_HEADER`）。

## 4. ModelView

### 4.1 构造与初始化顺序

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

### 4.2 配置属性

#### 列与展示

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

#### 筛选、排序、搜索

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

#### 表单

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

#### 分页、权限、导出、模板

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

### 4.3 列解析

- 列名会解析成 `(字段名, 显示标签)`。
- 未设置时由 backend 脚手架推断。
- 点号路径用于关联列（如 `author.email`）。

### 4.4 权限开关

`can_create` / `can_edit` / `can_delete` 是**视图级功能开关**：

- `False` 时路由重定向回列表，而不是 403。
- 用户是否能进入视图，由 `SimpleAuthorizer` 决定；两者不同。
- `action_disallowed_list` 只影响批量/行操作，不影响单条 CRUD。

## 5. DataBackend 协议

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

## 6. SqlaModelView 与 SqlaBackend

### 6.1 构造

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

### 6.2 脚手架规则

| 脚手架 | 规则 |
| --- | --- |
| `scaffold_list_columns` | 包含多对一/多对多关系列；标量列跳过外键 |
| `scaffold_sortable_columns` | 只含单列属性；跳过外键与复合列 |
| `scaffold_filter` | 按列类型生成过滤器；使用 `column_choices` 作为 options |
| `scaffold_form` | 跳过主键、外键、下划线开头字段；关系字段保留 |
| `scaffold_list_form` | 按 `column_editable_list` 生成 |

### 6.3 列表查询顺序

顺序很重要：

1. 搜索/筛选加入 JOIN 条件。
2. 自动 eager load 加入 `joinedload`/`selectinload`。
3. **先计数**，再分页/排序；计数查询会带上 JOIN。
4. 分页 `offset = page * page_size`。
5. 排序支持单列与多列。

### 6.4 自动 eager load

- 多对一：`joinedload`
- 多对多/一对多：`selectinload`
- 目的：减少列表页 N+1。

### 6.5 CRUD 事务

```python
def create_model(self, model): ...
def update_model(self, model): ...
def delete_model(self, model): ...
```

- 写操作失败返回 `None`/`False`，视图层 flash 错误。
- 批量删除失败会 `rollback` 后重新抛异常。
- 视图层不直接操作 session。

### 6.6 已知问题

| 问题 | 说明 |
| --- | --- |
| C2 计数偏大 | `build_count()` 应用 JOIN 但未去重；一对多搜索/筛选时 `count` 大于根记录数 |
| 复合主键 | 使用逗号编码；主键值本身含逗号时会歧义 |
| 自动 JOIN | 只根据 `column_list` 的根关系推断；复杂路径可能需要手动配置 |

## 7. 列、格式化、筛选、排序、搜索

### 7.1 列与标签

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

### 7.2 自定义格式化器

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

### 7.3 类型格式化器

```python
from flask_exts.admin.model.type_formatters import BASE_FORMATTERS

MY_FORMATTERS = dict(BASE_FORMATTERS)
MY_FORMATTERS[type(None)] = lambda view, value, name: "—"


class AuthorView(SqlaModelView):
    column_type_formatters = MY_FORMATTERS
```

优先级低于列级格式化器。

### 7.4 自定义过滤器

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

### 7.5 排序

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

### 7.6 搜索

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

### 7.7 内联编辑

```python
class PostView(SqlaModelView):
    column_editable_list = ("color",)
```

- 列表页通过 `/ajax/update/` 保存。
- 需要字段可编辑、表单可生成、CSRF 正确。

## 8. 表单生成

### 8.1 转换器组合

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

### 8.2 字段选择

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

### 8.3 关系字段与编辑页过滤

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

### 8.4 CSRF

- 表单默认使用 `FlaskForm`，CSRF 由全局 `CSRF_ENABLED` 控制。
- 测试中常关闭 CSRF；生产保持开启。
- 自定义 AJAX 保存必须携带 `csrf_token`。

## 9. Inline 模型

### 9.1 配置形式

```python
inline_models = (
    Post,
    (Post, {"form_columns": ("title", "text")}),
    InlineForm(
        Post, form_columns=("title", "text"), form_args={"title": {"label": "Title"}}
    ),
)
```

### 9.2 转换流程

1. `get_inline_form(prop)`：把模型/元组/`InlineForm` 统一成 `InlineForm`。
2. `process_ajax_refs(inline_form)`：处理 AJAX 外键。
3. `_calculate_mapping_key_pair(model, info)`：找父子关系的前向/反向属性。
4. `contribute(model, form_class, inline_model)`：生成子表单并加入父表单。

关系发现：

- 从子模型出发遍历 `iterate_properties`，筛选指向父模型的 `MANYTOONE` / `MANYTOMANY` 关系。
- 优先 `back_populates`；找不到再遍历候选；仍找不到抛 `ValueError`。
- 支持一对多、一对一、多对多。

### 9.3 AJAX 保存

- `POST /admin/<view>/ajax/create-parent/`
- `POST /admin/<view>/ajax/inline/<relationship_name>/`
  - `action=save` 保存子记录
  - `action=delete` 删除子记录
- 需要 CSRF token；后端会校验。

### 9.4 已知缺陷 C1

`process_ajax_refs` 调用 `self.view.create_ajax_loader(...)` 时传 5 个参数，但签名是 `(name, options)`；完整复现证据见第 16 章 C1。

后果：Inline 子模型配置 `ajax_refs` 时直接 `TypeError`。修复方向：

- 统一 `create_ajax_loader` 签名；或
- Inline 里先构造 `AjaxSqlaModelLoader` 并赋值。

修复后补测试：`tests/integration/admin/sqla/test_inline_ajax.py`。

## 10. AJAX 外键

### 10.1 配置

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

### 10.2 路由

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

### 10.3 注意事项

- 关联模型的 Admin 视图最好已注册，便于前端跳转/权限一致。
- `ajax_refs` 与 Inline 同时使用时注意 C1。
- AJAX 更新需要 CSRF。

## 11. 导出

### 11.1 配置

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

### 11.2 行为

- CSV 使用流式 `Response`。
- 其他格式走 tablib；`xls`/`xlsx` 需要额外依赖（如 `tablib[xls]`）。
- 不支持的格式会 flash 错误并重定向回列表。
- 导出格式化器不支持宏（`inner` 名称会抛 `NotImplementedError`）。
- 文件名经过 `secure_filename`。

## 12. 分页与列表参数

### 12.1 请求参数

| 参数 | 含义 |
| --- | --- |
| `page` | 页码，**从 0 开始** |
| `page_size` | 页大小；必须在白名单内 |
| `sort` | 排序列索引（列表列下标） |
| `desc` | `1` 表示降序 |
| `search` | 搜索词 |
| `flt*` | 过滤器参数 |
| 其他 | 放入 `extra_args`，分页/排序时保留（`url`、`flt*` 除外） |

### 12.2 解析

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

### 12.3 已知问题 C5/C6

- `hasattr(self, "get_url")` 在 `PaginationHandler` 上永远为假，因为 `get_url` 在 `View` 上；这是死分支（C5）。
- 手写查询字符串没有 URL 编码；搜索词含 `&`、`#`、空格、中文时可能出错（C6）。
- 建议改用 `url_for` + `urlencode`，并补 A-32 测试。

## 13. CRUD 与请求流程

### 13.1 列表请求

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

### 13.2 创建

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

### 13.3 编辑 / 详情 / 删除

- 编辑：`GET/POST /edit/?id=...`；`edit_form(obj=model)`；`update_model`。
- 详情：`GET /details/?id=...`；`get_one`。
- 删除：`POST /delete/`；`delete_form` 校验；`delete_model`。
- `get_redirect_target()` 使用 `safe_redirect_target` 处理 `url` 参数，防止开放重定向。

### 13.4 批量/行操作

- `POST /action/`：批量操作（如批量删除）。
- `action_disallowed_list` 禁用操作。
- `can_delete` 等是视图级开关，不是用户授权。

### 13.5 Inline 表单提交

```text
编辑带 Inline：
  ├─ scaffold_inline_models_form()
  ├─ 子表单字段加入父表单
  ├─ 提交时校验父/子
  ├─ 保存父记录
  ├─ 处理子记录新增/修改/删除
  └─ 失败抛 InlineModelError
```

## 14. 模板与自定义页面

### 14.1 默认模板

| 模板 | 用途 |
| --- | --- |
| `admin/model/list.html` | 列表 |
| `admin/model/create.html` | 创建 |
| `admin/model/edit.html` | 编辑 |
| `admin/model/details.html` | 详情 |
| `admin/master.html` | 布局/菜单/消息 |

### 14.2 覆盖模板

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

### 14.3 自定义页面

自定义页面的最小示例见 0.2 节；`render_string` 适合小页面，复杂页面用模板 + `render`。`allow_access=True` 公开，否则需要 admin 权限。

## 15. Recipes

### 15.1 新增一个模型视图

1. 定义模型。
2. 定义 `SqlaModelView` 子类。
3. `admin.register_view(view_instance)`。
4. 访问 `/admin/<endpoint>/`。

### 15.2 自定义格式化器

见 7.2。

### 15.3 自定义过滤器

见 7.4。

### 15.4 Inline 子表单

见 9.1。

### 15.5 AJAX 外键

见 10.1。

### 15.6 自定义列表模板

见 14.2。

### 15.7 自定义后端

```python
from flask_exts.admin.model.view import ModelView
from .backend import JsonBackend


class JsonModelView(ModelView):
    column_list = ("id", "name")


jsonview = JsonModelView(MyRecord, JsonBackend)
admin.register_view(jsonview)
```

`JsonBackend` 实现第 5 章的协议；不需要 SQLAlchemy。

### 15.8 自定义页面

见 14.3。

## 16. 已知问题与回归

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

### 16.1 详细说明

#### C1：Inline AJAX 加载器参数不匹配

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

#### C2：`build_count` 一对多重复计数

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

#### C5 / C6：`get_list_url`

`PaginationHandler` 没有 `get_url`，所以分支永远走 `else`。同时手写查询字符串没有编码。

**建议：**

- 删除死分支，或在 Handler 中显式持有 view 并调用 `self.view.get_url(".index_view", **kwargs)`
- 使用 `urllib.parse.urlencode` 生成查询字符串
- 补测试：搜索词含空格/`&`/中文时 URL 正确

#### C7：未使用的 query builders

`FilterBuilder`、`JoinBuilder`、`SortBuilder`、`PaginationBuilder` 没有被 `SqlaBackend` 使用。

**建议：** 二选一：

- 接入 `Query`，让 builder 成为唯一查询构造方式
- 删除，减少误导

#### C10：晚注册扩展

`AdminExtension.post_init` 只在初始化阶段扫描一次。`register_extension` 的文档已说明这一点。

**建议：**

- 如果确实需要动态注册，提供显式的 `admin.rescan_views()` 或事件
- 或在 `register_extension` 中对新扩展触发相关扩展的 `post_init`（需要设计幂等与重复注册保护）

#### V-02：RowAction 与 RowsAction 命名混淆

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

## 17. 测试映射

| 能力 | `testing.md` 用例 |
| --- | --- |
| 列表/详情/分页 | A-01～A-04、A-12、A-33 |
| 排序 | A-05/A-06 |
| 搜索 | A-07/A-08、A-32 |
| 筛选 | A-09/A-10 |
| CRUD | A-11、A-17 |
| 导出 | A-13～A-15 |
| Inline | A-18～A-21 |
| AJAX | A-22 |
| 权限 | A-25～A-28 |
| 表单/字段 | A-30 |
| 一对多计数 | A-31（对应 C2） |
| URL 特殊字符 | A-32（对应 C6） |

现有测试目录：

- `tests/integration/admin/sqla/test_views.py`
- `tests/integration/admin/sqla/test_forms.py`
- `tests/integration/admin/sqla/test_search.py`
- `tests/integration/admin/sqla/test_sorting.py`
- `tests/integration/admin/sqla/test_pagination.py`
- `tests/integration/admin/sqla/test_actions.py`
- `tests/integration/admin/sqla/test_export.py`
- `tests/integration/admin/sqla/test_inline_forms.py`
- `tests/integration/admin/sqla/test_inline_views.py`
- `tests/integration/admin/sqla/test_inline_ajax.py`
- `tests/integration/admin/sqla/test_ajax.py`
- `tests/integration/admin/sqla/test_primary_keys.py`

运行方式见 `testing.md` 第 0 章；本文只维护测试映射。

重点缺口：

- Inline + AJAX 外键（C1）没有真正触发缺陷的测试。
- 一对多搜索计数（C2）没有 `count` 断言。
- URL 特殊字符（C6）缺少回归测试。
- 自定义 `DataBackend` 没有单元测试。
- 权限矩阵（匿名/普通/inactive）仍不完整。
- `can_edit=False` 时 `/ajax/update/` 的行为（V-01）没有测试。
- 单行操作按钮与批量操作的渲染/执行（V-02）没有专门测试；`test_actions.py` 主要覆盖内联编辑与批量删除。

## 18. API 速查

> 本节是速查表，只列常用入口；语义见第 7–15 章，不在本节重复解释。

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
