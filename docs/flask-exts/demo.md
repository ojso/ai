# Flask-Exts Demo 编写指南

> 本文是 `examples/demo` 的**编写、运行与维护指南**，面向需要新增/修改示例应用、数据模型、Admin 视图、模板和初始化数据的贡献者。
>
> | 项目 | 内容 |
> | --- | --- |
> | 文档版本 | v0.1 |
> | 状态 | 可用 |
> | 最后更新 | 2026-11-10 |
> | 数据快照 | 2026-11-10（源码版本 `0.4.0`；HEAD `171b40968f309c04ae3ad423696227c2767b0055`） |
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

执行前先向用户确认代码仓库根目录；下表中的“仓库根目录”均指该确认路径，不假定固定位置。

对外启动说明列出的方式是在 `examples/demo` 目录运行：

| 执行目录 | 命令 |
| --- | --- |
| `examples/demo` | `flask --app __init__ run` |

端口、调试和 CLI 子命令沿用 `--app __init__`，见第 0.3、0.4 节。

**命令来源：**

- 对外启动命令以 `examples/README.rst` 为准；该文件只列出上表方式。
- 未经验证的仓库根目录启动变体不列为受支持方式。

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

以下是对外启动方式的附加 CLI 示例；运行目录与 `--app` 约定见第 0.2 节：

```bash
# 查看路由，确认应用可导入
flask --app __init__ routes

# 指定端口
flask --app __init__ run --port 5001

# 开启调试
flask --app __init__ run --debug
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

| 范围 | 主要入口 |
| --- | --- |
| 应用与示例数据 | `make_app.py`、`build_sample.py` |
| 模型与关系 | `models/` |
| Admin 视图 | `views/`、`admin_views.py` |
| 模板与静态资源 | `templates/`、`static/` |

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
    ├── models/              # author、post、tag、post_tag、tree
    ├── views/               # author、post、tag、tree
    ├── templates/           # tree_list.html 等示例模板
    └── static/
```

`simple/` 是最小示例；`demo/` 展示数据模型、Admin 视图、模板和示例数据。运行时数据库与未接入路由的模板/辅助模块见第 0.4、6.3、6.4 节。

## 3. 启动流程

### 3.1 调用链

以下以对外说明中的启动方式为例：在 `examples/demo` 目录执行 `flask --app __init__ run`。

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
```

### 4.2 模型职责

| 模型 | 表 | 关键字段 | 演示点 |
| --- | --- | --- | --- |
| `Author` | `author` | `type`、`email`（唯一）、`featured_post_id`、电话/日期字段 | 枚举、hybrid property、1-N、指向 Post 的可空外键 |
| `Post` | `post` | `title`、`text`、`color`、`date`、`author_id` | 1-N、M-N、可排序/可搜索字段 |
| `Tag` | `tag` | `name`（唯一） | 最简模型 |
| `post_tag` | `post_tag` | `post_id`、`tag_id` | 多对多关联表 |
| `Tree` | `tree` | `name`、`parent_id` | 自引用/递归关系 |

### 4.3 关系约定

模型使用 SQLAlchemy 2.0 `Mapped` / `mapped_column`。双向关系显式使用 `back_populates`；`Author` / `Post` 展示一对多，`Post` / `Tag` 使用独立关联表，`Tree` 展示自引用关系。具体字段和关系以 `models/` 中的示例为准。

### 4.4 `Author.phone_number`

`Author.phone_number` 是同时支持 Python 对象与 SQL 表达式的 `hybrid_property`；当前未加入 `AuthorView.column_list`。实现见 `models/author.py`。

### 4.5 新增模型

新增模型、Admin 视图和示例数据的步骤集中见第 9.1 节，避免维护两份流程。

## 5. Admin 视图

> View/ModelView/SqlaModelView 的配置、DataBackend、Inline、AJAX、导出与已知问题见 [`spec.md` 第 10 章](./spec.md#10-view-与-admin-专题)。本章只说明 demo 中的实际用法；完整 demo 类以本章与 `examples/demo` 为主，`spec.md` 第 10 章只保留最小 API 片段。

### 5.1 注册方式

视图实例集中在 `admin_views.py`，通过 `admin.register_view()` 注册。`is_menu=False` 可隐藏菜单；重复的视图名会抛 `ValueError`，默认名称取类名。

### 5.2 视图能力对照

| 视图 | 模型 | 演示点 |
| --- | --- | --- |
| `AuthorView` | `Author` | Inline 子表单、分页、导出、排序、筛选、可编辑列、自定义表单参数 |
| `PostView` | `Post` | 关联列、关联搜索、多列排序、自定义过滤器、AJAX 外键、导出 |
| `TagView` | `Tag` | 最小可用视图 |
| `TreeView` | `Tree` | 自定义列表模板、`render()` 传参、递归关系 |

### 5.3 `AuthorView`

`AuthorView` 展示 Inline `Post`、表单 choices/validators、只读字段、固定分页和禁用删除。编辑表单将 `featured_post` 限定为当前作者的文章；`DEFAULT_SORT` 的格式见 [`spec.md` 第 10.4.2 节](./spec.md#1042-配置属性)。完整取值以 `views/author_view.py` 为准。

### 5.4 `PostView`

`PostView` 展示关联列与搜索、多列排序、自定义过滤器、作者 AJAX 外键和导出。XLS 需要可选的 `tablib[xls]`；CSV 不依赖该扩展。具体配置见 `views/post_view.py`，功能语义见 `spec.md` 第 10.7.5～10.7.7、10.11 节。

### 5.5 自定义过滤器

demo 自定义过滤器 `FilterNameBrown`、`FilterLike` 的配置见 `views/post_view.py`；过滤器 API 与实现示例见 `spec.md` 第 10.7.4 节。

### 5.6 `TreeView`：自定义模板与传参

`TreeView` 的 demo 实现在 `views/tree_view.py` 与 `templates/tree_list.html`；模板需保留父模板内容（`{{ super() }}`），`render()` 可传额外模板参数。通用模板 API 见 `spec.md` 第 10.14.2 节。

### 5.7 新增 Admin 视图的标准步骤

已有模型新增视图时，在 `views/` 创建 `foo_view.py` 并于 `admin_views.py` 注册。新增模型、视图与种子数据的完整步骤见第 9.1 节；需要新表时按第 0.4 节重建可丢弃的本地数据库。

## 6. 模板与静态资源

### 6.1 模板查找顺序

Flask 会先找应用自己的 `templates/`，再找扩展提供的模板。demo 的 `templates/tree_list.html` 因此可以覆盖/扩展库内模板。

### 6.2 可覆盖的块

内置模板的块名称、覆盖范围与语义见 `spec.md` 第 10.14.2 节；demo 当前只接入 `tree_list.html`。

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

非模型页面不必使用 `SqlaModelView`；路由、权限与模板配置见 `spec.md` 第 10.0.2 节。

## 7. 示例数据

### 7.1 `build_sample_db()` 做了什么

`build_sample_db()` 会重建已注册模型的表并生成以下数据：

| 数据 | 示例规模 |
| --- | --- |
| Tree | 1 个 Trunk、5 个 Branch、25 个 Leaf |
| Post | 25 个作者、9 个标签、25 篇文章 |
| 用户 | 创建初始 `admin` 用户并分配 `admin` 角色 |

该函数含 `drop_all()`，只允许用于可丢弃的本地 demo 数据库。

### 7.2 触发条件

`create_app()` 仅在 `demo.sqlite` 不存在时调用 `build_sample_db()`；文件已存在时不会重建或迁移 schema。模型变更后，仅对可丢弃的本地数据库按第 0.4 节重置；不得对真实数据调用该函数。

### 7.3 数据随机性

`build_sample_post()` 使用 `random.choice` / `random.sample`，没有固定 seed：

- 每次重建的作者电话/币种/时区、文章日期、标签组合都可能不同。
- 如果希望可复现，在 `build_sample_db()` 开头加 `random.seed(0)`。
- 不要让演示数据依赖随机结果做断言；需要稳定数据时显式指定。

### 7.4 已知问题

| 问题 | 说明 | 处理 |
| --- | --- | --- |
| `author.coutry = country[1]` | 字段名拼写错误，值不会持久化 | 修正或删除；不要照抄 |
| `admin` 用户未显式 `is_active=True` | HEAD 中 `User._is_active` 默认值为 `True`；但 `SimpleAuthorizer` 在 active 检查前放行 `admin` 角色，禁用管理员仍可能保有权限（SEC-01） | demo 显式设置账号状态；生产禁用管理员时同时移除 `admin` 角色或删除账号 |

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

demo 的 Author/Post Inline 配置见 `views/author_view.py`；子模型需有父子关系。通用配置见 `spec.md` 第 10.9 节。Inline 子模型同时启用 AJAX 外键时有已知问题 C1，详情见 `spec.md` 第 10.16.1 节。

### 9.4 新增 AJAX 外键

`PostView.ajax_refs` 展示作者外键查询；关联关系与 Admin 视图必须存在。实际取值见 `views/post_view.py`，字段和路由语义见 `spec.md` 第 10.10 节。

### 9.5 新增自定义列表模板

demo 模板扩展见第 5.6 节；通用 API 见 `spec.md` 第 10.14.2 节。

### 9.6 新增上传字段

`FileField.save_path` 必须指向已存在的目录。`file_op.py` 当前未接入路由；上传示例仅适用于本地演示，生产环境应使用受控存储。

### 9.7 新增 CLI 命令（可选）

demo 目前没有自定义 CLI。若新增，在 `make_app.py` 的 `init_app(app)` 中注册；会调用 `build_sample_db()` 的命令具有破坏性，只能用于可丢弃的本地数据库，遵循第 0.4 节。

## 10. 常见问题

| 现象 | 原因 | 处理 |
| --- | --- | --- |
| `ModuleNotFoundError: flask_exts` | 没有安装项目 | `python -m pip install -e .` |
| `attempted relative import with no known parent package` | 在错误目录/用错误模块名启动 | 按第 0.2 节选择与执行目录匹配的启动模块名 |
| `sqlite3.OperationalError: no such column: author.cdate` | `demo.sqlite` 是旧 schema，文件存在但模型已变 | 先按第 7.2 节确认触发条件；仅可丢弃的本地库按第 0.4 节重置 |
| 访问 `/admin/author/` 403 | 未登录或用户没有 `admin` 角色 | 使用第 0.2 节的本地演示账号；确认其有 `admin` 角色。`/admin/` 门户可匿名访问 |
| 登录后仍回到登录页 | 用户不存在/密码错误/角色缺失 | 确认 `build_user_admin()` 执行；需重置时按第 0.4 节处理可丢弃的本地 demo 数据库 |
| 端口 5000 被占用 | 其他服务占用 | 改用未占用端口，命令示例见第 0.3 节 |
| 注册后没有收到邮件 | demo 未配置 `NOREPLY_EMAIL_SENDER` | 预期行为与配置边界见第 8.3 节 |
| 配置 `config.py` 不生效 | 配置文件不在 Flask instance 目录 | 路径确认方法见第 8.2 节 |
| `RuntimeError: Exts extension already initialized` | 同一进程重复初始化同一 app/多个 app | 每个进程只创建一个 app；多 app 先 `dispose()` |
| `ValueError: View with name ... already exists` | 视图名重复 | 修改 `name=` 或检查重复注册 |
| 列表页空/字段缺失 | 模型/视图配置不一致 | 检查 `column_list`、模型导入、是否重建数据库 |
| 导出 500 | `export_types` 需要 tablib 支持 | 使用 `csv` 或确认已安装 tablib |
| `demo.sqlite` 出现在 `git status` | 被其他规则覆盖或手动 add | 确认 `.gitignore` 的 `*.sqlite`；不要提交 |

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
- [ ] `/admin/author/` 未登录默认返回 403；仅该视图显式使用 `@login_required` 时检查 302
- [ ] `admin/admin` 能登录
- [ ] 登录后 `/admin/author/` 列表可打开（无 `no such column`）
- [ ] `/admin/post/` 列表、关联列、筛选可用
- [ ] `/admin/tag/` 列表可打开
- [ ] `/admin/tree/` 使用自定义模板，`foo` 显示为 `bar`
- [ ] Author 编辑页 Inline 能新增/编辑/删除 Post
- [ ] Post 列表能按作者、日期排序，能按标题/作者搜索
- [ ] CSV 导出可用；XLS 在安装 `tablib[xls]` 后可用
- [ ] `Post` 的 AJAX 作者外键能搜索并保存
- [ ] 修改/新增模型后，按第 0.4 节重建可丢弃的本地 demo 数据库并验证可用

### 11.3 冒烟测试片段（可选）

在仓库根目录执行：

```python
from examples.demo import create_app

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
print("demo smoke ok")
```

> 该片段会读取现有 `demo.sqlite`；若 schema 过期，仅对可丢弃的本地 demo 数据库按第 0.4 节重置。CSRF 关闭仅用于脚本冒烟，不要用于生产配置。

### 11.4 提交前

- [ ] `git status` 中没有 `demo.sqlite`、上传文件、日志、密钥
- [ ] 对外启动命令与第 0.2 节所指的权威说明一致
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
| 模型 | `models/{name}.py`，并在 `models/__init__.py` 导入 |
| Admin 视图 | `views/{name}_view.py` |
| 视图注册 | `admin_views.py` |
| 种子数据 | `build_sample.py` |
| 模板 | `templates/{name}.html` |
| 静态文件 | `static/`（仅本地演示） |
| 应用配置 | `make_app.py` 或 instance 配置 |

## 13. 与主文档、测试文档的关系

本文只维护 demo 的组织、运行与扩展说明。跨文档职责按 `README.md` 第 3、5、6 节；新增功能按契约、测试、安全文档及适用的工作流执行。启动命令来源与同步规则见第 0.2 节。
