# WORKFLOW_REQUESTBASE 数据字典

## 表基本信息

| 属性 | 值 |
|------|-----|
| 表名 | WORKFLOW_REQUESTBASE |
| 描述 |  |
| 所属Schema | ECOLOGY |
| 表空间 | ECOLOGY |

## 字段列表

| 序号 | 字段名 | 数据类型 | 可空 | 字段类型 | 实体对象 | 说明 |
|------|--------|----------|------|----------|----------|------|
| 1 | REQUESTID | NUMBER | NO | 系统字段 |  | 流程RequestID |
| 2 | WORKFLOWID | NUMBER | YES | 数字 |  | 流程定义ID |
| 3 | LASTNODEID | NUMBER | YES | 数字 |  | 最后节点ID |
| 4 | LASTNODETYPE | CHAR(1) | YES | 单行文本 |  | 最后节点类型 |
| 5 | CURRENTNODEID | NUMBER | YES | 数字 |  | 当前节点ID |
| 6 | CURRENTNODETYPE | CHAR(1) | YES | 单行文本 |  | 当前节点类型 |
| 7 | STATUS | VARCHAR2(500) | YES | 单行文本 |  | 流程状态 |
| 8 | PASSEDGROUPS | NUMBER | YES | 数字 |  | 已通过节点数 |
| 9 | TOTALGROUPS | NUMBER | YES | 数字 |  | 总节点数 |
| 10 | REQUESTNAME | VARCHAR2(1000) | YES | 单行文本 |  | 请求名称 |
| 11 | CREATER | NUMBER | YES | 数字 |  | 创建人 |
| 12 | CREATEDATE | CHAR(10) | YES | 单行文本 |  | 创建日期 |
| 13 | CREATETIME | CHAR(8) | YES | 单行文本 |  | 创建时间 |
| 14 | LASTOPERATOR | NUMBER | YES | 数字 |  | 最后操作人 |
| 15 | LASTOPERATEDATE | CHAR(10) | YES | 单行文本 |  | 最后操作日期 |
| 16 | LASTOPERATETIME | CHAR(8) | YES | 单行文本 |  | 最后操作时间 |
| 17 | DELETED | NUMBER | YES | 数字 |  | None |
| 18 | CREATERTYPE | NUMBER | YES | 数字 |  | None |
| 19 | LASTOPERATORTYPE | NUMBER | YES | 数字 |  | None |
| 20 | NODEPASSTIME | FLOAT(126) | YES |  |  | None |
| 21 | NODELEFTTIME | FLOAT(126) | YES |  |  | None |
| 22 | DOCIDS | VARCHAR2(4000) | YES | 单行文本 |  | None |
| 23 | CRMIDS | VARCHAR2(4000) | YES | 单行文本 |  | None |
| 24 | HRMIDS_TEMP | VARCHAR2(4000) | YES | 单行文本 |  | None |
| 25 | PRJIDS | VARCHAR2(4000) | YES | 单行文本 |  | None |
| 26 | CPTIDS | VARCHAR2(4000) | YES | 单行文本 |  | None |
| 27 | REQUESTLEVEL | NUMBER | YES | 数字 |  | None |
| 28 | REQUESTMARK | VARCHAR2(800) | YES | 单行文本 |  | None |
| 29 | MESSAGETYPE | NUMBER | YES | 数字 |  | None |
| 30 | MAINREQUESTID | NUMBER | YES | 数字 |  | None |
| 31 | CURRENTSTATUS | NUMBER | YES | 数字 |  | None |
| 32 | LASTSTATUS | VARCHAR2(480) | YES | 单行文本 |  | None |
| 33 | ISMULTIPRINT | NUMBER | YES | 数字 |  | None |
| 34 | CHATSTYPE | NUMBER | YES | 数字 |  | None |
| 35 | ECOLOGY_PINYIN_SEARCH | VARCHAR2(1000) | YES | 单行文本 |  | None |
| 36 | HRMIDS | CLOB | YES |  |  | None |
| 37 | REQUESTNAMENEW | VARCHAR2(4000) | YES | 单行文本 |  | None |
| 38 | FORMSIGNATUREMD5 | VARCHAR2(1000) | YES | 单行文本 |  | None |
| 39 | DATAAGGREGATED | CHAR(1) | YES | 单行文本 |  | None |
| 40 | SECLEVEL | CHAR(1) | YES | 单行文本 |  | None |
| 41 | SECDOCID | VARCHAR2(500) | YES | 单行文本 |  | None |
| 42 | REMINDTYPES | VARCHAR2(40) | YES | 单行文本 |  | None |
| 43 | LASTFEEDBACKDATE | CHAR(10) | YES | 单行文本 |  | None |
| 44 | LASTFEEDBACKTIME | CHAR(8) | YES | 单行文本 |  | None |
| 45 | LASTFEEDBACKOPERATOR | NUMBER | YES | 数字 |  | None |
| 46 | REQUESTNAMEHTMLNEW | VARCHAR2(4000) | YES | 单行文本 |  | None |
| 47 | SECVALIDITY | VARCHAR2(50) | YES | 单行文本 |  | None |
| 48 | SECENCKEY | VARCHAR2(200) | YES | 单行文本 |  | None |
| 49 | SECCRC | VARCHAR2(100) | YES | 单行文本 |  | None |

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
