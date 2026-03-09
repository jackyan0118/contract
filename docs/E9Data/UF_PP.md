# UF_PP 数据字典

## 表基本信息

| 属性 | 值 |
|------|-----|
| 表名 | UF_PP |
| 描述 |  |
| 所属Schema | ECOLOGY |
| 表空间 | ECOLOGY |

## 字段列表

| 序号 | 字段名 | 数据类型 | 可空 | 字段类型 | 实体对象 | 说明 |
|------|--------|----------|------|----------|----------|------|
| 1 | ID | NUMBER | NO | 系统字段 |  | 主键 |
| 2 | REQUESTID | NUMBER | YES | 系统字段 |  | 流程RequestID |
| 3 | DM | VARCHAR2(300) | YES | 单行文本 |  | 代码 |
| 4 | MS | VARCHAR2(300) | YES | 单行文本 |  | 描述 |
| 5 | FORMMODEID | NUMBER | YES | 系统字段 |  | 表单模式ID |
| 6 | MODEDATACREATER | NUMBER | YES | 数字 |  | 创建人 |
| 7 | MODEDATACREATERTYPE | NUMBER | YES | 数字 |  | 创建人类型 |
| 8 | MODEDATACREATEDATE | VARCHAR2(10) | YES | 单行文本 |  | 创建日期 |
| 9 | MODEDATACREATETIME | VARCHAR2(8) | YES | 单行文本 |  | 创建时间 |
| 10 | MODEDATAMODIFIER | NUMBER | YES | 数字 |  | 修改人 |
| 11 | MODEDATAMODIFYDATETIME | VARCHAR2(100) | YES | 单行文本 |  | 修改时间 |
| 12 | FORM_BIZ_ID | VARCHAR2(100) | YES | 单行文本 |  | 表单业务ID |
| 13 | MODEUUID | VARCHAR2(100) | YES | 单行文本 |  | 模式UUID |
| 14 | SFQY | NUMBER | YES | 选择框 |  | 是否启用 |
| 15 | XSM | VARCHAR2(999) | YES | 单行文本 |  | 显示名 |
| 16 | SAPPPDM | VARCHAR2(20) | YES | 单行文本 |  | SAP品牌代码 |

## 字段类型说明

| 类型值 | 说明 |
|--------|------|
| 1 | 单行文本 |
| 2 | 多行文本 |
| 3 | 浏览按钮 |
| 4 | Check框 |
| 5 | 选择框 |
| 6 | 附件上传 |
| 7 | 特殊字段 |
