import os
import logging
from datetime import datetime


class Logger:
    """
    日志类，记录多个模块的信息
    """

    def __init__(self, log_path):
        # 目录不存在则创建
        self.path = log_path
        os.makedirs(self.path, exist_ok=True)

        # 定义handler的输出格式
        self.formatter = logging.Formatter('[%(asctime)s] [%(levelname)s] [%(class_name)s.%(func_name)s] [%(url_name)s] %(message)s',
                                           '%Y-%m-%d %H:%M:%S')

        # 创建一个logger
        self.logger = None

        # 日志文件、控制台 handler
        self.console_handler = None
        self.file_handler = None

    def get_logger(self, name) -> logging.Logger:
        # 文件处理
        log_file = os.path.join(self.path, f"{datetime.now().strftime('%Y-%m-%d')}_{name}.log")
        self.file_handler = logging.FileHandler(log_file)
        self.file_handler.setFormatter(self.formatter)

        # 控制台
        self.console_handler = logging.StreamHandler()
        self.console_handler.setLevel('DEBUG')
        self.console_handler.setFormatter(self.formatter)

        # 返回
        self.logger = logging.getLogger(name)
        self.logger.setLevel(getattr(logging, name.upper()))  # 设置日志级别
        self.logger.addHandler(self.file_handler)
        self.logger.addHandler(self.console_handler)

        return self.logger
