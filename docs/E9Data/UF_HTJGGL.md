# UF_HTJGGL 数据字典

## 表基本信息

| 属性 | 值 |
|------|-----|
| 表名 | UF_HTJGGL |
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
| 10 | JGMS | VARCHAR2(999) | YES | 单行文本 |  | 价格描述 |
| 11 | HTJSRQ | CHAR(10) | YES | 浏览按钮 | 日期 | 合同结束日期 |
| 12 | JGQDBH | VARCHAR2(999) | YES | 单行文本 |  | 价格清单编号 |
| 13 | SJJD | NUMBER | YES | 选择框 |  | 设价节点 |
| 14 | SJSJ | CHAR(10) | YES | 浏览按钮 | 日期 | 设价时间 |
| 15 | SFTQSJ | NUMBER | YES | 选择框 |  | 是否提前设价 |
| 16 | HTKSRQ | CHAR(10) | YES | 浏览按钮 | 日期 | 合同开始日期 |
| 17 | SJID | VARCHAR2(999) | YES | 单行文本 |  | 数据ID |
| 18 | HTBH | VARCHAR2(999) | YES | 单行文本 |  | 合同编号 |
| 19 | LCBH | VARCHAR2(999) | YES | 单行文本 |  | 流程编号 |
| 20 | SJLX | NUMBER | YES | 选择框 |  | 设价类型 |
| 21 | SYB | VARCHAR2(1000) | YES | 浏览按钮 | UF_CRMSYB | 事业部 |
| 22 | SJKHZT | VARCHAR2(1000) | YES | 浏览按钮 | UF_CRMKHKP | 设价客户主体 |
| 23 | SJKHZD | VARCHAR2(1000) | YES | 浏览按钮 | UF_CRMKHKP | 设价客户终端 |
| 24 | JGGXBJ | NUMBER | YES | 选择框 |  | 价格更新标记 |
| 25 | YWCX | NUMBER | YES | 选择框 |  | 业务产线 |
| 26 | BKHTXNJG | VARCHAR2(999) | YES | 单行文本 |  | 本客户（体系内）价格， |
| 27 | HTDL | NUMBER | YES | 选择框 |  | 合同大类 |
| 28 | MXBTXKH | VARCHAR2(999) | YES | 单行文本 |  | 明细表填写客户， |
| 29 | MODEDATAMODIFIER | NUMBER | YES | 数字 |  | 修改人 |
| 30 | MODEDATAMODIFYDATETIME | VARCHAR2(100) | YES | 单行文本 |  | 修改时间 |
| 31 | LCID | NUMBER | YES | 浏览按钮 | workflow_requestbase | 流程ID |
| 32 | HTLCID | NUMBER | YES | 浏览按钮 | workflow_requestbase | 合同流程ID |
| 33 | HTJGFJLJ | VARCHAR2(999) | YES | 单行文本 |  | 合同价格附件链接 |
| 34 | HTJGFJ | VARCHAR2(4000) | YES | 附件上传 |  | 合同价格附件 |

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
