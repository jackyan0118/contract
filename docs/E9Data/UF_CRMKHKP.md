# UF_CRMKHKP 数据字典

## 表基本信息

| 属性 | 值 |
|------|-----|
| 表名 | UF_CRMKHKP |
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
| 8 | MODEDATAMODIFIER | NUMBER | YES | 数字 |  | 修改人 |
| 9 | MODEDATAMODIFYDATETIME | VARCHAR2(100) | YES | 单行文本 |  | 修改时间 |
| 10 | MODEUUID | VARCHAR2(100) | YES | 单行文本 |  | 模式UUID |
| 11 | KHBH | VARCHAR2(999) | YES | 单行文本 |  | 客户编号 |
| 12 | KHMC | VARCHAR2(999) | YES | 单行文本 |  | 客户名称 |
| 13 | KHZYM | VARCHAR2(999) | YES | 单行文本 |  | 客户曾用名 |
| 14 | ZT | NUMBER | YES | 选择框 |  | 状态 |
| 15 | KHFL | NUMBER | YES | 选择框 |  | 客户分类 |
| 16 | ZCDZ | VARCHAR2(999) | YES | 单行文本 |  | 注册地址 |
| 17 | GJ | VARCHAR2(1000) | YES | 浏览按钮 | UF_CRMGJ | 国家 |
| 18 | SF | VARCHAR2(1000) | YES | 浏览按钮 | UF_CRMSF | 省份 |
| 19 | CS | VARCHAR2(1000) | YES | 浏览按钮 | UF_CRMCS | 城市 |
| 20 | JYDZ | VARCHAR2(999) | YES | 单行文本 |  | 经营地址 |
| 21 | KHLX | NUMBER | YES | 选择框 |  | 客户类型 |
| 22 | YWDY | VARCHAR2(4000) | YES | 浏览按钮 | UF_CRMYWDY | 业务单元 |
| 23 | SSSYB | VARCHAR2(4000) | YES | 浏览按钮 | UF_CRMSYB | 所属销售组织 |
| 24 | YCJXS | VARCHAR2(1) | YES | 单行文本 |  | 隐藏经销商 |
| 25 | TYSHZXDM | VARCHAR2(999) | YES | 单行文本 |  | 统一社会征信代码 |
| 26 | YJHSYB | VARCHAR2(4000) | YES | 浏览按钮 | UF_CRMSYB | 已激活销售组织 |
| 27 | YELXR | VARCHAR2(999) | YES | 单行文本 |  | 业务联系人 |
| 28 | HBHDKH | VARCHAR2(1000) | YES | 浏览按钮 | UF_CRMKHKP | 合并后的客户 |
| 29 | YWY | VARCHAR2(4000) | YES | 多行文本 |  | 业务员 |
| 30 | SFJTKHZ | NUMBER | YES | 选择框 |  | 是否集团客户组 |
| 31 | SYKHNEW | NUMBER | YES | 选择框 |  | 首营客户new |
| 32 | OAKHLY | VARCHAR2(1000) | YES | 浏览按钮 | UF_CRMKHLY | 客户来源 |
| 33 | OAJTKHZ | VARCHAR2(1000) | YES | 浏览按钮 | UF_CRMJTKHZ | 集团客户组 |
| 34 | OAJGGR | VARCHAR2(1000) | YES | 浏览按钮 | UF_CRMJGGR | 机构个人 |
| 35 | KHFLNEW | VARCHAR2(1000) | YES | 浏览按钮 | UF_SAPKHLX | 客户分类new |
| 36 | BU_GROUP | VARCHAR2(1000) | YES | 浏览按钮 | UF_GYS_ZHZ | 账户组 |
| 37 | BAHNE | VARCHAR2(200) | YES | 单行文本 |  | 渠道K3客户编码 |
| 38 | FORM_BIZ_ID | VARCHAR2(100) | YES | 单行文本 |  | 表单业务ID |
| 39 | QAZK | VARCHAR2(1000) | YES | 浏览按钮 | UF_CRMQAZK | QA质控 |

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
