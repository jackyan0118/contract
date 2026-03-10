"""模板规则数据模型."""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class RuleCondition(BaseModel):
    """匹配条件 - 所有字段为精确匹配（AND关系）"""
    产品细分编号: Optional[str] = Field(default=None, description="产品细分编号")
    产品细分: Optional[str] = Field(default=None, description="产品细分名称")
    定价组编号: Optional[str] = Field(default=None, description="定价组编号")
    定价组名称: Optional[str] = Field(default=None, description="定价组名称")
    是否集采: Optional[str] = Field(default=None, description="是否集采: 0=是, 1=否")
    供货价类型: Optional[str] = Field(default=None, description="供货价类型")

    def match(self, data: Dict[str, Any]) -> bool:
        """检查数据是否满足此条件

        Args:
            data: 待匹配的数据字典

        Returns:
            bool: 所有条件都满足返回 True，否则返回 False
        """
        for field, expected in self.model_dump(exclude_none=True).items():
            actual = data.get(field)
            # 处理 None 值和不匹配的情况
            if actual is None:
                return False
            # 统一转为字符串比较，过滤空格
            if str(actual).strip() != str(expected).strip():
                return False
        return True


class TemplateRule(BaseModel):
    """模板规则"""
    id: str = Field(description="模板ID，如 模板1")
    name: str = Field(description="模板名称")
    file: str = Field(description="模板文件路径")
    条件: List[RuleCondition] = Field(default_factory=list, description="条件列表（AND关系）")
    排序规则: Optional[str] = Field(default=None, description="排序规则")

    def match(self, data: Dict[str, Any]) -> bool:
        """检查数据是否匹配此模板（所有条件都满足）"""
        if not self.条件:
            return True  # 无条件则匹配所有
        return all(condition.match(data) for condition in self.条件)
