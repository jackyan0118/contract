# 06. 配置文件模板

## 设计目标

提供完整的配置文件模板，支持快速部署和环境配置，确保配置项完整且易于理解。

## 文件清单

| 文件 | 说明 | 位置 |
|------|------|------|
| `settings.yaml.example` | 应用配置模板 | `config/` |
| `.env.example` | 环境变量模板 | 项目根目录 |
| `.gitignore` | Git 忽略配置 | 项目根目录 |

## config/settings.yaml.example

```yaml
# 价格附件生成系统 - 配置文件示例
# 复制此文件为 settings.yaml 并根据实际环境修改

# 应用配置
app:
  name: "价格附件生成系统"
  debug: false
  version: "0.1.0"
  host: "0.0.0.0"
  port: 8000

# 数据库配置
database:
  # Oracle 连接字符串格式：oracle://user:password@host:1521/service_name
  dsn: "oracle://user:password@localhost:1521/ORCL"
  # Oracle Schema/用户，用于查询表时指定前缀（如 "KHB_USER"）
  schema: ""
  min_connections: 2
  max_connections: 10
  pool_increment: 1
  connect_timeout: 30
  command_timeout: 60

# 日志配置
logging:
  level: "INFO"  # DEBUG, INFO, WARNING, ERROR, CRITICAL
  format_console: "[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s"
  format_file: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
  file_path: "logs/app.log"
  max_bytes: 10485760  # 10MB
  backup_count: 5

# 模板配置
template:
  path: "templates"
  rule_file: "价格模板规则 - 更新 2026306.xlsx"
  output_dir: "output"
  max_file_size: 10485760  # 10MB
```

## .env.example

```bash
# 价格附件生成系统 - 环境变量配置
# 复制此文件为 .env 并根据实际环境修改

# ==================== 应用配置 ====================
APP_NAME=价格附件生成系统
APP_DEBUG=false
APP_VERSION=0.1.0
APP_HOST=0.0.0.0
APP_PORT=8000

# ==================== 数据库配置 ====================
# Oracle 连接字符串
# 格式：oracle://user:password@host:1521/service_name
DB_DSN=oracle://user:password@localhost:1521/ORCL
# Oracle Schema/用户，用于查询表时指定前缀（如 "KHB_USER"）
DB_SCHEMA=

# 连接池配置
DB_MIN_CONNECTIONS=2
DB_MAX_CONNECTIONS=10
DB_POOL_INCREMENT=1
DB_CONNECT_TIMEOUT=30
DB_COMMAND_TIMEOUT=60

# ==================== 日志配置 ====================
LOG_LEVEL=INFO
LOG_FORMAT_CONSOLE=[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s
LOG_FORMAT_FILE=%(asctime)s - %(name)s - %(levelname)s - %(message)s
LOG_FILE_PATH=logs/app.log
LOG_MAX_BYTES=10485760
LOG_BACKUP_COUNT=5

# ==================== 模板配置 ====================
TEMPLATE_PATH=templates
TEMPLATE_RULE_FILE=价格模板规则 - 更新 2026306.xlsx
TEMPLATE_OUTPUT_DIR=output
TEMPLATE_MAX_FILE_SIZE=10485760
```

## .gitignore

```gitignore
# ==================== Python ====================
# Byte-compiled / optimized / DLL files
__pycache__/
*.py[cod]
*$py.class

# C extensions
*.so

# Distribution / packaging
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
pip-wheel-metadata/
share/python-wheels/
*.egg-info/
.installed.cfg
*.egg
MANIFEST

# PyInstaller
*.manifest
*.spec

# Installer logs
pip-log.txt
pip-delete-this-directory.txt

# Unit test / coverage reports
htmlcov/
.tox/
.nox/
.coverage
.coverage.*
.cache
nosetests.xml
coverage.xml
*.cover
*.py,cover
.hypothesis/
.pytest_cache/

# Translations
*.mo
*.pot

# Django stuff:
*.log
local_settings.py
db.sqlite3
db.sqlite3-journal

# Flask stuff:
instance/
.webassets-cache

# Scrapy stuff:
.scrapy

# Sphinx documentation
docs/_build/

# PyBuilder
target/

# Jupyter Notebook
.ipynb_checkpoints

# IPython
profile_default/
ipython_config.py

# pyenv
.python-version

# pipenv
Pipfile.lock

# PEP 582
__pypackages__/

# Celery stuff
celerybeat-schedule
celerybeat.pid

# SageMath parsed files
*.sage.py

# Environments
.env
.venv
env/
venv/
ENV/
env.bak/
venv.bak/

# Spyder project settings
.spyderproject
.spyproject

# Rope project settings
.ropeproject

# mkdocs documentation
/site

# mypy
.mypy_cache/
.dmypy.json
dmypy.json

# Pyre type checker
.pyre/

# pytype static type analyzer
.pytype/

# Cython debug symbols
cython_debug/

# ==================== IDE ====================
# JetBrains IDEs
.idea/
*.iml
*.ipr
*.iws

# VS Code
.vscode/
*.code-workspace

# Emacs
*~
\#*\#

# Vim
*.swp
*.swo
*~

# ==================== OS ====================
# macOS
.DS_Store
.AppleDouble
.LSOverride
._*

# Windows
Thumbs.db
ehthumbs.db
Desktop.ini
$RECYCLE.BIN/

# ==================== Project Specific ====================
# Logs
logs/
*.log

# Output files
output/
*.docx

# Database
*.db

# Configuration (keep examples, ignore actual configs)
config/settings.yaml
!config/settings.yaml.example

# Secrets
*.key
*.pem
!*.pem.example

# Temporary files
tmp/
temp/
*.tmp
```

## 配置项说明

### 应用配置

| 配置项 | 必填 | 默认值 | 说明 | 示例 |
|--------|------|--------|------|------|
| `app.name` | 否 | "价格附件生成系统" | 应用名称 | 价格附件生成系统 |
| `app.debug` | 否 | false | 调试模式 | true/false |
| `app.version` | 否 | "0.1.0" | 版本号 | 0.1.0 |
| `app.host` | 否 | "0.0.0.0" | 监听地址 | 0.0.0.0 |
| `app.port` | 否 | 8000 | 监听端口 | 8000 |

### 数据库配置

| 配置项 | 必填 | 默认值 | 说明 | 示例 |
|--------|------|--------|------|------|
| `database.dsn` | 是 | - | Oracle 连接字符串 | oracle://user:pass@host:1521/ORCL |
| `database.min_connections` | 否 | 2 | 最小连接数 | 2 |
| `database.max_connections` | 否 | 10 | 最大连接数 | 10 |
| `database.pool_increment` | 否 | 1 | 连接池增量 | 1 |
| `database.connect_timeout` | 否 | 30 | 连接超时 (秒) | 30 |
| `database.command_timeout` | 否 | 60 | 命令超时 (秒) | 60 |

### 日志配置

| 配置项 | 必填 | 默认值 | 说明 | 示例 |
|--------|------|--------|------|------|
| `logging.level` | 否 | "INFO" | 日志级别 | INFO |
| `logging.format_console` | 否 | - | 控制台格式 | [%(asctime)s]... |
| `logging.format_file` | 否 | - | 文件格式 | %(asctime)s... |
| `logging.file_path` | 否 | "logs/app.log" | 日志文件路径 | logs/app.log |
| `logging.max_bytes` | 否 | 10485760 | 单文件最大大小 | 10485760 |
| `logging.backup_count` | 否 | 5 | 备份文件数 | 5 |

### 模板配置

| 配置项 | 必填 | 默认值 | 说明 | 示例 |
|--------|------|--------|------|------|
| `template.path` | 否 | "templates" | 模板文件目录 | templates |
| `template.rule_file` | 否 | - | 规则 Excel 文件名 | 价格模板规则 - 更新 2026306.xlsx |
| `template.output_dir` | 否 | "output" | 输出文件目录 | output |
| `template.max_file_size` | 否 | 10485760 | 最大文件大小 | 10485760 |

## 环境配置示例

### 开发环境 (.env.development)

```bash
APP_DEBUG=true
APP_PORT=8000
LOG_LEVEL=DEBUG
DB_DSN=oracle://dev_user:dev_pass@dev-db:1521/DEVDB
DB_SCHEMA=DEV_USER
```

### 测试环境 (.env.test)

```bash
APP_DEBUG=false
APP_PORT=8000
LOG_LEVEL=INFO
DB_DSN=oracle://test_user:test_pass@test-db:1521/TESTDB
DB_SCHEMA=TEST_USER
```

### 生产环境 (.env.production)

```bash
APP_DEBUG=false
APP_PORT=8000
LOG_LEVEL=WARNING
DB_DSN=oracle://prod_user:prod_pass@prod-db:1521/PRODDB
DB_SCHEMA=PROD_USER
DB_MAX_CONNECTIONS=20
```

## 文件权限设置

为确保配置文件安全，需要设置适当的文件权限。

### Linux/macOS 系统

```bash
# 设置配置文件权限（仅所有者可读写）
chmod 600 config/settings.yaml
chmod 600 .env

# 设置目录权限（所有者可读写执行，组可读执行）
chmod 750 logs/
chmod 750 output/
chmod 750 templates/

# 确保运行时创建目录
mkdir -p logs output templates
```

### Windows 系统

在 Windows 上，使用文件属性设置权限：
1. 右键点击文件 → 属性 → 安全
2. 移除不必要的用户权限
3. 只保留管理员和 SYSTEM 完全控制

### 权限说明

| 文件/目录 | 权限 | 说明 |
|-----------|------|------|
| `config/settings.yaml` | 600 | 仅所有者可读写，防止敏感信息泄露 |
| `.env` | 600 | 仅所有者可读写，包含数据库密码等 |
| `logs/` | 750 | 所有者可读写执行，组可读执行 |
| `output/` | 750 | 所有者可读写执行，组可读执行 |
| `templates/` | 750 | 所有者可读写执行，组可读执行 |

### 注意事项

- **切勿**将包含真实凭证的配置文件提交到版本控制
- 使用 `.env.example` 或 `settings.yaml.example` 作为模板
- 在 `.gitignore` 中确保排除实际配置文件
- 定期检查配置文件权限设置

## 配置加载优先级

配置加载的优先级顺序（从高到低）：

1. 环境变量（直接设置的环境变量）
2. `.env` 文件
3. `config/settings.yaml` 文件
4. 默认值

## 验收标准

- [ ] `settings.yaml.example` 配置完整
- [ ] `.env.example` 配置完整
- [ ] `.gitignore` 配置正确
- [ ] 配置项说明清晰
- [ ] 示例值合理

---

*文档版本：1.0*
*创建日期：2026-03-06*
