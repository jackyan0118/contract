# UF_HTJGKST 数据字典

## 表基本信息

| 属性 | 值 |
|------|-----|
| 表名 | UF_HTJGKST |
| 描述 |  |
| 所属Schema | ECOLOGY |
| 表空间 | ECOLOGY |

## 字段列表

| 序号 | 字段名 | 数据类型 | 可空 | 字段类型 | 实体对象 | 说明 |
|------|--------|----------|------|----------|----------|------|
| 1 | ID | NUMBER | NO | 系统字段 |  | 主键 |
| 2 | REQUESTID | NUMBER | YES | 系统字段 |  | 流程RequestID |
| 3 | FORMMODEID | NUMBER | YES | 系统字段 |  | 表单模式ID |
| 4 | MODEDATACREATER | NUMBER | YES | 数字 |  | 创建人 |
| 5 | MODEDATACREATERTYPE | NUMBER | YES | 数字 |  | 创建人类型 |
| 6 | MODEDATACREATEDATE | VARCHAR2(10) | YES | 单行文本 |  | 创建日期 |
| 7 | MODEDATACREATETIME | VARCHAR2(8) | YES | 单行文本 |  | 创建时间 |
| 8 | MODEUUID | VARCHAR2(100) | YES | 单行文本 |  | 模式UUID |
| 9 | FORM_BIZ_ID | VARCHAR2(100) | YES | 单行文本 |  | 表单业务ID |
| 10 | LCBH | VARCHAR2(999) | YES | 单行文本 |  | 流程编号 |
| 11 | HTBH | VARCHAR2(999) | YES | 单行文本 |  | 合同编号 |
| 12 | XGLC | NUMBER | YES | 浏览按钮 | workflow_requestbase | 相关流程 |
| 13 | WYBS | VARCHAR2(999) | YES | 单行文本 |  | 唯一标识 |
| 14 | MODEDATAMODIFIER | NUMBER | YES | 数字 |  | 修改人 |
| 15 | MODEDATAMODIFYDATETIME | VARCHAR2(100) | YES | 单行文本 |  | 修改时间 |

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
