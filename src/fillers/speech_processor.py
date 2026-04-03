"""话术处理器 - 处理话术逻辑和互斥组."""

import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum

from src.fillers.data_filler import DataFiller, FilterCondition
from src.fillers.constants import DEFAULT_SPEECH_VARIABLES

logger = logging.getLogger(__name__)


class SpeechType(str, Enum):
    """话术类型枚举"""

    CONDITIONAL = "conditional"
    FIXED = "fixed"


@dataclass
class Speech:
    """话术"""

    id: str
    content: str
    type: SpeechType = SpeechType.CONDITIONAL
    mutex_group: Optional[str] = None
    variables: Dict[str, str] = field(default_factory=dict)
    conditions: List[FilterCondition] = field(default_factory=list)


class SpeechProcessor:
    """话术处理器"""

    # 默认话术变量（从 constants 导入）
    DEFAULT_VARIABLES = DEFAULT_SPEECH_VARIABLES

    def __init__(self):
        self.data_filler = DataFiller()

    def process_speeches(
        self, speech_configs: List[Speech], detail_data_list: List[Dict[str, Any]]
    ) -> List[str]:
        """处理话术列表

        Args:
            speech_configs: 话术配置列表
            detail_data_list: 明细数据列表（用于话术条件判断）

        Returns:
            话术内容列表
        """
        if not speech_configs:
            return []

        results = []
        selected_in_group: Dict[str, Speech] = {}  # 互斥组已选择的话术
        speech_index = 0  # 话术序号计数器
        number_symbols = ["①", "②", "③", "④", "⑤", "⑥", "⑦", "⑧", "⑨", "⑩"]

        # 遍历话术配置，先计算最终会有多少条话术
        temp_selected = {}
        for speech in speech_configs:
            if speech.type == "fixed":
                continue
            if speech.mutex_group:
                if speech.mutex_group in temp_selected:
                    continue
            if self._check_speech_conditions(speech, detail_data_list):
                temp_selected[speech.mutex_group or speech.id] = True

        final_speech_count = len(temp_selected) + sum(
            1 for s in speech_configs if s.type == "fixed"
        )
        add_number_prefix = final_speech_count > 1  # 只有多条话术时才加序号

        # 遍历话术配置
        for speech in speech_configs:
            if speech.type == "fixed":
                # 固定话术，直接添加（不使用条件判断）
                content = self._replace_speech_variables(speech.content, speech.variables, {})
                # 添加序号前缀
                if add_number_prefix and speech_index < len(number_symbols):
                    content = f"{number_symbols[speech_index]} {content}"
                speech_index += 1
                results.append(content)
                logger.debug(f"Added fixed speech: {speech.id}")
            elif speech.type == "conditional":
                # 条件话术，检查互斥组
                if speech.mutex_group:
                    # 检查是否已有同组话术被选中
                    if speech.mutex_group in selected_in_group:
                        # 已有话术，跳过当前话术
                        logger.debug(
                            f"Skipped {speech.id}: group {speech.mutex_group} already has speech"
                        )
                        continue

                # 检查条件是否满足：任意一条明细满足则匹配
                if self._check_speech_conditions(speech, detail_data_list):
                    content = self._replace_speech_variables(speech.content, speech.variables, {})
                    # 添加序号前缀
                    if add_number_prefix and speech_index < len(number_symbols):
                        content = f"{number_symbols[speech_index]} {content}"
                    speech_index += 1
                    results.append(content)

                    if speech.mutex_group:
                        selected_in_group[speech.mutex_group] = speech
                        logger.debug(f"Selected speech {speech.id} for group {speech.mutex_group}")
                else:
                    logger.debug(f"Speech {speech.id} conditions not met")

        return results

    def _check_speech_conditions(
        self, speech: Speech, detail_data_list: List[Dict[str, Any]]
    ) -> bool:
        """检查话术条件是否满足

        Args:
            speech: 话术对象
            detail_data_list: 明细数据列表

        Returns:
            任意一条明细满足条件则返回 True
        """
        # 如果话术没有明确条件配置，默认显示
        if not hasattr(speech, "conditions") or not speech.conditions:
            return True

        # 遍历明细数据，任意一条满足条件则匹配
        for data in detail_data_list:
            if self.data_filler.match_conditions(data, speech.conditions):
                return True

        return False

    def _replace_speech_variables(
        self, content: str, variables: Dict[str, str], data: Dict[str, Any]
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
        self, speeches: List[Speech], mutex_group: str, detail_data_list: List[Dict[str, Any]]
    ) -> Optional[Speech]:
        """查找匹配的话术（用于互斥组）

        Args:
            speeches: 话术列表
            mutex_group: 互斥组名称
            detail_data_list: 明细数据列表

        Returns:
            匹配的话术或 None
        """
        for speech in speeches:
            if speech.mutex_group != mutex_group:
                continue

            if self._check_speech_conditions(speech, detail_data_list):
                return speech

        return None
