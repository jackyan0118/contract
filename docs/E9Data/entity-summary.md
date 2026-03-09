# 泛微E9 实体对象汇总

## 概述

本文档汇总价格附件生成系统涉及的所有泛微E9实体对象，包括浏览按钮对应的实体表。

## 实体对象列表

### 1. UF_CRMKHKP - CRM客户卡片

**用途**: 客户主体、客户终端选择

**字段列表**:

| 字段名 | 数据类型 | 说明 |
|--------|----------|------|
| ID | NUMBER | 主键 |
| REQUESTID | NUMBER | 流程RequestID |
| FORMMODEID | NUMBER | 表单模式ID |
| MODEDATACREATER | NUMBER | 创建人 |
| MODEDATACREATEDATE | VARCHAR2(10) | 创建日期 |
| MODEDATACREATETIME | VARCHAR2(8) | 创建时间 |
| ... | ... | (共39个字段) |

---

### 2. UF_CPZWH - 产品组维护

**用途**: 定价组选择

**字段列表**:

| 字段名 | 数据类型 | 说明 |
|--------|----------|------|
| ID | NUMBER | 主键 |
| REQUESTID | NUMBER | 流程RequestID |
| ZCTPKL | NUMBER(38,2) | 主体投票率 |
| CPZ | VARCHAR2(999) | 产品组 |
| ... | ... | (共20个字段) |

---

### 3. UF_SAPCPLBQD - SAP产品类别清单

**用途**: 特殊价格说明、产品类别选择

**字段列表**:

| 字段名 | 数据类型 | 说明 |
|--------|----------|------|
| ID | NUMBER | 主键 |
| REQUESTID | NUMBER | 流程RequestID |
| CPLBBM | VARCHAR2(10) | 产品类别编码 |
| CPLBMC | VARCHAR2(100) | 产品类别名称 |
| SFZY | NUMBER | 是否主营 |
| ... | ... | (共14个字段) |

---

### 4. UF_CPXF - 产品细分

**用途**: 产品细分选择

**字段列表**:

| 字段名 | 数据类型 | 说明 |
|--------|----------|------|
| ID | NUMBER | 主键 |
| REQUESTID | NUMBER | 流程RequestID |
| BM | VARCHAR2(999) | 编码 |
| CPXF | VARCHAR2(999) | 产品细分 |
| ... | ... | (共18个字段) |

---

### 5. UF_PP - 品牌

**用途**: 品牌选择

**字段列表**:

| 字段名 | 数据类型 | 说明 |
|--------|----------|------|
| ID | NUMBER | 主键 |
| REQUESTID | NUMBER | 流程RequestID |
| DM | VARCHAR2(300) | 代码 |
| MS | VARCHAR2(300) | 描述 |
| ... | ... | (共16个字段) |

---

### 6. UF_JYTC - 检验套餐

**用途**: 检验套餐选择

**字段列表**:

| 字段名 | 数据类型 | 说明 |
|--------|----------|------|
| ID | NUMBER | 主键 |
| REQUESTID | NUMBER | 流程RequestID |
| LB | VARCHAR2(999) | 类别 |
| ... | ... | (共13个字段) |

---

### 7. UF_CPKXMJC - 项目简称

**用途**: 项目简称选择

**字段列表**:

| 字段名 | 数据类型 | 说明 |
|--------|----------|------|
| ID | NUMBER | 主键 |
| REQUESTID | NUMBER | 流程RequestID |
| BH | VARCHAR2(999) | 编号 |
| XMJC | VARCHAR2(999) | 项目简称 |
| SCBXMJC | VARCHAR2(999) | 市场部项目简称 |
| CPMC | VARCHAR2(999) | 产品名称 |
| CX | NUMBER | 车型 |
| ... | ... | (共17个字段) |

---

### 8. WORKFLOW_REQUESTBASE - 流程请求表

**用途**: 流程浏览选择

**字段列表**:

| 字段名 | 数据类型 | 说明 |
|--------|----------|------|
| REQUESTID | NUMBER | 请求ID |
| WORKFLOWID | NUMBER | 流程ID |
| LASTNODEID | NUMBER | 最后节点ID |
| CURRENTNODEID | NUMBER | 当前节点ID |
| STATUS | VARCHAR2(500) | 状态 |
| REQUESTNAME | VARCHAR2(1000) | 请求名称 |
| CREATERTYPE | NUMBER(38,0) | 创建人类型 |
| CREATER | NUMBER(38,0) | 创建人 |
| CREATEDATE | VARCHAR2(10) | 创建日期 |
| CREATETIME | VARCHAR2(8) | 创建时间 |
| ... | ... | (共49个字段) |

---

## 浏览按钮字段映射

| 源字段 | 实体对象 | 说明 |
|--------|----------|------|
| XGLC | WORKFLOW_REQUESTBASE | 相关流程 |
| SJKHZT | UF_CRMKHKP | 设价客户主体 |
| SJKH | UF_CRMKHKP | 设价客户 |
| SJKHZD | UF_CRMKHKP | 设价客户终端 |
| DJZ | UF_CPZWH | 定价组 |
| TSJGSM | UF_SAPCPLBQD | 特殊价格说明 |
| SJSJ | - | 日期（标准浏览按钮） |
| CPXF | UF_CPXF | 产品细分 |
| PP | UF_PP | 品牌 |
| JYTC | UF_JYTC | 检验套餐 |
| XMJC | UF_CPKXMJC | 项目简称 |

---

## 注意事项

1. 所有实体表均位于 ECOLOGY Schema 下
2. 泛微建模表均包含标准字段：ID, REQUESTID, FORMMODEID, MODEDATACREATER, MODEDATACREATEDATE, MODEDATACREATETIME 等
3. 浏览按钮字段存储的是实体表的 ID，显示值通过关联查询获取
