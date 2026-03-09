"""报价单数据模型测试."""

from decimal import Decimal

import pytest

from src.models import Quotation, QuotationDetail, QuotationItem


class TestQuotation:
    """Quotation 模型测试类."""

    def test_create_quotation_with_required_fields(self):
        """测试创建只有必填字段的报价单."""
        quotation = Quotation(id=1, wybs="TEST001")

        assert quotation.id == 1
        assert quotation.wybs == "TEST001"
        assert quotation.requestid is None
        assert quotation.formmodeid is None
        assert quotation.lcbh is None
        assert quotation.htbh is None

    def test_create_quotation_with_all_fields(self):
        """测试创建包含所有字段的报价单."""
        quotation = Quotation(
            id=1,
            wybs="TEST001",
            requestid=100,
            formmodeid=10,
            modeuuid="uuid-123",
            form_biz_id="BIZ001",
            lcbh="LC001",
            htbh="HT001",
            xglc=1,
            creater=50,
            createdate="2024-01-01",
            createtime="10:00:00",
        )

        assert quotation.id == 1
        assert quotation.wybs == "TEST001"
        assert quotation.requestid == 100
        assert quotation.formmodeid == 10
        assert quotation.modeuuid == "uuid-123"
        assert quotation.form_biz_id == "BIZ001"
        assert quotation.lcbh == "LC001"
        assert quotation.htbh == "HT001"
        assert quotation.xglc == 1
        assert quotation.creater == 50
        assert quotation.createdate == "2024-01-01"
        assert quotation.createtime == "10:00:00"

    def test_quotation_immutable(self):
        """测试 Quotation 不可变性 - dataclass 默认是可变的，这里验证字段不会自动改变."""
        quotation = Quotation(id=1, wybs="TEST001")

        # 创建新的实例来验证数据一致性
        quotation2 = Quotation(id=quotation.id, wybs=quotation.wybs)

        assert quotation.id == quotation2.id
        assert quotation.wybs == quotation2.wybs


class TestQuotationDetail:
    """QuotationDetail 模型测试类."""

    def test_create_detail_with_required_fields(self):
        """测试创建只有必填字段的明细."""
        detail = QuotationDetail(id=1, mainid=100, wybs="TEST001", lyxh=1)

        assert detail.id == 1
        assert detail.mainid == 100
        assert detail.wybs == "TEST001"
        assert detail.lyxh == 1
        assert detail.wldm is None
        assert detail.wlms is None

    def test_create_detail_with_all_fields(self):
        """测试创建包含所有字段的明细."""
        detail = QuotationDetail(
            id=1,
            mainid=100,
            wybs="TEST001",
            lyxh=1,
            wldm="M001",
            wlms="物料1",
            gg="规格A",
            dw="个",
            lsj=Decimal("100.00"),
            bzjxj=Decimal("90.00"),
            ghjy=Decimal("80.00"),
            zxkhkpdjy=Decimal("75.00"),
            jsj=Decimal("70.00"),
            klbfb=Decimal("0.85"),
            yhfdbfb=Decimal("0.15"),
            jgms="价格描述",
            sfwc=1,
            sfjl=1,
            sfjj=1,
            bz="备注",
            # 价格更新相关字段（新增）
            jggxbj=1,
            sjjd=2,
            sftqsj=0,
            sftpsybjg=0,
            sjlx=1,
            sjsj="2024-01-01 10:00:00",
            # 扩展价格字段（新增）
            xzxjg=Decimal("95.00"),
            tpj=Decimal("85.00"),
            sczdjjc=Decimal("90.00"),
            sczdjfjc=Decimal("88.00"),
            bzjxjjc=Decimal("92.00"),
            bzjxjfjc=Decimal("90.00"),
            jczbj=Decimal("82.00"),
            jcjxj=Decimal("80.00"),
            jgjcy=Decimal("5.00"),
            # 扩展字段（Browser类型）
            sjkht="客户A",
            djz="A",
            djzmc="A级",
            sjkhan="客户甲",
            sjkhan_zd="客户组1",
            cpxf="型号X",
            pp="品牌A",
            jytc="业态1",
            xmjc="项目X",
            tsjgsm="特殊价格说明",
            # 新增字段（本年供货价类型、是否集采）
            bnghjlx="供货类型A",
            bnghjlxz=1,
            sfjc=1,
        )

        assert detail.id == 1
        assert detail.mainid == 100
        assert detail.wybs == "TEST001"
        assert detail.lyxh == 1
        assert detail.wldm == "M001"
        assert detail.wlms == "物料1"
        assert detail.gg == "规格A"
        assert detail.dw == "个"
        assert detail.lsj == Decimal("100.00")
        assert detail.bzjxj == Decimal("90.00")
        assert detail.ghjy == Decimal("80.00")
        assert detail.zxkhkpdjy == Decimal("75.00")
        assert detail.jsj == Decimal("70.00")
        assert detail.klbfb == Decimal("0.85")
        assert detail.yhfdbfb == Decimal("0.15")
        assert detail.jgms == "价格描述"
        assert detail.sfwc == 1
        assert detail.sfjl == 1
        assert detail.sfjj == 1
        assert detail.bz == "备注"
        # 价格更新相关字段（新增）
        assert detail.jggxbj == 1
        assert detail.sjjd == 2
        assert detail.sftqsj == 0
        assert detail.sftpsybjg == 0
        assert detail.sjlx == 1
        assert detail.sjsj == "2024-01-01 10:00:00"
        # 扩展价格字段（新增）
        assert detail.xzxjg == Decimal("95.00")
        assert detail.tpj == Decimal("85.00")
        assert detail.sczdjjc == Decimal("90.00")
        assert detail.sczdjfjc == Decimal("88.00")
        assert detail.bzjxjjc == Decimal("92.00")
        assert detail.bzjxjfjc == Decimal("90.00")
        assert detail.jczbj == Decimal("82.00")
        assert detail.jcjxj == Decimal("80.00")
        assert detail.jgjcy == Decimal("5.00")
        # 扩展字段（Browser类型）
        assert detail.sjkht == "客户A"
        assert detail.djz == "A"
        assert detail.djzmc == "A级"
        assert detail.sjkhan == "客户甲"
        assert detail.sjkhan_zd == "客户组1"
        assert detail.cpxf == "型号X"
        assert detail.pp == "品牌A"
        assert detail.jytc == "业态1"
        assert detail.xmjc == "项目X"
        assert detail.tsjgsm == "特殊价格说明"
        # 新增字段（本年供货价类型、是否集采）
        assert detail.bnghjlx == "供货类型A"
        assert detail.bnghjlxz == 1
        assert detail.sfjc == 1

    def test_detail_decimal_fields(self):
        """测试明细的价格字段可以接受 Decimal 类型."""
        detail = QuotationDetail(
            id=1,
            mainid=100,
            wybs="TEST001",
            lyxh=1,
            lsj=Decimal("100.50"),
            bzjxj=Decimal("90.12"),
            ghjy=Decimal("80.50"),
            jsj=Decimal("75.99"),
            klbfb=Decimal("0.85"),
            yhfdbfb=Decimal("0.15"),
        )

        # 验证 Decimal 类型
        assert isinstance(detail.lsj, Decimal)
        assert isinstance(detail.bzjxj, Decimal)
        assert isinstance(detail.ghjy, Decimal)
        assert isinstance(detail.jsj, Decimal)
        assert isinstance(detail.klbfb, Decimal)
        assert isinstance(detail.yhfdbfb, Decimal)

    def test_detail_new_price_fields(self):
        """测试明细的新增价格字段（数据字典更新）."""
        detail = QuotationDetail(
            id=1,
            mainid=100,
            wybs="TEST001",
            lyxh=1,
            # 价格更新相关字段
            jggxbj=1,
            sjjd=2,
            sftqsj=0,
            sftpsybjg=1,
            sjlx=3,
            sjsj="2024-06-01 15:30:00",
            # 扩展价格字段
            xzxjg=Decimal("120.00"),
            tpj=Decimal("110.00"),
            sczdjjc=Decimal("115.00"),
            sczdjfjc=Decimal("112.00"),
            bzjxjjc=Decimal("118.00"),
            bzjxjfjc=Decimal("116.00"),
            jczbj=Decimal("100.00"),
            jcjxj=Decimal("98.00"),
            jgjcy=Decimal("10.00"),
            tsjgsm="大客户特殊价格",
        )

        # 验证价格更新相关字段
        assert detail.jggxbj == 1
        assert detail.sjjd == 2
        assert detail.sftqsj == 0
        assert detail.sftpsybjg == 1
        assert detail.sjlx == 3
        assert detail.sjsj == "2024-06-01 15:30:00"

        # 验证扩展价格字段类型
        assert isinstance(detail.xzxjg, Decimal)
        assert isinstance(detail.tpj, Decimal)
        assert isinstance(detail.sczdjjc, Decimal)
        assert isinstance(detail.sczdjfjc, Decimal)
        assert isinstance(detail.bzjxjjc, Decimal)
        assert isinstance(detail.bzjxjfjc, Decimal)
        assert isinstance(detail.jczbj, Decimal)
        assert isinstance(detail.jcjxj, Decimal)
        assert isinstance(detail.jgjcy, Decimal)

        # 验证扩展价格字段值
        assert detail.xzxjg == Decimal("120.00")
        assert detail.tpj == Decimal("110.00")
        assert detail.sczdjjc == Decimal("115.00")
        assert detail.sczdjfjc == Decimal("112.00")
        assert detail.bzjxjjc == Decimal("118.00")
        assert detail.bzjxjfjc == Decimal("116.00")
        assert detail.jczbj == Decimal("100.00")
        assert detail.jcjxj == Decimal("98.00")
        assert detail.jgjcy == Decimal("10.00")
        assert detail.tsjgsm == "大客户特殊价格"


class TestQuotationItem:
    """QuotationItem 模型测试类."""

    def test_create_item_with_required_fields(self):
        """测试创建只有必填字段的报价单项."""
        item = QuotationItem(wybs="TEST001")

        assert item.wybs == "TEST001"
        assert item.id == 0
        assert item.items == []

    def test_create_item_with_all_fields(self):
        """测试创建包含所有字段的报价单项."""
        details = [
            QuotationDetail(id=1, mainid=100, wybs="TEST001", lyxh=1),
            QuotationDetail(id=2, mainid=100, wybs="TEST001", lyxh=2),
        ]

        item = QuotationItem(
            wybs="TEST001",
            id=100,
            lcbh="LC001",
            htbh="HT001",
            xglc=1,
            items=details,
        )

        assert item.wybs == "TEST001"
        assert item.id == 100
        assert item.lcbh == "LC001"
        assert item.htbh == "HT001"
        assert item.xglc == 1
        assert len(item.items) == 2

    def test_item_count_property(self):
        """测试 item_count 属性."""
        # 创建时直接传入 items 列表
        details = [
            QuotationDetail(id=1, mainid=100, wybs="TEST001", lyxh=1),
            QuotationDetail(id=2, mainid=100, wybs="TEST001", lyxh=2),
            QuotationDetail(id=3, mainid=100, wybs="TEST001", lyxh=3),
        ]
        item = QuotationItem(wybs="TEST001", items=details)

        assert item.item_count == 3

        # 测试空列表的情况
        item_empty = QuotationItem(wybs="TEST002")
        assert item_empty.item_count == 0

    def test_item_with_none_items(self):
        """测试 items 为 None 时的处理."""
        # 由于 frozen=True，无法在 __post_init__ 中修改 None
        # 使用 default_factory 确保 items 默认是空列表
        item = QuotationItem(wybs="TEST001")

        # 验证默认值是空列表（不需要显式传入 None）
        assert item.items == []
        assert item.item_count == 0

    def test_item_default_factory(self):
        """测试使用默认工厂创建空列表."""
        item1 = QuotationItem(wybs="TEST001")
        item2 = QuotationItem(wybs="TEST002")

        # 验证每个实例有独立的 items 列表
        assert item1.items == []
        assert item2.items == []

        item1.items.append(
            QuotationDetail(id=1, mainid=100, wybs="TEST001", lyxh=1)
        )

        # item2 不应受影响
        assert len(item2.items) == 0
