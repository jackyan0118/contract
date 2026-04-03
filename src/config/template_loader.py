"""模板配置加载器 - 从 YAML 加载模板元数据."""

import yaml
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any, Literal
from pydantic import BaseModel, Field, ConfigDict
from enum import Enum

logger = logging.getLogger(__name__)


class Operator(str, Enum):
    """操作符枚举"""
    EQ = "="
    NE = "!="
    CONTAINS = "contains"
    IN = "in"
    NOT_IN = "not_in"
    GT = ">"
    LT = "<"
    GTE = ">="
    LTE = "<="


class ConditionModel(BaseModel):
    """条件模型"""
    model_config = ConfigDict(populate_by_name=True)

    field: str
    operator: Operator = Operator.EQ
    value: Any
    value_type: Optional[str] = None  # 可选：指定值的类型，如 "bm" 表示BM编码需转换为ID


class FilterRuleModel(BaseModel):
    """过滤规则模型"""
    model_config = ConfigDict(populate_by_name=True)

    id: Optional[str] = None  # 兼容：YAML中使用name作为标识
    name: Optional[str] = None
    conditions: List[ConditionModel] = Field(default_factory=list)

    def get_id(self) -> str:
        """获取规则ID"""
        return self.id or self.name or ""


class DetailFilterModel(BaseModel):
    """明细过滤模型"""
    model_config = ConfigDict(populate_by_name=True)

    filter_rules: Optional[List[FilterRuleModel]] = Field(default_factory=list)
    condition_groups: Optional[List[FilterRuleModel]] = Field(default_factory=list)  # 兼容旧版YAML

    def get_rules(self) -> List[FilterRuleModel]:
        """获取过滤规则，兼容新旧版本"""
        return self.filter_rules if self.filter_rules else self.condition_groups or []


class ColumnType(str, Enum):
    """列类型枚举"""
    TEXT = "text"
    AUTO_NUMBER = "auto_number"


class TableColumnModel(BaseModel):
    """表格列模型"""
    model_config = ConfigDict(populate_by_name=True)

    name: str
    source_field: Optional[str] = None  # auto_number 类型时可以为 None
    source_table: str = "UF_HTJGKST_DT1"
    type: ColumnType = ColumnType.TEXT
    transform: Optional[str] = None
    params: Dict[str, Any] = Field(default_factory=dict)


class TableModel(BaseModel):
    """表格配置模型"""
    model_config = ConfigDict(populate_by_name=True)

    placeholders: Dict[str, str] = Field(default_factory=dict)
    columns: List[TableColumnModel] = Field(default_factory=list)


class SpeechVariableModel(BaseModel):
    """话术变量模型"""
    model_config = ConfigDict(populate_by_name=True)

    name: str
    default: str


class SpeechType(str, Enum):
    """话术类型枚举"""
    CONDITIONAL = "conditional"
    FIXED = "fixed"


class SpeechModel(BaseModel):
    """话术模型"""
    model_config = ConfigDict(populate_by_name=True)

    id: str
    type: SpeechType = SpeechType.CONDITIONAL
    mutex_group: Optional[str] = None
    conditions: List[ConditionModel] = Field(default_factory=list)
    content: str = ""
    variables: List[SpeechVariableModel] = Field(default_factory=list)


class ProductMatchItem(BaseModel):
    """产品匹配项"""
    name: str
    seq: int = 0


class ProductMatchModel(BaseModel):
    """产品匹配模型"""
    match_field: str = "WLMS"  # 匹配字段
    products: List[ProductMatchItem] = Field(default_factory=list)


class SortRuleModel(BaseModel):
    """排序规则模型"""
    name: str = ""
    description: str = ""
    field: str = ""
    order: str = "asc"  # asc 或 desc


class DedupRuleModel(BaseModel):
    """去重规则模型"""
    name: str = ""
    field: str = ""


class DiscountTemplateModel(BaseModel):
    """折扣话术模板模型"""
    seq_range: List[int] = Field(default_factory=list)
    template: str = ""


class TemplateMetadataModel(BaseModel):
    """模板元数据模型"""
    model_config = ConfigDict(populate_by_name=True)

    id: str
    name: str
    file: str
    category: str = ""
    match_conditions: Dict[str, Any] = Field(default_factory=dict)
    detail_filter: Optional[DetailFilterModel] = None
    table: Optional[TableModel] = None
    paragraph_placeholders: Dict[str, str] = Field(default_factory=dict)
    speeches: List[SpeechModel] = Field(default_factory=list)
    product_matching: Optional[ProductMatchModel] = None
    discount_template: Optional[str] = None
    discount_templates: List[DiscountTemplateModel] = Field(default_factory=list)
    sort_rules: List[SortRuleModel] = Field(default_factory=list)
    dedup_rules: List[DedupRuleModel] = Field(default_factory=list)


class TemplateLoader:
    """模板配置加载器"""

    def __init__(self, config_dir: str = "config/template_metadata/templates"):
        self.config_dir = Path(config_dir)

    def load(self, template_id: str) -> TemplateMetadataModel:
        """加载指定模板的配置

        Args:
            template_id: 模板ID

        Returns:
            TemplateMetadataModel: 模板元数据

        Raises:
            FileNotFoundError: 配置文件不存在
        """
        config_file = self.config_dir / f"{template_id}.yaml"

        if not config_file.exists():
            raise FileNotFoundError(f"Template config not found: {config_file}")

        logger.info(f"Loading template config: {config_file}")

        with open(config_file, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)

        return TemplateMetadataModel(**data)

    def load_all(self) -> List[TemplateMetadataModel]:
        """加载所有模板配置

        Returns:
            List[TemplateMetadataModel]: 所有模板配置列表
        """
        templates = []

        for config_file in self.config_dir.glob("*.yaml"):
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    data = yaml.safe_load(f)
                    templates.append(TemplateMetadataModel(**data))
            except Exception as e:
                logger.warning(f"Failed to load {config_file}: {e}")

        logger.info(f"Loaded {len(templates)} template configs")
        return templates
