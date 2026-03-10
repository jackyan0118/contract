"""模板匹配器 - 单模板匹配核心."""

import logging
from typing import List, Dict, Any

from src.models.template_rule import TemplateRule
from src.models.match_result import MatchResult

logger = logging.getLogger(__name__)


class TemplateMatcher:
    """模板匹配器 - 单模板匹配"""

    def __init__(self, rules: List[TemplateRule]):
        self.rules = rules

    def match(self, data: Dict[str, Any]) -> MatchResult:
        """匹配模板

        Args:
            data: 报价单数据

        Returns:
            MatchResult: 匹配结果
        """
        matched_templates = []

        for rule in self.rules:
            if rule.match(data):
                matched_templates.append(rule)
                logger.debug(f"Data matched template: {rule.id} - {rule.name}")

        if not matched_templates:
            return MatchResult(
                success=False,
                templates=[],
                matched_count=0,
                reason="No matching template found"
            )

        return MatchResult(
            success=True,
            templates=matched_templates,
            matched_count=len(matched_templates),
            reason=None
        )
