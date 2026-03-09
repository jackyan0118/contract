# UF_SAPCPLBQD 数据字典

## 表基本信息

| 属性 | 值 |
|------|-----|
| 表名 | UF_SAPCPLBQD |
| 描述 |  |
| 所属Schema | ECOLOGY |
| 表空间 | ECOLOGY |

## 字段列表

| 序号 | 字段名 | 数据类型 | 可空 | 字段类型 | 实体对象 | 说明 |
|------|--------|----------|------|----------|----------|------|
| 1 | ID | NUMBER | NO | 系统字段 |  | 主键 |
| 2 | REQUESTID | NUMBER | YES | 系统字段 |  | 流程RequestID |
| 3 | CPLBBM | VARCHAR2(10) | YES | 单行文本 |  | 产品类别编码 |
| 4 | CPLBMC | VARCHAR2(100) | YES | 单行文本 |  | 产品类别名称 |
| 5 | SFZY | NUMBER | YES | 选择框 |  | 是否在用 |
| 6 | FORMMODEID | NUMBER | YES | 系统字段 |  | 表单模式ID |
| 7 | MODEDATACREATER | NUMBER | YES | 数字 |  | 创建人 |
| 8 | MODEDATACREATERTYPE | NUMBER | YES | 数字 |  | 创建人类型 |
| 9 | MODEDATACREATEDATE | VARCHAR2(10) | YES | 单行文本 |  | 创建日期 |
| 10 | MODEDATACREATETIME | VARCHAR2(8) | YES | 单行文本 |  | 创建时间 |
| 11 | MODEDATAMODIFIER | NUMBER | YES | 数字 |  | 修改人 |
| 12 | MODEDATAMODIFYDATETIME | VARCHAR2(100) | YES | 单行文本 |  | 修改时间 |
| 13 | FORM_BIZ_ID | VARCHAR2(100) | YES | 单行文本 |  | 表单业务ID |
| 14 | MODEUUID | VARCHAR2(100) | YES | 单行文本 |  | 模式UUID |

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
