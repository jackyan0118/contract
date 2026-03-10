"""话术处理器 - 处理话术逻辑和互斥组."""

import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field

from src.fillers.data_filler import DataFiller, FilterCondition

logger = logging.getLogger(__name__)


@dataclass
class Speech:
    """话术"""
    id: str
    content: str
    type: str  # conditional, fixed
    mutex_group: Optional[str] = None
    variables: Dict[str, str] = field(default_factory=dict)


class SpeechProcessor:
    """话术处理器"""

    # 默认话术变量
    DEFAULT_VARIABLES = {
        "肝功扣率": "85",
        "通用扣率": "70",
        "北极星扣率": "25",
        "耗材扣率": "50",
    }

    def __init__(self):
        self.data_filler = DataFiller()

    def process_speeches(
        self,
        speech_configs: List[Speech],
        data: Dict[str, Any]
    ) -> List[str]:
        """处理话术列表

        Args:
            speech_configs: 话术配置列表
            data: 数据字典

        Returns:
            话术内容列表
        """
        if not speech_configs:
            return []

        results = []
        selected_in_group: Dict[str, Speech] = {}  # 互斥组已选择的话术

        # 遍历话术配置
        for speech in speech_configs:
            if speech.type == "fixed":
                # 固定话术，直接添加
                content = self._replace_speech_variables(speech.content, speech.variables, data)
                results.append(content)
                logger.debug(f"Added fixed speech: {speech.id}")
            elif speech.type == "conditional":
                # 条件话术，检查互斥组
                if speech.mutex_group:
                    # 检查是否已有同组话术被选中
                    if speech.mutex_group in selected_in_group:
                        # 已有话术，跳过当前话术
                        logger.debug(f"Skipped {speech.id}: group {speech.mutex_group} already has speech")
                        continue

                # 检查条件是否满足（这里简化处理，实际需要条件匹配）
                # 如果没有条件，默认满足
                if self._check_speech_conditions(speech, data):
                    content = self._replace_speech_variables(speech.content, speech.variables, data)
                    results.append(content)

                    if speech.mutex_group:
                        selected_in_group[speech.mutex_group] = speech
                        logger.debug(f"Selected speech {speech.id} for group {speech.mutex_group}")
                else:
                    logger.debug(f"Speech {speech.id} conditions not met")

        return results

    def _check_speech_conditions(
        self,
        speech: Speech,
        data: Dict[str, Any]
    ) -> bool:
        """检查话术条件是否满足

        简化实现：检查数据中是否包含话术ID对应的关键字
        """
        # 简化逻辑：如果话术没有明确条件配置，默认显示
        # 实际应该根据 speech 中的 conditions 字段判断
        if not hasattr(speech, 'conditions') or not speech.conditions:
            return True

        # 实际的条件检查
        return self.data_filler._match_conditions(data, speech.conditions)

    def _replace_speech_variables(
        self,
        content: str,
        variables: Dict[str, str],
        data: Dict[str, Any]
    ) -> str:
        """替换话术变量"""
        # 合并默认变量和自定义变量
        all_vars = {**self.DEFAULT_VARIABLES, **variables}

        # 从数据中获取变量值
        for var_name, default_value in all_vars.items():
            placeholder = f"{{{{{var_name}}}}}"
            if placeholder in content:
                # 优先使用传入的值
                value = data.get(var_name, default_value)
                content = content.replace(placeholder, str(value))

        return content

    def find_matching_speech(
        self,
        speeches: List[Speech],
        mutex_group: str,
        data: Dict[str, Any]
    ) -> Optional[Speech]:
        """查找匹配的话术（用于互斥组）

        Args:
            speeches: 话术列表
            mutex_group: 互斥组名称
            data: 数据字典

        Returns:
            匹配的话术或 None
        """
        for speech in speeches:
            if speech.mutex_group != mutex_group:
                continue

            if self._check_speech_conditions(speech, data):
                return speech

        return None
