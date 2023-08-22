# -*- coding:utf-8 -*-

# @Time   : 2023/8/15 15:14
# @Author : huangkewei


class OpenaiContext:
    """
    用于记录请求，发送请求相关的信息
    """

    def __init__(self):
        self.forward_key = ''
        self.openai_key = ''
        self.key_used = None
        self.key = None
        self.key_type = ''
        self.model_map = None
        self.model_name = ''

        self.req_params = None
        self.res_content = None

        self.start_time = 0.0
        self.deal_time = 0.0
        self.first_time = 0.0
        self.all_time = 0.0

        self.retry_times = 0


def get_context():
    return OpenaiContext()
