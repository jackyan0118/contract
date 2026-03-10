"""规则加载服务 - 支持热更新和线程安全."""

import yaml
import logging
import threading
from pathlib import Path
from typing import List, Optional
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileSystemEvent

from src.models.template_rule import TemplateRule

logger = logging.getLogger(__name__)


class RuleLoadError(Exception):
    """规则加载异常"""
    pass


class RuleLoader:
    """规则加载服务 - 线程安全，支持热更新"""

    def __init__(self, rule_file: str = "config/template_rules.yaml"):
        self.rule_file = Path(rule_file)
        self._rules: List[TemplateRule] = []
        self._observer: Optional[Observer] = None
        self._lock = threading.RLock()
        self._backup_rules: List[TemplateRule] = []

    def load(self) -> List[TemplateRule]:
        """加载规则文件

        Raises:
            RuleLoadError: 文件不存在或格式错误
        """
        logger.info(f"Loading rules from {self.rule_file}")

        if not self.rule_file.exists():
            raise RuleLoadError(f"Rule file not found: {self.rule_file}")

        try:
            with open(self.rule_file, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
        except yaml.YAMLError as e:
            raise RuleLoadError(f"Invalid YAML format: {e}")

        rules_data = data.get('模板规则', [])
        self._rules = [TemplateRule(**rule) for rule in rules_data]
        logger.info(f"Loaded {len(self._rules)} template rules")
        return self._rules

    def reload(self):
        """重新加载规则（带锁保护，失败时回滚）"""
        with self._lock:
            logger.info("Reloading template rules...")
            # 备份当前规则
            self._backup_rules = self._rules.copy()

            try:
                self.load()
                logger.info("Template rules reloaded successfully")
                # 清空备份
                self._backup_rules = []
            except Exception as e:
                logger.error(f"Failed to reload rules: {e}")
                # 回滚到旧规则
                self._rules = self._backup_rules
                self._backup_rules = []
                raise

    def get_rules(self) -> List[TemplateRule]:
        """获取已加载的规则"""
        with self._lock:
            return self._rules.copy()

    def start_watching(self):
        """启动文件监听（热更新）"""
        if self._observer is not None:
            return

        event_handler = RuleFileHandler(self)
        self._observer = Observer()
        self._observer.schedule(event_handler, str(self.rule_file.parent), recursive=False)
        self._observer.start()
        logger.info(f"Started watching {self.rule_file} for changes")

    def stop_watching(self):
        """停止文件监听"""
        if self._observer:
            self._observer.stop()
            self._observer.join()
            self._observer = None
            logger.info("Stopped watching rule file")


class RuleFileHandler(FileSystemEventHandler):
    """规则文件变化处理器 - 带防抖机制"""

    DEBOUNCE_SECONDS = 1.0  # 防抖延迟时间

    def __init__(self, loader: RuleLoader):
        self.loader = loader
        self._debounce_timer: Optional[threading.Timer] = None

    def on_modified(self, event: FileSystemEvent):
        if event.src_path != str(self.loader.rule_file):
            return

        # 取消之前的定时器
        if self._debounce_timer:
            self._debounce_timer.cancel()

        # 设置新的定时器（防抖）
        self._debounce_timer = threading.Timer(
            self.DEBOUNCE_SECONDS,
            self._do_reload
        )
        self._debounce_timer.start()

    def _do_reload(self):
        """执行重载"""
        logger.warning(f"Rule file changed, reloading...")
        try:
            self.loader.reload()
        except Exception as e:
            logger.error(f"Failed to reload rules: {e}")
