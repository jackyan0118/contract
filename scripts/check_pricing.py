#!/usr/bin/env python3
"""核对 Excel 定价组与数据库定价组."""

import os
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
os.chdir(project_root)

import oracledb
import pandas as pd

# 初始化 Oracle
oracledb.init_oracle_client(lib_dir='/opt/oracle/instantclient')

oracledb.init_oracle_client(lib_dir='/opt/oracle/instantclient')
from src.database.config import get_database_config

db_config = get_database_config()
params = db_config.to_oracledb_params()

# 读取 Excel
excel_file = 'docs/template/价格模板规则-更新2026306.xlsx'
df = pd.read_excel(excel_file, sheet_name='模板类型', header=1)
df_valid = df[df['模板'].notna()].copy()

# 从 Excel 提取定价组
excel_pricing = {}
for _, row in df_valid.iterrows():
    code = row['定价组']
    name = row['Unnamed: 5']
    if pd.notna(code) and pd.notna(name):
        excel_pricing[int(code)] = name

print('=== Excel 定价组 ({}个) ==='.format(len(excel_pricing)))
for code, name in sorted(excel_pricing.items()):
    print(f'{code}: {name}')

# 从数据库查询
conn = oracledb.connect(user=params['user'], password=params['password'], dsn=params['dsn'])
cursor = conn.cursor()
cursor.execute('SELECT CPZBH, CPZ FROM ECOLOGY.UF_CPZWH WHERE CPZBH IS NOT NULL')
db_pricing = {}
for row in cursor.fetchall():
    code, name = row
    try:
        code = int(code)
        db_pricing[code] = name
    except:
        pass
cursor.close()
conn.close()

print()
print('=== 核对结果 ===')
for code, excel_name in sorted(excel_pricing.items()):
    db_name = db_pricing.get(code)
    if db_name:
        match = 'OK' if excel_name == db_name else 'DIFF'
        print(f'{code}: Excel="{excel_name}"')
        print(f'     DB="{db_name}" [{match}]')
    else:
        print(f'{code}: Excel="{excel_name}" -> DB NOT FOUND')
