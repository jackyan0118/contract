"""报价单数据模型."""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal
from typing import Optional


@dataclass(frozen=True)
class Quotation:
    """报价单主表模型.

    对应数据库表: uf_htjgkst
    查询主键: WYBS (唯一标识)
    """

    # 主键
    id: int
    wybs: str  # 唯一标识（查询主键）

    # 流程相关
    requestid: Optional[int] = None
    formmodeid: Optional[int] = None
    modeuuid: Optional[str] = None
    form_biz_id: Optional[str] = None

    # 业务字段
    lcbh: Optional[str] = None  # 流程编号
    htbh: Optional[str] = None  # 合同编号
    xglc: Optional[int] = None  # 相关流程

    # 创建信息
    creater: Optional[int] = None
    createdate: Optional[str] = None
    createtime: Optional[str] = None


@dataclass(frozen=True)
class QuotationDetail:
    """报价单明细模型.

    对应数据库表: uf_htjgkst_dt1
    关联主表: MAINID -> uf_htjgkst.ID
    """

    # 主键
    id: int
    mainid: int  # 关联主表.ID
    wybs: str  # 唯一标识

    # 序号
    lyxh: int

    # 物料信息
    wldm: Optional[str] = None  # 物料代码
    wlms: Optional[str] = None  # 物料描述
    gg: Optional[str] = None  # 规格
    dw: Optional[str] = None  # 单位

    # 价格字段
    lsj: Optional[Decimal] = None  # 零售价
    bzjxj: Optional[Decimal] = None  # 标准价(升级价)
    ghjy: Optional[Decimal] = None  # 供货价
    zxkhkpdjy: Optional[Decimal] = None  # 执行客户开单价
    jsj: Optional[Decimal] = None  # 结算价
    klbfb: Optional[Decimal] = None  # 扣率百分比
    yhfdbfb: Optional[Decimal] = None  # 优惠幅度百分比

    # 价格描述
    jgms: Optional[str] = None

    # 状态标记
    sfwc: Optional[int] = None  # 是否完成
    sfjl: Optional[int] = None  # 是否记录
    sfjj: Optional[int] = None  # 是否计价
    bz: Optional[str] = None  # 备注

    # 价格更新相关字段（新增）
    jggxbj: Optional[int] = None  # 价格更新标记
    sjjd: Optional[int] = None  # 设价节点
    sftqsj: Optional[int] = None  # 是否提前设价
    sftpsybjg: Optional[int] = None  # 是否突破事业部价格
    sjlx: Optional[int] = None  # 设价类型
    sjsj: Optional[str] = None  # 设价时间

    # 扩展价格字段（新增）
    xzxjg: Optional[Decimal] = None  # 现执行价格
    tpj: Optional[Decimal] = None  # 突破价
    sczdjjc: Optional[Decimal] = None  # 市场指导价_集采
    sczdjfjc: Optional[Decimal] = None  # 市场指导价_非集采
    bzjxjjc: Optional[Decimal] = None  # 标准经销价_集采
    bzjxjfjc: Optional[Decimal] = None  # 标准经销价_非集采
    jczbj: Optional[Decimal] = None  # 集采中标价
    jcjxj: Optional[Decimal] = None  # 集采经销价
    jgjcy: Optional[Decimal] = None  # 价格间差异

    # 扩展字段（Browser类型）
    sjkht: Optional[str] = None  # 客户主体
    djz: Optional[str] = None  # 等级
    djzmc: Optional[str] = None  # 等级名称
    sjkhan: Optional[str] = None  # 客户
    sjkhan_zd: Optional[str] = None  # 客户组
    cpxf: Optional[str] = None  # 产品型号
    pp: Optional[str] = None  # 品牌
    jytc: Optional[str] = None  # 业态
    xmjc: Optional[str] = None  # 项目简称
    tsjgsm: Optional[str] = None  # 特殊价格说明


@dataclass(frozen=True)
class QuotationItem:
    """报价单项（合并主表和明细的完整数据）.

    这是系统内部使用的完整报价单模型，
    包含主表信息和明细列表。
    """

    # 主表核心字段
    wybs: str  # 唯一标识（查询主键）
    id: int = 0  # 主表主键

    # 扩展字段
    lcbh: Optional[str] = None  # 流程编号
    htbh: Optional[str] = None  # 合同编号
    xglc: Optional[int] = None  # 相关流程

    # 明细列表
    items: list[QuotationDetail] = field(default_factory=list)

    def __post_init__(self):
        if self.items is None:
            self.items = []

    @property
    def item_count(self) -> int:
        """明细行数."""
        return len(self.items)
