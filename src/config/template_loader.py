"""模板配置加载器 - 从 YAML 加载模板元数据."""

import yaml
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class ConditionModel(BaseModel):
    """条件模型"""
    field: str
    operator: str = "="
    value: Any


class FilterRuleModel(BaseModel):
    """过滤规则模型"""
    id: str
    name: str
    conditions: List[ConditionModel] = Field(default_factory=list)


class DetailFilterModel(BaseModel):
    """明细过滤模型"""
    filter_rules: List[FilterRuleModel] = Field(default_factory=list)


class TableColumnModel(BaseModel):
    """表格列模型"""
    name: str
    source_field: str
    source_table: str = "UF_HTJGKST_DT1"
    type: str = "text"  # text, auto_number
    transform: Optional[str] = None
    params: Dict[str, Any] = Field(default_factory=dict)


class TableModel(BaseModel):
    """表格配置模型"""
    placeholders: Dict[str, str] = Field(default_factory=dict)
    columns: List[TableColumnModel] = Field(default_factory=list)


class SpeechVariableModel(BaseModel):
    """话术变量模型"""
    name: str
    default: str


class SpeechModel(BaseModel):
    """话术模型"""
    id: str
    type: str = "conditional"  # conditional, fixed
    mutex_group: Optional[str] = None
    conditions: List[ConditionModel] = Field(default_factory=list)
    content: str = ""
    variables: List[SpeechVariableModel] = Field(default_factory=list)


class TemplateMetadataModel(BaseModel):
    """模板元数据模型"""
    id: str
    name: str
    file: str
    category: str = ""
    match_conditions: Dict[str, Any] = Field(default_factory=dict)
    detail_filter: Optional[DetailFilterModel] = None
    table: Optional[TableModel] = None
    paragraph_placeholders: Dict[str, str] = Field(default_factory=dict)
    speeches: List[SpeechModel] = Field(default_factory=list)


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
