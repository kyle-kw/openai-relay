# -*- coding:utf-8 -*-

# @Time   : 2023/7/13 13:57
# @Author : huangkewei

import openai
import threading
import time
import logging

# logging.basicConfig(
#     level=logging.INFO,
#     format='[%(levelname)s] %(asctime)s - %(filename)s func:%(funcName)s line: %(lineno)d - %(message)s'
# )
logger = logging.getLogger(__name__)


def run_demo():
    stream = True
    msg = [
        {'role': 'user', 'content': '你是谁？'},
    ]
    kwargs = {
        'api_key': 'fd-TijSXUYDckHFoEwuqrIrKOoJ9WXR7hOJRDhfXoujKlYVmq2',
        'api_base': 'http://localhost:8000/v1',
        'model': 'gpt-35-turbo',
        # 可以指定平台
        # 'model': 'gpt-35-turbo/azure',

        # 兼容azure请求
        # 'api_type': 'azure',
        # 'api_version': '2023-05-15',
        # 'engine': 'zhongbiao-gpt-35-turbo-16k',

        'messages': msg,
        'temperature': 0.8,
        'max_tokens': 3000,
        'presence_penalty': 1,
        'n': 1,
        'timeout': 10,
        'stop': None,
        'top_p': 1,
        'stream': stream
    }

    now = time.time()
    logger.info(f'{threading.get_native_id()} start time: {now}')
    responses = openai.ChatCompletion.create(**kwargs)
    logger.info(f'{threading.get_native_id()} first return time: {time.time()-now}')

    if stream:
        for response in responses:
            resp_json = response.to_dict_recursive()
            choice = resp_json['choices'][0] or {}
            finish_reason = choice.get('finish_reason')
            if finish_reason:
                # 判断流式输出是否结束
                pass
            delta = choice.get('delta') or {}

            content = delta.get('content') or ''
            if content:
                print(content, end='')
        print()
    else:
        print(responses)

    logger.info(f'{threading.get_native_id()} end return time: {time.time() - now}')


def run_the():
    # 多线程调用测试
    logger.info('------- start -----------')
    now = time.time()
    task = []
    for _ in range(5):
        t = threading.Thread(target=run_demo)
        t.start()
        task.append(t)

    for t in task:
        t.join()

    logger.info('------- end -----------')
    logger.info(f'请求用时： {time.time() - now}')


if __name__ == '__main__':
    run_demo()
    # run_the()
