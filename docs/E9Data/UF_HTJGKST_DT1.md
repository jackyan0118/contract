# UF_HTJGKST_DT1 数据字典

## 表基本信息

| 属性 | 值 |
|------|-----|
| 表名 | UF_HTJGKST_DT1 |
| 描述 |  |
| 所属Schema | ECOLOGY |
| 表空间 | ECOLOGY |

## 字段列表

| 序号 | 字段名 | 数据类型 | 可空 | 字段类型 | 实体对象 | 说明 |
|------|--------|----------|------|----------|----------|------|
| 1 | ID | NUMBER | NO | 系统字段 |  | 主键 |
| 2 | MAINID | NUMBER | YES | 系统字段 |  | 关联主表ID |
| 3 | SJKHZT | VARCHAR2(1000) | YES | 浏览按钮 | UF_CRMKHKP | 设价客户主体 |
| 4 | LSH | VARCHAR2(999) | YES | 单行文本 |  | 流水号 |
| 5 | WYBS | VARCHAR2(999) | YES | 单行文本 |  | 唯一标识 |
| 6 | LYXH | NUMBER | YES | 单行文本 |  | 物料生成来源（明细） |
| 7 | DJZ | VARCHAR2(1000) | YES | 浏览按钮 | UF_CPZWH | 定价组 |
| 8 | DJZMC | VARCHAR2(999) | YES | 单行文本 |  | 定价组名称 |
| 9 | WLDM | VARCHAR2(999) | YES | 单行文本 |  | 物料代码 |
| 10 | WLMS | VARCHAR2(999) | YES | 单行文本 |  | 物料描述 |
| 11 | SFWC | NUMBER | YES | 选择框 |  | 是否外采 |
| 12 | GG | VARCHAR2(999) | YES | 单行文本 |  | 规格 |
| 13 | DW | VARCHAR2(999) | YES | 单行文本 |  | 单位 |
| 14 | JGMS | VARCHAR2(999) | YES | 单行文本 |  | 价格描述 |
| 15 | LSJ | NUMBER(38,2) | YES | 单行文本 |  | 零售价 |
| 16 | BZJXJ | NUMBER(38,2) | YES | 单行文本 |  | 标准经销价 |
| 17 | GHJY | NUMBER(38,2) | YES | 单行文本 |  | 供货价_元 |
| 18 | ZXKHKPDJY | NUMBER(38,2) | YES | 单行文本 |  | 直销客户开票单价_元 |
| 19 | JSJ | NUMBER(38,2) | YES | 单行文本 |  | 结算价 |
| 20 | KLBFB | NUMBER(38,2) | YES | 单行文本 |  | 扣率_百分比 |
| 21 | YHFDBFB | NUMBER(38,2) | YES | 单行文本 |  | 优惠幅度_百分比 |
| 22 | BZ | VARCHAR2(999) | YES | 单行文本 |  | 备注 |
| 23 | SFJL | NUMBER | YES | 选择框 |  | 是否计量 |
| 24 | SFJJ | NUMBER | YES | 选择框 |  | 是否计奖 |
| 25 | TSJGSM | VARCHAR2(1000) | YES | 浏览按钮 | UF_SAPCPLBQD | 特殊价格说明 |
| 26 | JGGXBJ | NUMBER | YES | 选择框 |  | 价格更新标记 |
| 27 | SJJD | NUMBER | YES | 选择框 |  | 设价节点 |
| 28 | SJSJ | CHAR(10) | YES | 浏览按钮 | 日期 | 设价时间 |
| 29 | SFTQSJ | NUMBER | YES | 选择框 |  | 是否提前设价 |
| 30 | XZXJG | NUMBER(38,2) | YES | 单行文本 |  | 现执行价格 |
| 31 | TPJ | NUMBER(38,2) | YES | 单行文本 |  | 突破价 |
| 32 | SCZDJJC | NUMBER(38,2) | YES | 单行文本 |  | 市场指导价_集采 |
| 33 | SCZDJFJC | NUMBER(38,2) | YES | 单行文本 |  | 市场指导价_非集采 |
| 34 | BZJXJJC | NUMBER(38,2) | YES | 单行文本 |  | 标准经销价_集采 |
| 35 | BZJXJFJC | NUMBER(38,2) | YES | 单行文本 |  | 标准经销价_非集采 |
| 36 | SFTPSYBJG | NUMBER | YES | 选择框 |  | 是否突破事业部价格 |
| 37 | JCZBJ | NUMBER(38,2) | YES | 单行文本 |  | 集采中标价 |
| 38 | JCJXJ | NUMBER(38,2) | YES | 单行文本 |  | 集采经销价 |
| 39 | SJLX | NUMBER | YES | 选择框 |  | 设价类型 |
| 40 | SJKH | VARCHAR2(1000) | YES | 浏览按钮 | UF_CRMKHKP | 设价客户 |
| 41 | SJKHZD | VARCHAR2(1000) | YES | 浏览按钮 | UF_CRMKHKP | 设价客户终端 |
| 42 | CPXF | VARCHAR2(1000) | YES | 浏览按钮 | UF_CPXF | 产品细分 |
| 43 | PP | VARCHAR2(1000) | YES | 浏览按钮 | UF_PP | 品牌 |
| 44 | JYTC | VARCHAR2(1000) | YES | 浏览按钮 | UF_JYTC | 检验套餐 |
| 45 | XMJC | VARCHAR2(1000) | YES | 浏览按钮 | UF_CPKXMJC | 项目简称 |
| 46 | JGJCY | NUMBER(38,2) | YES | 单行文本 |  | 价格间差异 |

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
