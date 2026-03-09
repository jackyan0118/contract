# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

价格附件生成系统 (Price Attachment Generator) - 基于模板规则自动生成 Word 价格附件的系统。

- **Framework**: FastAPI
- **Python**: 3.10+
- **Database**: Oracle (python-oracledb Thin 模式)
- **Document**: python-docx

## Common Commands

```bash
# Activate virtual environment
source venv/bin/activate  # Linux/macOS
# or
venv\Scripts\activate     # Windows

# Install dependencies
pip install -e ".[dev]"

# Run tests (80% coverage required)
pytest

# Run single test file
pytest tests/unit/test_config.py

# Run with coverage report
pytest --cov=src --cov-report=html --cov-report=term-missing

# Code formatting
black .
isort .

# Linting
ruff check .

# Type checking
mypy src

# Run development server
uvicorn src.main:app --reload
```

## Architecture

```
src/
├── api/               # FastAPI routes and middleware
│   ├── routes/        # API endpoints
│   └── middleware/    # Error handling, CORS, etc.
├── database/          # Oracle connection pool and queries
├── models/           # Pydantic data models
├── queries/          # SQL query definitions
├── transformers/     # Data transformation logic
├── parsers/          # Input parsing (Excel, etc.)
├── matchers/         # Template matching engine
├── readers/          # File readers (docx, xlsx)
├── fillers/          # Document field filling
├── generators/       # Word document generation
├── services/         # Business logic services
├── config/           # Configuration management (YAML + env)
├── utils/            # Logging, helpers
└── exceptions/       # Custom exception hierarchy
```

### Core Workflow

1. Receive `wybs` (报价单号/quote number)
2. Query Oracle database for quote data
3. Match templates based on product category, pricing group, etc.
4. Generate Word documents from matched templates
5. Return file(s) - single or ZIP bundle

### Database

- **Driver**: python-oracledb (Thin mode, no Oracle client needed)
- **Pool**: oracledb create_pool() for connection management
- **Tables**: Quote main table + `uf_htjgkst_dt1` (quote details)

### 泛微字段规则

- **选择框(是否)**：0 = 是，1 = 否，空值 = 否
  - 例如：`是否集采`字段：0=集采，1=非集采
  - 查询时使用：`NVL(字段, 1) = 0` 表示"是"

### Templates

- 35+ Word templates in `docs/template/`
- Rules defined in `docs/template/价格模板规则-更新2026306.xlsx`
- Matching criteria: product category, pricing group, centralized procurement flag, supply price type

## Testing Requirements

- Minimum **80% coverage** required
- Test markers: `@pytest.mark.unit`, `@pytest.mark.integration`, `@pytest.mark.e2e`, `@pytest.mark.slow`
- Async tests supported via `pytest-asyncio`

## Exception Hierarchy

```
AppException
├── ConfigException
├── DatabaseException
│   ├── ConnectionException
│   └── QueryException
├── TemplateException
│   ├── MatchException
│   └── GenerateException
└── APIException
    ├── ValidationError
    └── NotFoundException
```

## Configuration

- YAML config in `config/settings.yaml`
- Environment variables override YAML values
- See `config/settings.yaml.example` for template
