# Flask-Exts Demo 编写指南

> 本文是 `examples/demo` 的**编写、运行与维护指南**，面向需要新增/修改示例应用、数据模型、Admin 视图、模板和初始化数据的贡献者。
>
> | 项目 | 内容 |
> | --- | --- |
> | 文档版本 | v0.1 |
> | 状态 | 可用 |
> | 最后更新 | 2026-11-09 |
> | 数据快照 | 2026-11-07（仓库版本 `0.4.0`；未复核） |
> | 适用目录 | `flask-exts/examples/demo` |
> | 配套文档 | `architecture.md`（架构）、`spec.md`（设计/实现及 View/Admin）、`requirements.md`（契约）、`testing.md`（测试）、`security.md`（安全） |
>
> **定位**：`examples/demo` 是**可运行的参考应用**，不是生产模板。它用尽量少的代码展示 Flask-Exts 的模型、Admin、Inline、筛选、排序、导出、AJAX、递归关系和自定义模板能力。修改 demo 时优先保证“能运行、能看懂、不引入额外依赖”。

## 目录

- [0. 快速开始](#0-快速开始)
- [1. 定位与边界](#1-定位与边界)
- [2. 目录结构](#2-目录结构)
- [3. 启动流程](#3-启动流程)
- [4. 数据模型](#4-数据模型)
- [5. Admin 视图](#5-admin-视图)
- [6. 模板与静态资源](#6-模板与静态资源)
- [7. 示例数据](#7-示例数据)
- [8. 配置](#8-配置)
- [9. 扩展 Demo Recipes](#9-扩展-demo-recipes)
- [10. 常见问题](#10-常见问题)
- [11. 验证清单](#11-验证清单)
- [12. 编写规范](#12-编写规范)
- [13. 与主文档、测试文档的关系](#13-与主文档测试文档的关系)

## 0. 快速开始

### 0.1 环境准备

环境初始化命令只在 `testing.md` 第 0.1 节维护；这里不复制。

> demo 只依赖库本身的运行时依赖，不需要额外安装 `factory-boy`、`selenium` 等测试工具。

### 0.2 启动

demo 只支持下面两种启动形式，其他写法（如 `flask run`、`flask --app demo run`）不在本文档中使用：

| 方式 | 执行目录 | 命令 |
| --- | --- | --- |
| A（推荐） | `examples/demo` | `flask --app __init__ run` |
| B | 仓库根目录 | `flask --app examples.demo run` |

**命令约定：**

- 在 `examples/demo` 目录内执行时，`--app` 一律写 `__init__`。
- 在仓库根目录执行时，`--app` 一律写 `examples.demo`。
- 两种方式启动的是同一个应用，`create_app()` 与数据库初始化逻辑一致。
- 端口、调试、CLI 子命令都沿用所属目录的 `--app` 值，见 0.3、0.4。

**与 `examples/README.rst` 的关系：**

- `examples/README.rst` 是启动命令的对外权威来源；本文档的方式 A、B 与其保持同一写法。
- 当前环境没有 `flask-exts` 源码，无法逐字核对 README；一致性状态为 `待确认`。
- 若两者冲突，以 `examples/README.rst` 为准，并回来修正本文档。

方式 A：

```bash
cd examples/demo
flask --app __init__ run
```

方式 B：

```bash
flask --app examples.demo run
```

打开：

- 首页：`http://localhost:5000/`
- Admin：`http://localhost:5000/admin/`
- 登录：`http://localhost:5000/user/login/`

默认账号：

| 用户名 | 密码 | 角色 |
| --- | --- | --- |
| `admin` | `admin` | `admin` |

> 默认密码仅用于本地演示。任何可被他人访问的环境都必须修改。

### 0.3 常用命令

以下命令都在 `examples/demo` 目录执行（方式 A），因此统一使用 `--app __init__`：

```bash
# 查看路由，确认应用可导入
flask --app __init__ routes

# 指定端口
flask --app __init__ run --port 5001

# 开启调试
flask --app __init__ run --debug
```

在仓库根目录执行时，把 `--app __init__` 换成 `--app examples.demo`（方式 B）。

### 0.4 重置数据库

在仓库根目录执行（方式 B），先停止正在运行的 demo：

```bash
rm examples/demo/demo.sqlite
flask --app examples.demo run
```

demo 只在数据库文件**不存在**时初始化。

删除后会重新执行 `build_sample_db()`：建表、写入示例树/作者/文章/标签，并创建 `admin/admin`。

> `demo.sqlite` 已被 `.gitignore` 的 `*.sqlite` 规则忽略，不要提交。

## 1. 定位与边界

### 1.1 demo 要展示什么

| 能力 | 对应位置 |
| --- | --- |
| 应用工厂与扩展初始化 | `make_app.py` |
| SQLAlchemy 模型与关系 | `models/` |
| Admin 模型视图、列表、搜索、筛选、排序、分页 | `views/author_view.py`、`views/post_view.py` |
| Inline 父子表单 | `AuthorView.inline_models` |
| 多对多关系 | `Post.tags` + `post_tag` |
| 自引用/递归关系 | `models/tree.py`、`views/tree_view.py` |
| 自定义过滤器 | `views/post_view.py` 的 `FilterNameBrown`、`FilterLike` |
| 自定义列表模板 | `templates/tree_list.html` + `TreeView.render` |
| AJAX 外键 | `PostView.ajax_refs` |
| 导出 | `AuthorView`、`PostView` 的 `can_export` / `export_types` |
| 默认用户与登录 | `build_sample.py`、`/user/login/` |
| 示例数据生成 | `build_sample.py` |

### 1.2 demo 不负责什么

- 生产级安全（默认密码、`SECRET_KEY="demo"`、无 HTTPS、无 CSRF 配置加固）。
- 数据库迁移（直接 `drop_all()` / `create_all()`，不是 Alembic）。
- 邮件发送配置（未配置 `NOREPLY_EMAIL_SENDER`，注册流程不会真的发信）。
- 部署、反向代理、静态资源 CDN。
- 完整测试覆盖（demo 的测试策略见 `testing.md`，目前以手工冒烟为主）。

### 1.3 修改原则

1. **保持可运行**：只依赖 `pyproject.toml` 中的运行时依赖。
2. **保持可读**：一个文件只演示一个主题，避免为了“功能多”堆叠配置。
3. **保持最小**：新增功能优先改现有模型/视图，不要为演示引入新框架。
4. **不提交生成物**：`demo.sqlite`、上传文件、日志不入库。
5. **代码英文**：变量、注释、docstring 用英文；本文档用中文。

## 2. 目录结构

```text
examples/
├── README.rst                  # 运行说明（会被 docs/examples.rst 引用）
├── simple/
│   └── __init__.py             # 最小 Admin 视图示例
└── demo/
    ├── __init__.py             # 导出 create_app，供 Flask CLI 发现
    ├── make_app.py             # 应用工厂：配置、扩展、模型、视图、初始化
    ├── admin_views.py          # 统一注册 Admin 视图
    ├── build_sample.py         # 示例数据：树、作者、文章、标签、admin 用户
    ├── file_op.py              # 上传辅助函数（当前未接入路由）
    ├── demo.sqlite             # 运行时生成，忽略提交
    ├── models/
    │   ├── __init__.py         # 导入所有模型，注册到 db.metadata
    │   ├── author.py           # Author + 枚举 + hybrid property
    │   ├── post.py             # Post + 作者/标签关系
    │   ├── tag.py              # Tag
    │   ├── post_tag.py         # 多对多关联表
    │   └── tree.py             # Tree 自引用
    ├── views/
    │   ├── author_view.py      # AuthorView（Inline、表单、筛选、导出）
    │   ├── post_view.py        # PostView（关联列、自定义过滤器、AJAX）
    │   ├── tag_view.py         # TagView（最小视图）
    │   └── tree_view.py        # TreeView（自定义模板）
    ├── templates/
    │   ├── tree_list.html      # 扩展 admin/model/list.html
    │   ├── field_list.html     # 字段宏示例（当前未接入）
    │   └── locations.html      # 独立页面示例（当前未接入）
    └── static/
        └── favicon.ico
```

> `views/` 目前是**命名空间包**（没有 `__init__.py`），Python 3 可以直接导入。新增视图时可以直接放文件；如果希望显式导出，可以补一个 `views/__init__.py`，但不要在 `__init__.py` 里做重量级初始化。

`examples/simple` 与 `examples/demo` 的分工：

| 示例 | 用途 | 适合参考的场景 |
| --- | --- | --- |
| `examples/simple` | 最小可运行应用，只有一个自定义 Admin 页面 | 学习 `ExtensionManager` + `View` + `render_string` |
| `examples/demo` | 完整数据驱动应用 | 学习模型、Admin 模型视图、Inline、筛选、导出、模板 |

## 3. 启动流程

### 3.1 调用链

以方式 A（`examples/demo` 目录，`--app __init__`）为例；方式 B 的调用链相同，只是模块名换成 `examples.demo`。

```text
flask --app __init__ run
        │
        ▼
examples/demo/__init__.py  →  create_app()
        │
        ▼
make_app.create_app()
  1. Flask(__name__, instance_relative_config=True)
  2. 设置 APP_NAME / SECRET_KEY
  3. 读取可选的 instance/config.py、instance/config_prod.py
  4. 计算 DATABASE_FILE，设置 SQLALCHEMY_DATABASE_URI
  5. ExtensionManager().init_app(app)
  6. import .models（注册模型元数据）
  7. register_views(app)（注册 Admin 视图）
  8. 若数据库文件不存在 → build_sample_db()
        │
        ▼
返回 app，Flask 启动
```

### 3.2 关键顺序

1. **先初始化扩展，再导入模型**：`ExtensionManager.init_app()` 会创建/绑定 `db`，之后 `models` 中的 `db.Model` 才能正确注册到同一 metadata。
2. **先导入模型，再注册视图**：`SqlaModelView(Model)` 需要模型类；注册时 Flask 立即创建并注册蓝图。
3. **先注册视图，再建库**：`build_sample_db()` 需要 `db.Model.metadata` 已包含所有模型。
4. **初始化只跑一次**：`db` 是模块级单例，同一进程不要重复 `create_app()` 后同时持有两个 app；测试/多 app 场景先 `dispose()`。

### 3.3 `create_app()` 的真实行为

```python
def create_app():
    app = Flask(__name__, instance_relative_config=True)
    app.config["APP_NAME"] = "FlaskDemo"
    app.config["SECRET_KEY"] = "demo"
    app.config.from_pyfile("config.py", silent=True)
    app.config.from_pyfile("config_prod.py", silent=True)
    app.config["DATABASE_FILE"] = op.join(
        op.realpath(op.dirname(__file__)), "demo.sqlite"
    )
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + app.config["DATABASE_FILE"]
    init_app(app)
    return app
```

注意：

- `from_pyfile(..., silent=True)` 表示配置文件**可选**；缺失不报错。
- `DATABASE_FILE` 固定在 `examples/demo/demo.sqlite`，不受启动目录影响。
- 只有数据库文件不存在时才初始化；**文件存在但 schema 过期不会自动重建**（见第 10 章）。

## 4. 数据模型

### 4.1 关系图

```text
Author 1 ─────── N Post N ─────── M Tag
   │                  │
   │ featured_post_id │
   └──────────────────┘  (Author 的可空外键指向 Post)

Tree 1 ─────── N Tree
      parent_id
```

### 4.2 模型职责

| 模型 | 表 | 关键字段 | 演示点 |
| --- | --- | --- | --- |
| `Author` | `author` | `type`、`email`（唯一）、`featured_post_id`、电话/日期字段 | 枚举、hybrid property、1-N、指向 Post 的可空外键 |
| `Post` | `post` | `title`、`text`、`color`、`date`、`author_id` | 1-N、M-N、可排序/可搜索字段 |
| `Tag` | `tag` | `name`（唯一） | 最简模型 |
| `post_tag` | `post_tag` | `post_id`、`tag_id` | 多对多关联表 |
| `Tree` | `tree` | `name`、`parent_id` | 自引用/递归关系 |

### 4.3 关系写法

```python
# Author.posts：一对多，删除作者时级联删除文章
posts: Mapped[list["Post"]] = relationship(
    foreign_keys="[Post.author_id]",
    back_populates="author",
    cascade="all, delete-orphan",
)

# Post.author：反向关系
author: Mapped["Author"] = relationship(
    foreign_keys=[author_id], back_populates="posts"
)

# Post.tags：多对多
tags: Mapped[list["Tag"]] = relationship(secondary=post_tag_table)
```

约定：

- 使用 SQLAlchemy 2.0 `Mapped` / `mapped_column`。
- 双向关系显式 `back_populates`，不要用 `backref`。
- 自引用使用 `remote_side=id`：

```python
parent = relationship("Tree", back_populates="children", remote_side=id)
children = relationship("Tree", back_populates="parent")
```

- 多对多关联表放在独立模块（`post_tag.py`），由 `models/__init__.py` 统一导入。

### 4.4 `Author.phone_number`：hybrid property

```python
@hybrid_property
def phone_number(self):
    ...

@phone_number.expression
def phone_number(cls):
    return sql.operators.ColumnOperators.concat(
        cast(cls.dialling_code, String), cls.local_phone_number
    )
```

用途：同一个属性既能用于 Python 对象，也能用于 SQL 表达式。demo 中为了简化列表展示，`phone_number` 在 `column_list` 里被注释掉了；需要演示时再打开。

### 4.5 新增模型的标准步骤

1. 在 `models/` 新建 `foo.py`，定义 `Foo(db.Model)`。
2. 在 `models/__init__.py` 导入并加入 `__all__`。
3. 在 `build_sample.py` 中按需写入示例数据。
4. 在 `views/` 新建 `foo_view.py`，定义 `FooView(SqlaModelView)` 并实例化。
5. 在 `admin_views.py` 中 `admin.register_view(fooview)`。
6. 删除 `demo.sqlite` 后重启，让新表被创建。

## 5. Admin 视图

> View/ModelView/SqlaModelView 的配置、DataBackend、Inline、AJAX、导出与已知问题见 [`spec.md` 第 10 章](./spec.md#10-view-与-admin-专题)。本章只说明 demo 中的实际用法；完整 demo 类以本章与 `examples/demo` 为主，`spec.md` 第 10 章只保留最小 API 片段。

### 5.1 注册方式

```python
# admin_views.py
def register_views(app):
    admin = app.extensions["exts"].get_extension("admin").get_admin()
    admin.register_view(authorview)
    admin.register_view(postview)
    admin.register_view(tagview)
    admin.register_view(treeview)
```

- `register_view(view, is_menu=True, category=None)`。
- `is_menu=False` 可隐藏菜单项（内置 usercenter/portal 就这样做）。
- 视图名重复会抛 `ValueError`；`name` 默认取类名。

### 5.2 视图能力对照

| 视图 | 模型 | 演示点 |
| --- | --- | --- |
| `AuthorView` | `Author` | Inline 子表单、分页、导出、排序、筛选、可编辑列、自定义表单参数 |
| `PostView` | `Post` | 关联列、关联搜索、多列排序、自定义过滤器、AJAX 外键、导出 |
| `TagView` | `Tag` | 最小可用视图 |
| `TreeView` | `Tree` | 自定义列表模板、`render()` 传参、递归关系 |

### 5.3 `AuthorView`

关键配置：

```python
class AuthorView(SqlaModelView):
    can_set_page_size = False
    can_export = True
    page_size = 5
    page_size_options = (5, 10, 15)
    action_disallowed_list = ("delete",)

    inline_models = (
        InlineForm(
            Post,
            form_columns=("title", "text", "color", "date"),
            form_args={"title": {"label": "Post Title"}},
        ),
    )

    form_choices = {"type": AVAILABLE_USER_TYPES}
    form_args = {
        "dialling_code": {"label": "Dialling code"},
        "local_phone_number": {
            "label": "Phone number",
            "validators": [is_numberic_validator],
        },
    }
    form_widget_args = {"id": {"readonly": True}}
    column_list = (...)
    column_searchable_list = ("first_name", "last_name", "email")
    column_editable_list = ("type", "currency", "timezone", "cdate", "ctime", "cdatetime")
    column_details_list = (...)
    create_form_columns = (...)
    form_columns = (...)
    column_default_sort = DEFAULT_SORT
    column_filters = (...)
```

演示点：

- **Inline**：在 Author 编辑页直接增删改 Post。
- **表单 choices**：`form_choices` 的值是 `[(value, label), ...]`。
- **字段标签与校验**：`form_args` 同时设置 `label` 和 `validators`。
- **只读字段**：`form_widget_args` 给 `id` 加 `readonly`。
- **禁用删除**：`action_disallowed_list=("delete",)`。
- **固定分页**：`can_set_page_size=False`，但仍设置 `page_size_options` 供参考。
- **默认排序**：`DEFAULT_SORT` 是**模块级 list**，因为列表表示多列排序；写成 tuple 会被当成单个排序规格。
- **编辑页过滤外键**：`edit_form()` 重写 `featured_post.query_factory`，只允许选择当前作者的文章。

### 5.4 `PostView`

关键配置：

```python
class PostView(SqlaModelView):
    column_list = ("id", "author", "author.email", "title", "date", "tags", "color", "created_at")
    column_labels = {"title": "Post Title", "tags.name": "TagsName"}
    column_editable_list = ("color",)
    column_default_sort = ("date", True)
    column_sortable_list = (
        "id",
        "title",
        "date",
        ("author", ("author.last_name", "author.first_name")),
    )
    column_searchable_list = ("title", "author.first_name", "author.last_name")
    column_filters = (
        "id",
        "author.first_name",
        "author.id",
        FilterNameBrown(...),
        "color",
        "created_at",
        "title",
        "date",
        "tags.name",
        FilterLike(...),
    )
    can_export = True
    export_max_rows = 1000
    export_types = ("csv", "xls")
    ajax_refs = {"author": {"fields": ("first_name", "last_name")}}
    column_descriptions = {"color": "favorite color"}
```

演示点：

- **关联列**：`author.email`、`tags.name` 这类点号路径。
- **多列排序**：`("author", ("author.last_name", "author.first_name"))`。
- **关联搜索**：`author.first_name` / `author.last_name`。
- **自定义过滤器**：`FilterNameBrown` 继承 `BaseSQLAFilter`，`FilterLike` 复用内置过滤器。
- **导出**：`can_export`、`export_types`、`export_max_rows`。注意 `xls` 需要 `tablib[xls]`（`xlwt`/`xlrd`），项目默认依赖未包含；未安装时 CSV 可用，XLS 通常重定向回列表并提示格式不可用。
- **AJAX 外键**：`ajax_refs` 只配置了 `author`；`tags` 的配置在注释中，需要时可打开。
- **字段描述**：`column_descriptions` 会显示在表单/详情提示中。

> 排序、搜索、内联编辑与导出选项的语义见 `spec.md` 第 10.7.5～10.7.7、10.11 节；本节只保留 demo 的实际取值，不重复解释。

### 5.5 自定义过滤器

demo 中的 `FilterNameBrown` 与 `spec.md` 第 10.7.4 节的示例一致，完整代码见 `views/post_view.py`；本章不重复。

要点：

- `apply()` 必须调用 `query.add_filter(...)` 把条件加入 query；后端会忽略返回值，所以 `return query.add_filter(...)` 与直接调用效果相同。
- `operation()` 是显示在筛选下拉中的操作名。
- `options` 是 `(value, label)` 列表。
- 自定义过滤器可以直接放进 `column_filters`，也可以和字符串列名混用。

### 5.6 `TreeView`：自定义模板与传参

最小示例见 `spec.md` 第 10.14.2 节；完整 demo 实现见 `views/tree_view.py` 与 `templates/tree_list.html`；本章不重复。

要点：

- 覆盖 `list_template` 只影响列表页；创建/编辑/详情可分别用 `create_template` / `edit_template` / `details_template`。
- 模板必须 `extends` 内置模板并调用 `{{ super() }}`，否则会丢失列表、分页、筛选等 UI。
- `render()` 可以追加任意关键字参数；模板直接按名字使用。
- `form_excluded_columns=("children",)` 防止在表单里编辑反向集合。

### 5.7 新增 Admin 视图的标准步骤

1. 在 `views/` 新建 `foo_view.py`：

```python
from flask_exts.admin.sqla.view import SqlaModelView
from ..models.foo import Foo


class FooView(SqlaModelView):
    column_list = ("id", "name")
    column_searchable_list = ("name",)


fooview = FooView(Foo)
```

2. 在 `admin_views.py` 导入并注册：

```python
from .views.foo_view import fooview

def register_views(app):
    admin = app.extensions["exts"].get_extension("admin").get_admin()
    ...
    admin.register_view(fooview)
```

3. 删除 `demo.sqlite` 后重启，确认列表页可访问。

## 6. 模板与静态资源

### 6.1 模板查找顺序

Flask 会先找应用自己的 `templates/`，再找扩展提供的模板。demo 的 `templates/tree_list.html` 因此可以覆盖/扩展库内模板。

### 6.2 可覆盖的块

`admin/model/list.html` 继承 `admin/master.html`，常用块：

| 块 | 用途 |
| --- | --- |
| `main` | 列表页主体 |
| `model_menu_bar_before_filters` | 筛选栏之前 |
| `model_menu_bar_after_filters` | 筛选栏之后 |
| `list_table` | 整个表格 |
| `list_header` | 表头 |
| `list_row` | 单行 |
| `empty_list_message` | 空列表提示 |
| `list_pager` | 分页 |
| `tail` | 页面尾部脚本 |

### 6.3 当前模板说明

| 模板 | 状态 | 说明 |
| --- | --- | --- |
| `tree_list.html` | 已接入 | 通过 `TreeView.list_template` 使用 |
| `field_list.html` | 未接入 | 展示如何为字段写宏；需要视图/表单显式引用才会生效 |
| `locations.html` | 未接入 | 独立页面示例；当前没有路由渲染它 |

> 未接入的模板可以保留作为参考，但不要在文档中声称它们已生效；如果要启用，请补路由/视图并加入第 11 章验证。

### 6.4 静态资源

- 当前只有 `static/favicon.ico`。
- `file_op.py` 提供了 `save_image()` / `remove_image()`，但**当前没有路由使用**；它适合作为上传功能的起点。
- 上传文件写入 `static/` 只适合本地演示；生产应使用对象存储或独立上传目录，并校验扩展名/大小。

### 6.5 自定义页面（非模型视图）

如果只想加一个说明页/仪表盘，不需要 `SqlaModelView`。最小示例见 `spec.md` 第 10.0.2 节；本章不重复代码。

- `url="about"` → `/admin/about/`；`url="/about"` → `/about/`（绝对路径，不加 `/admin` 前缀）。
- `allow_access = True` 可让整个视图公开；否则需要 admin 角色。
- `@login_required` 先登录；`@requires_active` 再要求账号激活。
- `render_string()` 适合小页面；复杂页面用模板 + `render()`。

## 7. 示例数据

### 7.1 `build_sample_db()` 做了什么

```python
def build_sample_db():
    db.drop_all()
    db.create_all()
    build_sample_tree()
    build_sample_post()
    build_user_admin()
```

| 步骤 | 内容 |
| --- | --- |
| `db.drop_all()` | 删除所有已注册模型的表（破坏性） |
| `db.create_all()` | 按当前 metadata 建表 |
| `build_sample_tree()` | 1 个 Trunk + 5 个 Branch + 25 个 Leaf |
| `build_sample_post()` | 25 个作者、9 个标签、25 篇文章，随机关联标签 |
| `build_user_admin()` | 创建 `admin/admin`，分配 `admin` 角色 |

### 7.2 触发条件

`create_app()` 中的逻辑：

```python
if not op.exists(app.config["DATABASE_FILE"]):
    with app.app_context():
        from .build_sample import build_sample_db
        build_sample_db()
```

因此：

- 首次运行（无 `demo.sqlite`）→ 初始化。
- 已有 `demo.sqlite` → **不会**重新初始化。
- 模型变更后 → 删除 `demo.sqlite` 再启动。
- `build_sample_db()` 会 `drop_all()`，不要在包含真实数据的库上调用。

### 7.3 数据随机性

`build_sample_post()` 使用 `random.choice` / `random.sample`，没有固定 seed：

- 每次重建的作者电话/币种/时区、文章日期、标签组合都可能不同（`author.coutry` 是拼写错误，国家本身不会持久化）。
- 如果希望可复现，在 `build_sample_db()` 开头加 `random.seed(0)`。
- 不要让演示数据依赖随机结果做断言；需要稳定数据时显式指定。

### 7.4 已知问题

| 问题 | 说明 | 建议 |
| --- | --- | --- |
| `author.coutry = country[1]` | `Author` 没有 `coutry` 字段，这是拼写错误；该值不会持久化 | 改为 `country` 字段或删除该行；不要照抄 |
| `admin` 用户未显式 `is_active=True` | 登录使用 `force=True` + `admin` 角色校验，所以 demo 仍可登录 | 生产/测试应显式激活用户 |
| 默认密码 `admin` | 仅用于本地演示 | 任何共享环境必须修改 |
| 无固定 seed | 重建后数据不同 | 需要可复现时 `random.seed(0)` |
| `demo.sqlite` 可能过期 | 模型新增列后旧库不会自动迁移 | 删除后重建，或引入迁移工具 |

## 8. 配置

### 8.1 demo 显式设置的配置

| 配置 | 值 | 作用 |
| --- | --- | --- |
| `APP_NAME` | `"FlaskDemo"` | 应用名（TOTP issuer 等） |
| `SECRET_KEY` | `"demo"` | 会话、CSRF、令牌派生密钥；**仅本地** |
| `DATABASE_FILE` | `examples/demo/demo.sqlite` 的绝对路径 | 数据库文件位置 |
| `SQLALCHEMY_DATABASE_URI` | `sqlite:///<DATABASE_FILE>` | SQLAlchemy 连接串 |

### 8.2 可选实例配置

```python
app.config.from_pyfile("config.py", silent=True)
app.config.from_pyfile("config_prod.py", silent=True)
```

- 文件不存在时静默跳过。
- 文件从 Flask 的 **instance 目录**读取，不是你启动命令的当前目录。
- instance 目录取决于应用如何被导入：
  - 在 `examples/demo` 内启动：instance 路径通常为 `examples/demo/../instance`（≈ `examples/instance`）。
  - 从仓库根目录启动：instance 路径通常为仓库根目录下的 `instance/`。

> 启动命令见 0.2，本节只说明 instance 路径差异。

修改配置前先用下面代码确认实际路径：

```python
from examples.demo import create_app
app = create_app()
print(app.instance_path)
```

### 8.3 常用配置

配置项、默认值与取值约束只在 `flask-exts/docs/configure.rst` 维护；demo 不复制配置表。

demo 额外注意：

- 测试客户端需自行处理 CSRF token（demo 保持默认开启）。
- 未配置 `NOREPLY_EMAIL_SENDER` 时，邮件流程只记录 warning，不真正发信。
- 需要 JWT 功能时再配置 `JWT_SECRET_KEY` / `JWT_HASH`。

### 8.4 生产化前必须修改

- `SECRET_KEY`：换成随机、足够长的值。
- `admin` 密码：立即修改，或删除示例用户。
- `SQLALCHEMY_DATABASE_URI`：不要指向 demo 的 SQLite。
- `CSRF_ENABLED`：保持开启。
- 邮件、日志、静态资源、HTTPS、反向代理。

完整的威胁模型、认证/授权边界、密钥轮换、安全配置与发布检查见 [`security.md`](./security.md)。demo 的 `admin/admin` 只用于本地演示，不能作为安全默认值。

## 9. 扩展 Demo Recipes

### 9.1 新增一个模型 + 视图 + 种子数据

```python
# models/category.py
from sqlalchemy.orm import Mapped, mapped_column
from . import db


class Category(db.Model):
    __tablename__ = "category"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(unique=True)

    def __str__(self):
        return self.name
```

```python
# models/__init__.py
from .category import Category
__all__ = [..., "Category"]
```

```python
# views/category_view.py
from flask_exts.admin.sqla.view import SqlaModelView
from ..models.category import Category


class CategoryView(SqlaModelView):
    column_list = ("id", "name")
    column_searchable_list = ("name",)


categoryview = CategoryView(Category)
```

```python
# admin_views.py
from .views.category_view import categoryview
admin.register_view(categoryview)
```

```python
# build_sample.py
from .models.category import Category
...
db.session.add_all([Category(name="News"), Category(name="Tech")])
db.session.commit()
```

最后删除 `demo.sqlite` 并重启。

### 9.2 新增自定义过滤器

参考 `views/post_view.py` 的 `FilterNameBrown`：

```python
class FilterByColor(BaseSQLAFilter):
    def __init__(self, column_type, column, name, data_type=None, options=None):
        super().__init__(
            column_type, column, name, data_type,
            options=(("red", "Red"), ("blue", "Blue")),
        )

    def apply(self, query, value):
        return query.add_filter(self.column, "==", value)

    def operation(self):
        return "is color"
```

加入 `column_filters`：

```python
column_filters = ("id", "title", FilterByColor(...))
```

### 9.3 新增 Inline 子表单

前提：父子模型存在关系（一对多或一对一）。

```python
from flask_exts.admin.sqla.inline.inline_model_convert import InlineForm
from flask_exts.admin.sqla.view import SqlaModelView


class ParentView(SqlaModelView):
    inline_models = (
        InlineForm(
            Child,
            form_columns=("name", "value"),
            form_args={"name": {"label": "Child name"}},
        ),
    )
```

注意：

- 子模型必须有指向父模型的外键/关系。
- 如果 Inline 子模型配置了 `ajax_refs`，当前实现存在已知参数不匹配问题（见 `spec.md` 第 10.16.1 节 C1）；先补测试再修复。
- Inline 行通过 AJAX 保存，新增父记录后才会出现可编辑行。

### 9.4 新增 AJAX 外键

`ajax_refs` 的字段语义与完整配置见 `spec.md` 第 10.10 节；demo 的实际取值见 `views/post_view.py`，本节不重复代码。

前提：

- 外键关系存在。
- 关联模型的 Admin 视图已注册（AJAX 查询需要对应路由/模型）。
- 页面会调用 `/admin/<view>/ajax/lookup/`。

### 9.5 新增自定义列表模板

步骤：

1. 在视图中设置 `list_template = "<name>.html"`。
2. 模板 `extends "admin/model/list.html"`，在需要的位置保留 `{{ super() }}`。
3. 需要向模板传参时覆盖 `render()`，用 `super().render(template, extra="value", **kwargs)`。

最小示例见 `spec.md` 第 10.14.2 节；demo 实例见 `views/tree_view.py` 与 `templates/tree_list.html`。

### 9.6 新增上传字段

`FileField` 的 `save_path` 必须指向已存在的目录：

```python
import os.path as op
from flask_exts.forms.fields import FileField

upload_dir = op.join(op.dirname(__file__), "static", "uploads")
os.makedirs(upload_dir, exist_ok=True)

class FooView(SqlaModelView):
    form_extra_fields = {
        "image": FileField(
            label="Image",
            save_path=upload_dir,
            allow_overwrite=False,
        )
    }
```

本地演示可以写入 `static/uploads/`；生产不要这样做。`form_extra_fields` 中的字段如需出现在表单里，必要时配合 `form_columns` 显式包含。

### 9.7 新增 CLI 命令（可选）

demo 目前没有自定义 CLI。需要时在 `make_app.py` 的 `init_app(app)` 中注册（`app` 必须在该作用域内）：

```python
import click


def init_app(app: Flask):
    exts = ExtensionManager()
    exts.init_app(app)

    # ... 模型导入与视图注册 ...

    @app.cli.command("seed-demo")
    def seed_demo():
        """Rebuild demo data."""
        from .build_sample import build_sample_db

        build_sample_db()
        click.echo("demo data rebuilt")
```

然后：

```bash
flask --app __init__ seed-demo
```

> `@app.cli.command` 默认在 app context 中执行；`build_sample_db()` 会 `drop_all()`，只在本地使用。

## 10. 常见问题

| 现象 | 原因 | 处理 |
| --- | --- | --- |
| `ModuleNotFoundError: flask_exts` | 没有安装项目 | `python -m pip install -e .` |
| `attempted relative import with no known parent package` | 在错误目录/用错误模块名启动 | `cd examples/demo && flask --app __init__ run`，或根目录 `flask --app examples.demo run` |
| `sqlite3.OperationalError: no such column: author.cdate` | `demo.sqlite` 是旧 schema，文件存在但模型已变 | 删除 `examples/demo/demo.sqlite` 后重启 |
| 访问 `/admin/author/` 403 | 未登录或用户没有 `admin` 角色 | 用 `admin/admin` 登录；检查角色是否创建。`/admin/` 本身是公开门户，可能返回 200 |
| 登录后仍回到登录页 | 用户不存在/密码错误/角色缺失 | 删除数据库重建，确认 `build_user_admin()` 执行 |
| 端口 5000 被占用 | 其他服务占用 | `flask --app __init__ run --port 5001` |
| 注册后没有收到邮件 | 未配置 `NOREPLY_EMAIL_SENDER` | 这是 demo 的预期行为；需要时配置 SMTP |
| 配置 `config.py` 不生效 | instance 目录不是当前目录 | 打印 `app.instance_path`，把配置放到该目录 |
| `RuntimeError: Exts extension already initialized` | 同一进程重复初始化同一 app/多个 app | 每个进程只创建一个 app；多 app 先 `dispose()` |
| `ValueError: View with name ... already exists` | 视图名重复 | 修改 `name=` 或检查重复注册 |
| 列表页空/字段缺失 | 模型/视图配置不一致 | 检查 `column_list`、模型导入、是否重建数据库 |
| 导出 500 | `export_types` 需要 tablib 支持 | 使用 `csv` 或确认已安装 tablib |
| `demo.sqlite` 出现在 `git status` | 被其他规则覆盖或手动 add | 确认 `.gitignore` 的 `*.sqlite`；不要提交 |

## 11. 验证清单

修改 demo 后，至少完成以下检查：

### 11.1 静态检查

- [ ] `python -m compileall examples/demo` 通过
- [ ] `flask --app __init__ routes` 能列出预期路由
- [ ] 没有新增未使用的 import / 死代码（`file_op.py` 等已知未接入项除外）

### 11.2 启动与页面

- [ ] 删除 `demo.sqlite` 后能自动建库
- [ ] `/` 返回 200
- [ ] `/admin/` 门户返回 200（`allow_access=True`，未登录也可访问）
- [ ] `/admin/author/` 未登录返回 403（或按授权配置重定向）
- [ ] `admin/admin` 能登录
- [ ] 登录后 `/admin/author/` 列表可打开（无 `no such column`）
- [ ] `/admin/post/` 列表、关联列、筛选可用
- [ ] `/admin/tag/` 列表可打开
- [ ] `/admin/tree/` 使用自定义模板，`foo` 显示为 `bar`
- [ ] Author 编辑页 Inline 能新增/编辑/删除 Post
- [ ] Post 列表能按作者、日期排序，能按标题/作者搜索
- [ ] CSV 导出可用；XLS 在安装 `tablib[xls]` 后可用
- [ ] `Post` 的 AJAX 作者外键能搜索并保存
- [ ] 修改/新增模型后，重建数据库仍可用

### 11.3 冒烟测试片段（可选）

在仓库根目录执行：

```python
from examples.demo import create_app

app = create_app()
app.config["CSRF_ENABLED"] = False
client = app.test_client()

assert client.get("/").status_code == 200
assert client.get("/admin/").status_code == 200  # portal index is public
assert client.get("/admin/author/").status_code in (302, 403)

assert client.post(
    "/user/login/",
    data={"username": "admin", "password": "admin"},
).status_code == 302

assert client.get("/admin/author/").status_code == 200
print("demo smoke ok")
```

> 该片段会读取现有 `demo.sqlite`；如果 schema 过期，先删除并重建。CSRF 关闭仅用于脚本冒烟，不要用于生产配置。

### 11.4 提交前

- [ ] `git status` 中没有 `demo.sqlite`、上传文件、日志、密钥
- [ ] `examples/README.rst` 的启动命令与实际一致
- [ ] 新增视图/模型已加入 `models/__init__.py`、`admin_views.py`
- [ ] 示例数据可重复生成（必要时固定 seed）
- [ ] 模板 `extends` 正确且保留 `{{ super() }}`
- [ ] 没有把 demo 专属配置写进库代码

## 12. 编写规范

### 12.1 代码风格

- Python 3.10+；使用 `Mapped` / `mapped_column`。
- 双向关系用 `back_populates`，不用 `backref`。
- 优先 f-string，避免 `.format()` / `%`。
- 公共函数/方法加类型注解与简洁 Google 风格 docstring。
- 变量、注释、docstring 用英文；示例文档用中文。
- 模块级变量只放不可变或有意共享的配置（如 `DEFAULT_SORT`），避免可变全局状态。

### 12.2 Demo 特有约定

- 一个视图只演示一个主题；复杂配置加注释说明“为什么”。
- 不引入新的运行时依赖；需要新依赖先询问。
- 不把真实密钥、真实用户数据、生产数据库写进 demo。
- 新增随机数据时固定 seed，或明确说明不可复现。
- 新增模板时优先 `extends` 内置模板，而不是复制整份 HTML。
- 新增页面时提供最小可访问路径，并更新本文第 2/5/11 章。

### 12.3 文件放置

| 内容 | 位置 |
| --- | --- |
| 模型 | `models/<name>.py`，并在 `models/__init__.py` 导入 |
| Admin 视图 | `views/<name>_view.py` |
| 视图注册 | `admin_views.py` |
| 种子数据 | `build_sample.py` |
| 模板 | `templates/<name>.html` |
| 静态文件 | `static/`（仅本地演示） |
| 应用配置 | `make_app.py` 或 instance 配置 |

## 13. 与主文档、测试文档的关系

| 文档 | 角色 | 与 demo 的关系 |
| --- | --- | --- |
| `requirements.md` | 行为契约 | 定义模型、Admin、表单、安全等行为契约；demo 可用于展示相关用法 |
| `spec.md` | 设计与领域说明 | 说明项目设计背景及 View/Admin 的实现、配置与已知问题 |
| `testing.md` | 测试驱动 | 定义测试分层、fixtures、用例；demo 可作为 E2E/手工冒烟的对象 |
| `demo.md`（本文） | 示例驱动 | 规定 demo 如何组织、运行、扩展和验证 |

推荐工作流：

1. 先在 `requirements.md` 确认/更新契约，并按需同步 `spec.md` 等领域说明；
2. 在 `testing.md` 补对应测试或用例；
3. 在 `examples/demo` 落地可运行示例；
4. 按本文第 11 章验证；
5. 更新 `examples/README.rst` 与本文第 11 章说明。
