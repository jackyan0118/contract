"""多模板匹配处理器."""

import logging
from typing import List, Dict, Any

from src.models.template_rule import TemplateRule
from src.models.match_result import MatchResult
from src.matchers.template_matcher import TemplateMatcher

logger = logging.getLogger(__name__)


class MultiMatcher:
    """多模板匹配处理器"""

    def __init__(self, rules: List[TemplateRule]):
        self.matcher = TemplateMatcher(rules)

    def match_quote(self, quote_data: Dict[str, Any]) -> MatchResult:
        """匹配报价单主表数据

        Args:
            quote_data: 报价单主表数据

        Returns:
            MatchResult: 包含所有匹配模板的结果
        """
        result = self.matcher.match(quote_data)

        if result.matched_count > 1:
            logger.warning(
                f"Multiple templates matched for quote. "
                f"Matched templates: {[t.id for t in result.templates]}"
            )

        return result

    def match_details(self, detail_data_list: List[Dict[str, Any]]) -> List[MatchResult]:
        """匹配报价单明细数据

        Args:
            detail_data_list: 报价单明细数据列表

        Returns:
            List[MatchResult]: 每个明细的匹配结果
        """
        results = []
        for detail in detail_data_list:
            result = self.matcher.match(detail)
            results.append(result)

            if result.matched_count > 1:
                logger.warning(
                    f"Multiple templates matched for detail. "
                    f"Matched templates: {[t.id for t in result.templates]}"
                )

        return results
