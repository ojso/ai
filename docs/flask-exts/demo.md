# Flask-Exts Demo 编写指南

> 本文是 `examples/demo` 的**编写、运行与维护指南**，面向需要新增/修改示例应用、数据模型、Admin 视图、模板和初始化数据的贡献者。
>
> | 项目 | 内容 |
> | --- | --- |
> | 文档版本 | v0.1 |
> | 状态 | 可用 |
> | 最后更新 | 2026-11-18 |
> | 数据快照 | 2026-11-13（发布版本 `0.4.2`；HEAD `445b03d1fe6c59cd53405c8187de968c687a2909`；内容核对基线 `171b40968f309c04ae3ad423696227c2767b0055`）。2026-11-18 `examples/demo` 启用 `SECURITY_AUTHORIZER="rbac"`，并新增 `user_interest` 模型与 `InterestView` 对象级授权示例；随 `0.5.0` 提交（HEAD `ca9f325fa2d43f53eaf14ca71a77ee75b1471406`，标签已推送并发布至 PyPI）。 |
> | 适用目录 | `flask-exts/examples/demo`——代码仓库根目录下的示例应用；本文其余位置简写的 `examples/demo` 均指此路径，命令中的该路径相对仓库根目录执行 |
>
> **定位**：`examples/demo` 是**可运行的参考应用**，不是生产模板。它用尽量少的代码展示 Flask-Exts 的模型、Admin、Inline、筛选、排序、导出、AJAX、递归关系和自定义模板能力。修改 demo 时优先保证“能运行、能看懂、不引入额外依赖”。

## 0. 快速开始

### 0.1 环境准备

环境初始化命令只在 `testing.md` 第 0.1 节维护；这里不复制。

> demo 只依赖库本身的运行时依赖，不需要额外安装 `factory-boy`、`selenium` 等测试工具。

### 0.2 启动

执行前先向用户确认代码仓库根目录；下文中的“仓库根目录”均指该确认路径，不假定固定位置。

对外启动说明列出的方式是在 `examples/demo` 目录运行：

- **执行目录**：`examples/demo`
- **命令**：`uv run flask --app __init__ run`

`uv run` 使用仓库根目录 `uv sync` 创建的项目 `.venv`；依赖安装方式见 `testing.md` 第 0.1 节。

端口、调试和 CLI 子命令沿用 `--app __init__`，见第 0.3、0.4 节。

**命令来源**：

- 对外启动命令以 `examples/README.rst` 为准；该文件只列出上述方式。
- 未经验证的仓库根目录启动变体不列为受支持方式。

打开：

- 首页：`http://localhost:5000/`
- Admin：`http://localhost:5000/admin/`
- 登录：`http://localhost:5000/user/login/`

默认账号：

- **用户名**：`admin`
- **密码**：`admin`
- **角色**：`admin`

RBAC 演示账号：

- **用户名/密码**：`alice` / `alice`、`bob` / `bob`
- **角色**：无 `admin` 角色
- **用途**：只能访问兴趣视图；可查看所有用户的兴趣，但只能编辑自己的记录

> 默认密码仅用于本地演示。任何可被他人访问的环境都必须修改。

### 0.3 常用命令

以下是对外启动方式的附加 CLI 示例；运行目录与 `--app` 约定见第 0.2 节：

```bash
# 查看路由，确认应用可导入
uv run flask --app __init__ routes

# 指定端口
uv run flask --app __init__ run --port 5001

# 开启调试
uv run flask --app __init__ run --debug
```

### 0.4 重置数据库

仅在可丢弃的本地 demo 数据库上操作。执行前确认当前目录为仓库根目录、目标文件是 `examples/demo/demo.sqlite` 且数据可删除；禁止在生产环境或含真实数据的数据库上执行。先停止正在运行的 demo，再执行：

```bash
rm examples/demo/demo.sqlite
```

删除后进入 `examples/demo` 目录，按第 0.2 节重新启动。demo 只在数据库文件**不存在**时初始化。

删除后会重新执行 `build_sample_db()`：建表、写入示例树/作者/文章/标签，并创建 `admin/admin`。

> `demo.sqlite` 已被 `.gitignore` 的 `*.sqlite` 规则忽略，不要提交。

## 1. 定位与边界

### 1.1 demo 要展示什么

- **应用与示例数据**：`make_app.py`、`build_sample.py`
- **模型与关系**：`models/`
- **Admin 视图**：`views/`、`admin_views.py`
- **模板与静态资源**：`templates/`、`static/`
- **授权器切换**：`make_app.py` 通过 `SECURITY_AUTHORIZER = "rbac"` 启用 `RBACAuthorizer`；授权规则见 [`security.md` 4.6](./security.md#46-可选-rbacauthorizer)
- **RBAC 对象级授权**：`InterestView` 用 `Authenticated()` 放行全量只读，用 `Predicate` 把编辑限制到当前用户自己的 `UserInterest`

各视图展示点见第 5.2 节，模板接入状态见第 6.3 节。

### 1.2 demo 不负责什么

- 生产级安全（默认密码、`SECRET_KEY="demo"`、无 HTTPS、无 CSRF 配置加固）。
- 数据库迁移（直接 `drop_all()` / `create_all()`，不是 Alembic）。
- 邮件发送配置（未配置 `NOREPLY_EMAIL_SENDER`，注册流程不会真的发信）。
- 部署、反向代理、静态资源 CDN。
- 完整测试覆盖（demo 的测试策略见 `testing.md`，目前以手工冒烟为主）。

### 1.3 修改原则

修改应保持 demo 可运行、轻量且不提交生成物；代码风格与文件放置约定见第 12 节。

## 2. 目录结构

```text
examples/
├── README.rst
├── simple/                 # 最小 Admin 示例
└── demo/
    ├── __init__.py
    ├── make_app.py          # 应用工厂
    ├── admin_views.py       # Admin 视图注册
    ├── build_sample.py      # 示例数据
    ├── file_op.py           # 上传辅助模块（未接入路由）
    ├── models/              # author、post、tag、post_tag、tree、user_interest
    ├── views/               # author、interest、post、tag、tree
    ├── templates/           # tree_list.html 等示例模板
    └── static/
```

`simple/` 是最小示例；`demo/` 展示数据模型、Admin 视图、模板和示例数据。运行时数据库与未接入路由的模板/辅助模块见第 0.4、6.3、6.4 节。

## 3. 启动流程

### 3.1 调用链

以下以对外说明中的启动方式为例：在 `examples/demo` 目录执行 `uv run flask --app __init__ run`。

```text
uv run flask --app __init__ run
        │
        ▼
examples/demo/__init__.py  →  create_app()
        │
        ▼
make_app.create_app()
  1. Flask(__name__, instance_relative_config=True)
  2. 设置 APP_NAME / SECRET_KEY / SECURITY_AUTHORIZER
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
4. **授权器在扩展初始化时确定**：`ExtensionManager.init_app()` 初始化 `Security` 插件时读取 `SECURITY_AUTHORIZER`，因此该配置必须在第 3.1 节调用链的第 5 步之前写入；未声明要求的视图回落到共享的 `admin` 角色规则，`InterestView` 的按方法 requirement 见第 5.7 节。
5. **初始化只跑一次**：`db` 是模块级单例，同一进程不要重复 `create_app()` 后同时持有两个 app；测试/多 app 场景先 `dispose()`。

### 3.3 配置与数据库边界

- `create_app()` 可加载 instance 目录中的配置文件；路径确认方法见第 8.2 节。
- `DATABASE_FILE` 固定为 `examples/demo/demo.sqlite`，不受启动目录影响。
- 首次建库时才自动加载示例数据；触发条件见第 7.2 节，安全重置步骤见第 0.4 节。

## 4. 数据模型

### 4.1 关系图

```text
Author 1 ─────── N Post N ─────── M Tag
   │                  │
   │ featured_post_id │
   └──────────────────┘  (Author 的可空外键指向 Post)

Tree 1 ─────── N Tree
      parent_id

User 1 ─────── 1 UserInterest
                user_id（唯一，指向 users.id）
```

`User` 来自库的 `userstore`；其余模型定义在 `examples/demo/models/`。

### 4.2 模型职责

- `Author`
  - 表：`author`
  - 关键字段：`type`、`email`（唯一）、`featured_post_id`、电话/日期字段
  - 演示点：枚举、hybrid property、1-N、指向 Post 的可空外键

- `Post`
  - 表：`post`
  - 关键字段：`title`、`text`、`color`、`date`、`author_id`
  - 演示点：1-N、M-N、可排序/可搜索字段

- `Tag`
  - 表：`tag`
  - 关键字段：`name`（唯一）
  - 演示点：最简模型

- `post_tag`
  - 表：`post_tag`
  - 关键字段：`post_id`、`tag_id`
  - 演示点：多对多关联表

- `Tree`
  - 表：`tree`
  - 关键字段：`name`、`parent_id`
  - 演示点：自引用/递归关系

- `UserInterest`
  - 表：`user_interest`
  - 关键字段：`user_id`（唯一，指向 `users.id`）、`content`
  - 演示点：1:1 归属、单向关系、RBAC 对象级授权

### 4.3 关系约定

模型使用 SQLAlchemy 2.0 `Mapped` / `mapped_column`。双向关系显式使用 `back_populates`；`Author` / `Post` 展示一对多，`Post` / `Tag` 使用独立关联表，`Tree` 展示自引用关系。具体字段和关系以 `models/` 中的示例为准。

`UserInterest.user` 是单向关系：反向属性需要落在库的 `User` 模型上，demo 不为示例新增库 schema；1:1 由 `user_id` 的唯一约束保证。

### 4.4 `Author.phone_number`

`Author.phone_number` 是同时支持 Python 对象与 SQL 表达式的 `hybrid_property`；当前未加入 `AuthorView.column_list`。实现见 `models/author.py`。

### 4.5 新增模型

新增模型、Admin 视图和示例数据的步骤集中见第 9.1 节，避免维护两份流程。

## 5. Admin 视图

> View/ModelView/SqlaModelView 的配置、DataBackend、Inline、AJAX、导出与已知问题见 [`spec.md` 第 10 章](./spec.md#10-view-与-admin-专题)。本章只说明 demo 中的实际用法；完整 demo 类以本章与 `examples/demo` 为主，`spec.md` 第 10 章只保留最小 API 片段。

### 5.1 注册方式

视图实例集中在 `admin_views.py`，通过 `admin.register_view()` 注册。`is_menu=False` 可隐藏菜单；重复的视图名会抛 `ValueError`，默认名称取类名。

### 5.2 视图能力对照

- `AuthorView`
  - 模型：`Author`
  - 演示点：Inline 子表单、分页、导出、排序、筛选、可编辑列、自定义表单参数

- `PostView`
  - 模型：`Post`
  - 演示点：关联列、关联搜索、多列排序、自定义过滤器、AJAX 外键、导出

- `TagView`
  - 模型：`Tag`
  - 演示点：最小可用视图

- `TreeView`
  - 模型：`Tree`
  - 演示点：自定义列表模板、`render()` 传参、递归关系

- `InterestView`
  - 模型：`UserInterest`
  - 演示点：RBAC 登录门、`Authenticated()` 全量只读、`Predicate` 仅本人编辑

### 5.3 `AuthorView`

`AuthorView` 展示 Inline `Post`、表单 choices/validators、只读字段、固定分页和禁用删除。编辑表单将 `featured_post` 限定为当前作者的文章；`DEFAULT_SORT` 的格式见 [`spec.md` 第 10.4.2 节](./spec.md#1042-配置属性)。完整取值以 `views/author_view.py` 为准。

### 5.4 `PostView`

`PostView` 展示关联列与搜索、多列排序、自定义过滤器、作者 AJAX 外键和导出。XLS 需要可选的 `tablib[xls]`；CSV 不依赖该扩展。具体配置见 `views/post_view.py`，功能语义见 `spec.md` 第 10.7.5～10.7.7、10.11 节。

### 5.5 自定义过滤器

demo 自定义过滤器 `FilterNameBrown`、`FilterLike` 的配置见 `views/post_view.py`；过滤器 API 与实现示例见 `spec.md` 第 10.7.4 节。

### 5.6 `TreeView`：自定义模板与传参

`TreeView` 的 demo 实现在 `views/tree_view.py` 与 `templates/tree_list.html`；模板需保留父模板内容（`{{ super() }}`），`render()` 可传额外模板参数。通用模板 API 见 `spec.md` 第 10.14.2 节。

### 5.7 `InterestView`：RBAC 对象级授权

`InterestView` 展示 `RBACAuthorizer` 的按方法 requirement，实现在 `views/interest_view.py`：

- `permission = Authenticated()`
  - 作用：任何已登录用户都能读取全部兴趣（列表、详情、导出）。
  - 登录门先于 requirement：匿名请求直接 403，不会进入该判定。

- `permissions = {"create_view": ..., "edit_view": ...}`
  - `create_view`：仅当当前用户还没有兴趣记录时放行。
  - `edit_view`：`Predicate` 读取 `request.args["id"]` 对应的记录，只有 `user_id` 等于当前用户时才放行。
  - 键必须是被包装的方法名（`create_view` / `edit_view` / `delete_view`）；写成 `"delete"` 之类的 URL 动作名不会匹配，静默回落到视图级 `permission`。

- 归属写入
  - 表单只包含 `content`，`user_id` 不在表单中。
  - `create_model()` 用 `current_user.id` 写入归属，请求无法改归属。

- 删除
  - `can_delete = False`，并在 `action_disallowed_list` 中禁用 `delete`；页面不出现删除入口，直接构造删除请求也不会删除记录。

- 内联编辑（未启用）
  - 视图未设置 `column_editable_list`，`ajax_update` 会直接返回 404。
  - 若以后启用列表内联编辑，必须同时为 `ajax_update` 声明读取 `pk` 的归属谓词，否则该接口会绕过 `edit_view` 的对象检查。

- 管理员例外
  - `admin` 角色命中共享超级用户规则，可编辑任意用户的兴趣；普通用户只受自身 `Predicate` 约束。

- 1:1 约束
  - `user_interest.user_id` 唯一；模型侧只声明单向 `user` 关系，反向属性不落在库的 `User` 上。

判定顺序：共享登录门 → 按方法名取 requirement → `Predicate` 做对象归属检查 → 未声明的方法使用视图级 `Authenticated()`。

### 5.8 新增 Admin 视图的标准步骤

已有模型新增视图时，在 `views/` 创建 `foo_view.py` 并于 `admin_views.py` 注册。新增模型、视图与种子数据的完整步骤见第 9.1 节；需要新表时按第 0.4 节重建可丢弃的本地数据库。

## 6. 模板与静态资源

### 6.1 模板查找顺序

Flask 会先找应用自己的 `templates/`，再找扩展提供的模板。demo 的 `templates/tree_list.html` 因此可以覆盖/扩展库内模板。

### 6.2 可覆盖的块

内置模板的块名称、覆盖范围与语义见 `spec.md` 第 10.14.2 节；demo 当前只接入 `tree_list.html`。

### 6.3 当前模板说明

- `tree_list.html`
  - 状态：已接入
  - 说明：通过 `TreeView.list_template` 使用

- `field_list.html`
  - 状态：未接入
  - 说明：展示如何为字段写宏；需要视图/表单显式引用才会生效

- `locations.html`
  - 状态：未接入
  - 说明：独立页面示例；当前没有路由渲染它

> 未接入的模板可以保留作为参考，但不要在文档中声称它们已生效；如果要启用，请补路由/视图并加入第 11 章验证。

### 6.4 静态资源

- 当前只有 `static/favicon.ico`。
- `file_op.py` 提供了 `save_image()` / `remove_image()`，但**当前没有路由使用**；它适合作为上传功能的起点。
- 上传文件写入 `static/` 只适合本地演示；生产应使用对象存储或独立上传目录，并校验扩展名/大小。

### 6.5 自定义页面（非模型视图）

非模型页面不必使用 `SqlaModelView`；路由、权限与模板配置见 `spec.md` 第 10.0.2 节。

## 7. 示例数据

### 7.1 `build_sample_db()` 做了什么

`build_sample_db()` 会重建已注册模型的表并生成以下数据：

- **Tree**：1 个 Trunk、5 个 Branch、25 个 Leaf
- **Post**：25 个作者、9 个标签、25 篇文章
- **用户**：创建初始 `admin` 用户并分配 `admin` 角色
- **RBAC 演示数据**：创建 `alice`、`bob`（无 `admin` 角色），各写入一条 `UserInterest`

该函数含 `drop_all()`，只允许用于可丢弃的本地 demo 数据库。

### 7.2 触发条件

`create_app()` 仅在 `demo.sqlite` 不存在时调用 `build_sample_db()`；文件已存在时不会重建或迁移 schema。模型变更后，仅对可丢弃的本地数据库按第 0.4 节重置；不得对真实数据调用该函数。

### 7.3 数据随机性

`build_sample_post()` 使用 `random.choice` / `random.sample`，没有固定 seed：

- 每次重建的作者电话/币种/时区、文章日期、标签组合都可能不同。
- 如果希望可复现，在 `build_sample_db()` 开头加 `random.seed(0)`。
- 不要让演示数据依赖随机结果做断言；需要稳定数据时显式指定。

### 7.4 已知问题

- `author.coutry = country[1]`
  - 说明：字段名拼写错误，值不会持久化
  - 处理：修正或删除；不要照抄

- `admin` 用户未显式 `is_active=True`
  - 说明：HEAD 中 `User._is_active` 默认值为 `True`，demo 依赖该默认值；`SimpleAuthorizer` 已在 0.4.2 改为先拒绝 inactive 用户，再判断 `admin` 角色（SEC-01 已修复）
  - 处理：演示无需额外设置；生产禁用管理员时仍建议同时移除 `admin` 角色或删除账号

## 8. 配置

### 8.1 demo 显式设置的配置

- `APP_NAME`
  - 值：`"FlaskDemo"`
  - 作用：应用名（TOTP issuer 等）

- `SECRET_KEY`
  - 值：`"demo"`
  - 作用：会话、CSRF、令牌派生密钥；**仅本地**

- `SECURITY_AUTHORIZER`
  - 值：`"rbac"`
  - 作用：启用 `RBACAuthorizer`；`InterestView` 使用 `Authenticated()` 与 `Predicate`，其余视图未声明要求时回落到 `admin` 角色规则（`admin/admin` 仅本地演示）；规则见 [`security.md` 4.6](./security.md#46-可选-rbacauthorizer)

- `DATABASE_FILE`
  - 值：`examples/demo/demo.sqlite` 的绝对路径
  - 作用：数据库文件位置

- `SQLALCHEMY_DATABASE_URI`
  - 值：`sqlite:///<DATABASE_FILE>`
  - 作用：SQLAlchemy 连接串

### 8.2 可选实例配置

```python
app.config.from_pyfile("config.py", silent=True)
app.config.from_pyfile("config_prod.py", silent=True)
```

- 文件不存在时静默跳过。
- 文件从 Flask 的 **instance 目录**读取，不是启动命令的当前目录。
- instance 路径取决于 Flask app 的导入路径；修改配置前用下方代码读取 `app.instance_path`，不要按工作目录猜测。

> 启动命令见第 0.2 节。

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

demo 不是生产模板。生产配置与发布前安全要求见 [`security.md`](./security.md)；demo 的 `SECRET_KEY="demo"` 和 `admin/admin` 仅限本地演示。

## 9. 扩展 Demo Recipes

### 9.1 新增一个模型 + 视图 + 种子数据

1. 在 `models/` 定义模型，并在 `models/__init__.py` 导入。
2. 在 `views/` 定义对应视图，在 `admin_views.py` 注册。
3. 按需在 `build_sample.py` 增加示例数据。
4. 按第 0.4 节重置可丢弃的本地 demo 数据库，确认页面可用。

字段和关系应沿用第 4 节现有模型模式；不要在此文复制完整源码。

### 9.2 新增自定义过滤器

demo 自定义过滤器见 `views/post_view.py` 与第 5.5 节；通用 API 和示例见 `spec.md` 第 10.7.4 节。

### 9.3 新增 Inline 子表单

demo 的 Author/Post Inline 配置见 `views/author_view.py`；子模型需有父子关系。通用配置见 `spec.md` 第 10.9 节。Inline 子模型同时启用 AJAX 外键时有已知问题 CR-001，详情见 `spec.md` 第 10.16.1 节。

### 9.4 新增 AJAX 外键

`PostView.ajax_refs` 展示作者外键查询；关联关系与 Admin 视图必须存在。实际取值见 `views/post_view.py`，字段和路由语义见 `spec.md` 第 10.10 节。

### 9.5 新增自定义列表模板

demo 模板扩展见第 5.6 节；通用 API 见 `spec.md` 第 10.14.2 节。

### 9.6 新增上传字段

`FileField.save_path` 必须指向已存在的目录。`file_op.py` 当前未接入路由；上传示例仅适用于本地演示，生产环境应使用受控存储。

### 9.7 新增 CLI 命令（可选）

demo 目前没有自定义 CLI。若新增，在 `make_app.py` 的 `init_app(app)` 中注册；会调用 `build_sample_db()` 的命令具有破坏性，只能用于可丢弃的本地数据库，遵循第 0.4 节。

## 10. 常见问题

- `ModuleNotFoundError: flask_exts`
  - 原因：没有安装项目
  - 处理：在仓库根目录执行 `uv sync`

- `attempted relative import with no known parent package`
  - 原因：在错误目录/用错误模块名启动
  - 处理：按第 0.2 节选择与执行目录匹配的启动模块名

- `sqlite3.OperationalError: no such column: author.cdate`
  - 原因：`demo.sqlite` 是旧 schema，文件存在但模型已变
  - 处理：先按第 7.2 节确认触发条件；仅可丢弃的本地库按第 0.4 节重置

- **访问 `/admin/author/` 403**
  - 原因：未登录或用户没有 `admin` 角色
  - 处理：使用第 0.2 节的本地演示账号；确认其有 `admin` 角色。`/admin/` 门户可匿名访问

- **登录后仍回到登录页**
  - 原因：用户不存在/密码错误/角色缺失
  - 处理：确认 `build_user_admin()` 执行；需重置时按第 0.4 节处理可丢弃的本地 demo 数据库

- **端口 5000 被占用**
  - 原因：其他服务占用
  - 处理：改用未占用端口，命令示例见第 0.3 节

- **注册后没有收到邮件**
  - 原因：demo 未配置 `NOREPLY_EMAIL_SENDER`
  - 处理：预期行为与配置边界见第 8.3 节

- **配置 `config.py` 不生效**
  - 原因：配置文件不在 Flask instance 目录
  - 处理：路径确认方法见第 8.2 节

- `RuntimeError: Exts extension already initialized`
  - 原因：同一进程重复初始化同一 app/多个 app
  - 处理：每个进程只创建一个 app；多 app 先 `dispose()`

- `ValueError: View with name ... already exists`
  - 原因：视图名重复
  - 处理：修改 `name=` 或检查重复注册

- **列表页空/字段缺失**
  - 原因：模型/视图配置不一致
  - 处理：检查 `column_list`、模型导入、是否重建数据库

- **导出 500**
  - 原因：`export_types` 需要 tablib 支持
  - 处理：使用 `csv` 或确认已安装 tablib

- `demo.sqlite` 出现在 `git status`
  - 原因：被其他规则覆盖或手动 add
  - 处理：确认 `.gitignore` 的 `*.sqlite`；不要提交

## 11. 验证清单

修改 demo 后，至少完成以下检查：

### 11.1 静态检查

- [ ] `python -m compileall examples/demo` 通过
- [ ] 按第 0.3 节的路由检查命令确认能列出预期路由
- [ ] 没有新增未使用的 import / 死代码（`file_op.py` 等已知未接入项除外）

### 11.2 启动与页面

- [ ] 按第 0.4 节重置可丢弃的本地 demo 数据库后能自动建库
- [ ] `/` 返回 200
- [ ] `/admin/` 门户返回 200（`allow_access=True`，未登录也可访问）
- [ ] `/admin/author/` 未登录默认返回 403；`login_required_functions` 也返回 403（不重定向）
- [ ] `admin/admin` 能登录
- [ ] 登录后 `/admin/author/` 列表可打开（无 `no such column`）
- [ ] `/admin/post/` 列表、关联列、筛选可用
- [ ] `/admin/tag/` 列表可打开
- [ ] `/admin/tree/` 使用自定义模板，`foo` 显示为 `bar`
- [ ] Author 编辑页 Inline 能新增/编辑/删除 Post
- [ ] Post 列表能按作者、日期排序，能按标题/作者搜索
- [ ] CSV 导出可用；XLS 在安装 `tablib[xls]` 后可用
- [ ] `Post` 的 AJAX 作者外键能搜索并保存
- [ ] `/admin/interest/` 未登录返回 403
- [ ] `alice/alice` 登录后能看到所有用户的兴趣（含 `bob`），详情页可打开
- [ ] `alice` 编辑自己的兴趣返回 200；编辑 `bob` 的兴趣返回 403
- [ ] 新注册用户可创建自己的兴趣（表单无 `user_id`）；再次创建返回 403
- [ ] `admin/admin` 可编辑任意用户的兴趣（`admin` 超级用户规则）
- [ ] 兴趣视图没有删除入口；直接构造删除或批量删除请求不会删除记录
- [ ] 修改/新增模型后，按第 0.4 节重建可丢弃的本地 demo 数据库并验证可用

### 11.3 冒烟测试片段（可选）

在仓库根目录执行：

```python
from sqlalchemy import select

from examples.demo import create_app
from examples.demo.models.user_interest import UserInterest
from flask_exts.datastore.sqla import db

app = create_app()
app.config["CSRF_ENABLED"] = False
client = app.test_client()

assert client.get("/").status_code == 200
assert client.get("/admin/").status_code == 200  # portal index is public
assert client.get("/admin/author/").status_code == 403

assert client.post(
    "/user/login/",
    data={"username": "admin", "password": "admin"},
).status_code == 302

assert client.get("/admin/author/").status_code == 200

alice = app.test_client()
assert alice.post(
    "/user/login/",
    data={"username": "alice", "password": "alice"},
).status_code == 302

with app.app_context():
    rows = db.session.scalars(select(UserInterest)).all()
    alice_id = next(row.id for row in rows if row.user.username == "alice")
    bob_id = next(row.id for row in rows if row.user.username == "bob")

assert alice.get("/admin/interest/").status_code == 200
assert alice.get(f"/admin/interest/edit/?id={alice_id}").status_code == 200
assert alice.get(f"/admin/interest/edit/?id={bob_id}").status_code == 403
print("demo smoke ok")
```

> 该片段会读取现有 `demo.sqlite`；若 schema 过期，仅对可丢弃的本地 demo 数据库按第 0.4 节重置。CSRF 关闭仅用于脚本冒烟，不要用于生产配置。
>
> demo 启用 `SECURITY_AUTHORIZER = "rbac"` 后，`author` / `post` 等未声明要求的视图仍回落到 `admin` 角色规则，与默认配置一致；`InterestView` 额外声明了 `Authenticated()` 与 `Predicate`，按第 5.7 节验证。

### 11.4 提交前

- [ ] `git status` 中没有 `demo.sqlite`、上传文件、日志、密钥
- [ ] 对外启动命令与第 0.2 节所指的权威说明一致
- [ ] 新增视图/模型已加入 `models/__init__.py`、`admin_views.py`
- [ ] 示例数据可重复生成（必要时固定 seed）
- [ ] 模板 `extends` 正确且保留 `{{ super() }}`
- [ ] 没有把 demo 专属配置写进库代码

## 12. 编写规范

### 12.1 代码风格

- Python 3.11+；使用 `Mapped` / `mapped_column`。
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

- **模型**：`models/{name}.py`，并在 `models/__init__.py` 导入
- **Admin 视图**：`views/{name}_view.py`
- **视图注册**：`admin_views.py`
- **种子数据**：`build_sample.py`
- **模板**：`templates/{name}.html`
- **静态文件**：`static/`（仅本地演示）
- **应用配置**：`make_app.py` 或 instance 配置

## 13. 与主文档、测试文档的关系

本文只维护 demo 的组织、运行与扩展说明。跨文档职责按 `README.md` 第 3、5、6 节；新增功能按契约、测试、安全文档及适用的工作流执行。启动命令来源与同步规则见第 0.2 节。
