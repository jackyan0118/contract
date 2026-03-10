"""模板匹配结果数据模型."""

from typing import Optional, List
from pydantic import BaseModel, Field, computed_field

from src.models.template_rule import TemplateRule


class MatchResult(BaseModel):
    """模板匹配结果"""
    success: bool = Field(description="是否匹配成功")
    templates: List[TemplateRule] = Field(default_factory=list, description="匹配的模板列表（按优先级排序）")
    matched_count: int = Field(description="匹配数量")
    reason: Optional[str] = Field(default=None, description="未匹配原因")

    @computed_field
    @property
    def template(self) -> Optional[TemplateRule]:
        """获取第一个匹配的模板（向后兼容）"""
        return self.templates[0] if self.templates else None
