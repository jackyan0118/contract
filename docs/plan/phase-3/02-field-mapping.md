# 泛微E9表单字段映射

## 表单信息
- **表单ID**: -1717
- **表名**: uf_htjgkst (主表), uf_htjgkst_dt1 (明细表)
- **Schema**: ECOLOGY

> **注意**: 完整字段列表请参考 [数据字典文档](../../E9Data/)：
> - [UF_HTJGKST 数据字典](../../E9Data/UF_HTJGKST.md)
> - [UF_HTJGKST_DT1 数据字典](../../E9Data/UF_HTJGKST_DT1.md)

---

## 主表 (UF_HTJGKST)

| 序号 | 字段名 | 数据库类型 | 字段类型 | 说明 |
|------|--------|------------|----------|------|
| 1 | ID | NUMBER | 系统字段 | 主键 |
| 2 | REQUESTID | NUMBER | 系统字段 | 流程RequestID |
| 3 | FORMMODEID | NUMBER | 系统字段 | 表单模式ID |
| 4 | MODEDATACREATER | NUMBER | 数字 | 创建人 |
| 5 | MODEDATACREATERTYPE | NUMBER | 数字 | 创建人类型 |
| 6 | MODEDATACREATEDATE | VARCHAR2(10) | 单行文本 | 创建日期 |
| 7 | MODEDATACREATETIME | VARCHAR2(8) | 单行文本 | 创建时间 |
| 8 | MODEUUID | VARCHAR2(100) | 单行文本 | 流程UUID |
| 9 | FORM_BIZ_ID | VARCHAR2(100) | 单行文本 | 业务ID |
| 10 | LCBH | VARCHAR2(999) | 单行文本 | 流程编号 |
| 11 | HTBH | VARCHAR2(999) | 单行文本 | 合同编号 |
| 12 | XGLC | NUMBER | 浏览按钮 | 相关流程 |
| 13 | WYBS | VARCHAR2(999) | 单行文本 | 主键标识(唯一标识) |
| 14 | MODEDATAMODIFIER | NUMBER | 数字 | 修改人 |
| 15 | MODEDATAMODIFYDATETIME | VARCHAR2(100) | 单行文本 | 修改时间 |

---

## 明细表 (UF_HTJGKST_DT1)

| 序号 | 字段名 | 数据库类型 | 字段类型 | 实体对象 | 说明 |
|------|--------|------------|----------|----------|------|
| 1 | ID | NUMBER | 系统字段 | | 主键 |
| 2 | MAINID | NUMBER | 系统字段 | | 主表ID |
| 3 | SJKHZT | VARCHAR2(1000) | 浏览按钮 | UF_CRMKHKP | 设价客户主体 |
| 4 | LSH | VARCHAR2(999) | 单行文本 | | 流水号 |
| 5 | WYBS | VARCHAR2(999) | 单行文本 | | 主键标识 |
| 6 | LYXH | NUMBER | 单行文本 | | 物料生成来源（明细） |
| 7 | DJZ | VARCHAR2(1000) | 浏览按钮 | UF_CPZWH | 定价组 |
| 8 | DJZMC | VARCHAR2(999) | 单行文本 | | 定价组名称 |
| 9 | WLDM | VARCHAR2(999) | 单行文本 | | 物料代码 |
| 10 | WLMS | VARCHAR2(999) | 单行文本 | | 物料描述 |
| 11 | SFWC | NUMBER | 选择框 | | 是否外采 |
| 12 | GG | VARCHAR2(999) | 单行文本 | | 规格 |
| 13 | DW | VARCHAR2(999) | 单行文本 | | 单位 |
| 14 | JGMS | VARCHAR2(999) | 单行文本 | | 价格描述 |
| 15 | LSJ | NUMBER(38,2) | 单行文本 | | 零售价 |

> 完整46个字段请参考 [UF_HTJGKST_DT1 数据字典](../../E9Data/UF_HTJGKST_DT1.md)
| 16 | BZJXJ | NUMBER(22) | 标准价(升级价) | -174422 |
| 17 | GHJY | NUMBER(22) | 供货价 | -174423 |
| 18 | ZXKHKPDJY | NUMBER(22) | 执行客户开单价(代理价) | -174424 |
| 19 | JSJ | NUMBER(22) | 结算价 | -174425 |
| 20 | KLBFB | NUMBER(22) | 扣率百分比 | -174426 |
| 21 | YHFDBFB | NUMBER(22) | 优惠幅度百分比 | -174427 |
| 22 | BZ | VARCHAR2(999) | 备注 | -174428 |
| 23 | SFJL | NUMBER(22) | 是否记录 | -174429 |
| 24 | SFJJ | NUMBER(22) | 是否计价 | -174430 |
| 25 | TSJGSM | VARCHAR2(1000) | 特殊价格说明 | -174431 |
| 26 | JGGXBJ | NUMBER(22) | 价格是否有效 | -174432 |
| 27 | SJJD | NUMBER(22) | 税前几点 | -174433 |
| 28 | SJSJ | CHAR(10) | 税前税价 | -174434 |
| 29 | SFTQSJ | NUMBER(22) | 是否提取税价 | -174435 |
| 30 | XZXJG | NUMBER(22) | 税后总价格 | -174436 |
| 31 | TPJ | NUMBER(22) | 调票价 | -174437 |
| 32 | SCZDJJC | NUMBER(22) | 市场指导价(基础) | -174438 |
| 33 | SCZDJFJC | NUMBER(22) | 市场指导价(加价) | -174439 |
| 34 | BZJXJJC | NUMBER(22) | 标准升级价(基础) | -174440 |
| 35 | BZJXJFJC | NUMBER(22) | 标准升级价(加价) | -174441 |
| 36 | SFTPSYBJG | NUMBER(22) | 是否提取市场报价 | -174442 |
| 37 | JCZBJ | NUMBER(22) | 基础报价 | -174443 |
| 38 | JCJXJ | NUMBER(22) | 基础净价 | -174444 |
| 39 | SJLX | NUMBER(22) | 数据类型 | -174445 |
| 40 | SJKH | VARCHAR2(1000) | 客户 | -174446 |
| 41 | SJKHZD | VARCHAR2(1000) | 客户组 | -174447 |
| 42 | CPXF | VARCHAR2(1000) | 产品型号 | -174448 |
| 43 | PP | VARCHAR2(1000) | 品牌 | -174449 |
| 44 | JYTC | VARCHAR2(1000) | 业态 | -174450 |
| 45 | XMJC | VARCHAR2(1000) | 项目简称 | -174451 |
| 46 | JGJCY | NUMBER(22) | 价格间差异 | -174452 |

---

## 字段类型说明

| 字段类型 | 说明 | 存储内容 |
|----------|------|----------|
| 系统字段 | ID, REQUESTID, FORMMODEID 等系统管理字段 | - |
| 单行文本 | VARCHAR2 类型文本字段 | 文本内容 |
| 数字 | NUMBER 类型数值字段 | 数值 |
| 选择框 | 单选/多选标记字段 | 0/1 整数值 |
| 浏览按钮 | 关联选择字段 | 实体表ID |

### 浏览按钮字段对应实体对象

| 字段名 | 实体对象 | 说明 |
|--------|----------|------|
| XGLC | WORKFLOW_REQUESTBASE | 相关流程 |
| SJKHZT | UF_CRMKHKP | 设价客户主体 |
| DJZ | UF_CPZWH | 定价组 |
| TSJGSM | UF_SAPCPLBQD | 特殊价格说明 |
| SJKH | UF_CRMKHKP | 设价客户 |
| SJKHZD | UF_CRMKHKP | 设价客户终端 |
| CPXF | UF_CPXF | 产品细分 |
| PP | UF_PP | 品牌 |
| JYTC | UF_JYTC | 检验套餐 |
| XMJC | UF_CPKXMJC | 项目简称 |

> 详细字段映射请参考 [数据字典文档](../../E9Data/) 和 [实体对象汇总](../../E9Data/entity-summary.md)

---

## 查询关键字段

### 通过WYBS(唯一标识)查询报价单
```sql
-- 查询主表
SELECT * FROM ecology.uf_htjgkst WHERE wybs = :wybs;

-- 查询明细表
SELECT * FROM ecology.uf_htjgkst_dt1 WHERE mainid = :main_id;
```

### 关键关联字段
- **主表主键**: ID (通过 MODEDATACREATER 关联创建人)
- **明细表关联**: MAINID -> 主表.ID
- **流程关联**: REQUESTID -> 泛微流程表
- **唯一标识**: WYBS (用于外部系统关联)

---

## 泛微系统字段ID映射

字段标签ID（需要通过泛微多语言表查询实际中文）:
- -174409: 客户主体 (browser类型)
- -174410: 流水号
- -174411: 主键标识
- -174412: 序号
- -174413: 等级 (browser类型)
- -174414: 等级名称
- -174415: 物料代码
- -174416: 物料描述
- -174417: 是否完成
- -174418: 规格
- -174419: 单位
- -174420: 价格描述
- -174421: 零售价
- -174422: 标准价(升级价)
- -174423: 供货价
- -174424: 执行客户开单价
- -174425: 结算价
- -174426: 扣率百分比
- -174427: 优惠幅度百分比
- -174428: 备注
- -174429: 是否记录
- -174430: 是否计价
- -174431: 特殊价格说明
- -174432: 价格是否有效
- -174433: 税前几点
- -174434: 税前税价
- -174435: 是否提取税价
- -174436: 税后总价格
- -174437: 调票价
- -174438: 市场指导价(基础)
- -174439: 市场指导价(加价)
- -174440: 标准升级价(基础)
- -174441: 标准升级价(加价)
- -174442: 是否提取市场报价
- -174443: 基础报价
- -174444: 基础净价
- -174445: 数据类型
- -174446: 客户 (browser类型)
- -174447: 客户组 (browser类型)
- -174448: 产品型号 (browser类型)
- -174449: 品牌 (browser类型)
- -174450: 业态 (browser类型)
- -174451: 项目简称 (browser类型)
- -174452: 价格间差异
- -174453: WYBS(主表)
- -174406: 流程编号
- -174407: 合同编号
- -174408: 相关流程
