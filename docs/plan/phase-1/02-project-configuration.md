# 02. Python 项目配置

## 设计目标

配置 Python 项目依赖和构建系统，支持可重复的開發环境和生产部署。

## 文件清单

| 文件 | 说明 |
|------|------|
| `pyproject.toml` | Python 项目配置（PEP 518） |
| `requirements.txt` | 运行时依赖 |
| `requirements-dev.txt` | 开发依赖 |
| `.python-version` | Python 版本锁定 |

## pyproject.toml

```toml
[build-system]
requires = ["setuptools>=61.0", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "price-attachment-generator"
version = "0.1.0"
description = "价格附件生成系统 - 根据 Oracle 数据和模板规则生成 Word 价格附件"
readme = "README.md"
license = {text = "Proprietary"}
requires-python = ">=3.10"
authors = [
    {name = "Development Team", email = "dev@example.com"}
]
classifiers = [
    "Development Status :: 3 - Alpha",
    "Intended Audience :: Developers",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.10",
    "Programming Language :: Python :: 3.11",
]

dependencies = [
    "fastapi>=0.100.0",
    "uvicorn[standard]>=0.23.0",
    "python-oracledb>=1.4.0",
    "sqlalchemy>=2.0.0",
    "python-docx>=0.8.11",
    "openpyxl>=3.1.0",
    "pydantic>=2.0.0",
    "pydantic-settings>=2.0.0",
    "python-multipart>=0.0.6",
    "aiofiles>=23.0.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.4.0",
    "pytest-asyncio>=0.21.0",
    "pytest-cov>=4.1.0",
    "httpx>=0.24.0",
    "black>=23.0.0",
    "isort>=5.12.0",
    "mypy>=1.4.0",
    "ruff>=0.1.0",
]

[project.urls]
Homepage = "https://internal.example.com/price-attachment-generator"

[tool.setuptools.packages.find]
where = ["src"]

[tool.setuptools.package-dir]
"" = "src"

# Black 配置
[tool.black]
line-length = 100
target-version = ["py310", "py311"]
include = '\.pyi?$'

# isort 配置
[tool.isort]
profile = "black"
line_length = 100
multi_line_output = 3
include_trailing_comma = true

# pytest 配置
[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = "test_*.py"
python_functions = "test_*"
asyncio_mode = "auto"
addopts = "-v --cov=src --cov-report=html --cov-report=term-missing"

# mypy 配置
[tool.mypy]
python_version = "3.10"
warn_return_any = true
warn_unused_ignores = true
disallow_untyped_defs = true
strict_optional = true

# ruff 配置
[tool.ruff]
line-length = 100
target-version = "py310"
select = ["E", "F", "W", "I", "N", "UP", "B", "C4"]
```

## requirements.txt

```txt
# 运行时依赖 - 生产环境
fastapi==0.104.1
uvicorn[standard]==0.24.0
python-oracledb==2.0.0
sqlalchemy==2.0.23
python-docx==1.1.0
openpyxl==3.1.2
pydantic==2.5.2
pydantic-settings==2.1.0
python-multipart==0.0.6
aiofiles==23.2.1
```

## requirements-dev.txt

```txt
# 开发依赖
-r requirements.txt

# 测试
pytest==7.4.3
pytest-asyncio==0.21.1
pytest-cov==4.1.0
httpx==0.25.2

# 代码质量
black==23.11.0
isort==5.12.0
mypy==1.7.1
ruff==0.1.6

# 调试
ipython==8.18.1
pdbpp==0.10.3
```

## .python-version

```
3.10
```

## 安装说明

### 开发环境安装

```bash
# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # macOS/Linux
# or
.\venv\Scripts\activate  # Windows

# 安装开发依赖
pip install -r requirements-dev.txt

# 或者使用 pyproject.toml
pip install -e ".[dev]"
```

### 生产环境安装

```bash
# 仅安装运行时依赖
pip install -r requirements.txt
```

### 验证安装

```bash
# 运行测试
pytest

# 类型检查
mypy src/

# 代码格式检查
black --check src/
isort --check src/
```

## 验收标准

- [ ] `pyproject.toml` 配置正确
- [ ] 依赖版本锁定
- [ ] 虚拟环境可正常创建
- [ ] 所有依赖可正常安装
- [ ] pytest 可正常运行测试

---

*文档版本：1.0*
*创建日期：2026-03-06*
