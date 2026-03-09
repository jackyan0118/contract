# UF_YXZXHTGHJLXBN 数据字典

## 表基本信息

| 属性 | 值 |
|------|-----|
| 表名 | UF_YXZXHTGHJLXBN |
| 描述 |  |
| 所属Schema | ECOLOGY |
| 表空间 | ECOLOGY |

## 字段列表

| 序号 | 字段名 | 数据类型 | 可空 | 字段类型 | 实体对象 | 说明 |
|------|--------|----------|------|----------|----------|------|
| 1 | ID | NUMBER | NO | 系统字段 |  | 主键 |
| 2 | REQUESTID | NUMBER | YES | 系统字段 |  | 流程RequestID |
| 3 | CPZ | NUMBER | YES | 选择框 |  | 定价组 |
| 4 | FORMMODEID | NUMBER | YES | 系统字段 |  | 表单模式ID |
| 5 | MODEDATACREATER | NUMBER | YES | 数字 |  | 创建人 |
| 6 | MODEDATACREATERTYPE | NUMBER | YES | 数字 |  | 创建人类型 |
| 7 | MODEDATACREATEDATE | VARCHAR2(80) | YES | 单行文本 |  | 创建日期 |
| 8 | MODEDATACREATETIME | VARCHAR2(64) | YES | 单行文本 |  | 创建时间 |
| 9 | MODEUUID | VARCHAR2(800) | YES | 单行文本 |  | 模式UUID |
| 10 | GHJLXID | NUMBER | YES | 单行文本 |  | 供货价类型值 |
| 11 | GHJLX | VARCHAR2(800) | YES | 单行文本 |  | 供货价类型 |
| 12 | SJD1 | NUMBER | YES | 单行文本 |  | 类型数据ID |
| 13 | SFQY | NUMBER | YES | 选择框 |  | 是否启用 |
| 14 | MODEDATAMODIFIER | NUMBER | YES | 数字 |  | 修改人 |
| 15 | MODEDATAMODIFYDATETIME | VARCHAR2(100) | YES | 单行文本 |  | 修改时间 |
| 16 | CPZAN | VARCHAR2(1000) | YES | 浏览按钮 | UF_CPZWH | 定价组(按钮) |
| 17 | SFBTKL | NUMBER | YES | 选择框 |  | 是否必填扣率 |
| 18 | KL | NUMBER(38,2) | YES | 单行文本 |  | 扣率 |
| 19 | SFJCGHJLX | NUMBER | YES | 选择框 |  | 是否集采供货价类型 |

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
