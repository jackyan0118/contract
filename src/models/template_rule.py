"""模板规则数据模型."""

from typing import Optional, List, Dict, Any, Union
from pydantic import BaseModel, Field


class RuleCondition(BaseModel):
    """匹配条件 - 所有字段为精确匹配（AND关系）"""
    产品细分编号: Optional[Union[str, list]] = Field(default=None, description="产品细分编号，支持列表如['11','41']")
    产品细分: Optional[Union[str, list]] = Field(default=None, description="产品细分名称")
    定价组编号: Optional[Union[str, list]] = Field(default=None, description="定价组编号，支持列表")
    定价组名称: Optional[Union[str, list]] = Field(default=None, description="定价组名称")
    是否集采: Optional[Union[str, list]] = Field(default=None, description="是否集采: 0=是, 1=否")
    供货价类型: Optional[Union[str, list]] = Field(default=None, description="供货价类型")
    物料代码: Optional[Union[str, list]] = Field(default=None, description="物料代码，支持列表")
    品牌编号: Optional[Union[str, list]] = Field(default=None, description="品牌编号")

    def match(self, data: Dict[str, Any]) -> bool:
        """检查数据是否满足此条件

        Args:
            data: 待匹配的数据字典

        Returns:
            bool: 所有条件都满足返回 True，否则返回 False
        """
        for field, expected in self.model_dump(exclude_none=True).items():
            actual = data.get(field)
            # 处理 None 值
            if actual is None:
                return False
            # 统一转为字符串
            actual_str = str(actual).strip()
            expected_str = str(expected).strip()

            # 支持列表多值匹配（如 ['11', '41']）
            if isinstance(expected, (list, tuple)):
                expected_strs = [str(v).strip() for v in expected]
                if actual_str not in expected_strs:
                    return False
            else:
                # 普通精确匹配
                if actual_str != expected_str:
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
