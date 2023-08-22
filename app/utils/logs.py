# -*- coding:utf-8 -*-

# @Time   : 2023/8/18 13:36
# @Author : huangkewei

import os
import logging
from logging.handlers import RotatingFileHandler
from app.utils.conf import LOG_PATH, LOG_LEVEL


# 创建一个日志器，就是一个logger对象
logger = logging.getLogger()
logger.setLevel(LOG_LEVEL)

log_file = f'{LOG_PATH}/app.log'
if not os.path.exists(LOG_PATH):
    os.makedirs(LOG_PATH)

# 创建文件处理程序
file_handler = RotatingFileHandler(filename=log_file, maxBytes=10 * 1024 * 1024, backupCount=10)

# 创建格式化器
log_format = '[%(levelname)s] %(asctime)s - %(filename)s func:%(funcName)s line: %(lineno)d - %(message)s'
formatter = logging.Formatter(log_format)

# 将格式化器添加到处理程序
file_handler.setFormatter(formatter)

# 创建终端打印处理器
console_handler = logging.StreamHandler()
console_handler.setFormatter(formatter)

# 将处理器添加到日志器中
logger.addHandler(file_handler)
logger.addHandler(console_handler)

