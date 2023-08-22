# -*- coding:utf-8 -*-

# @Time   : 2023/8/11 09:21
# @Author : huangkewei

import re
import orjson
import string
import random
import time
import tiktoken
import httpx
from typing import List
from fastapi import Request
from data_stream_kit import AIOProducer
from orjson import JSONDecodeError

from app.dependencies.context import OpenaiContext
from app.utils.logs import logger
from app.utils.exception import RequestException
from app.utils.conf import KAFKA_URI, KAFKA_OPENAI_TOPIC, SAVE_LOG


path_azure = re.compile(r'/openai/deployments/.*?/')


async def aiter_bytes(r: httpx.Response, ctx: OpenaiContext):
    """
    处理响应之后的内容
    """
    url = ctx.req_params['url']
    key_type = ctx.key_type

    bytes_ = b""
    if key_type == 'baidu':
        baidu_id = generate_random_string(32)
        async for chunk in r.aiter_bytes():
            if not ctx.first_time:
                ctx.first_time = time.perf_counter()

            chunk_new_gen = baidu_api_res_to_openai(chunk, baidu_id)
            for chunk_new in chunk_new_gen:
                bytes_ += chunk_new
                yield chunk_new
        del_baidu_res_map(baidu_id)
    elif key_type == 'huawei':
        huawei_id = generate_random_string(32)
        async for chunk in r.aiter_bytes():
            if not ctx.first_time:
                ctx.first_time = time.perf_counter()

            chunk_new_gen = huawei_api_res_to_openai(chunk, huawei_id)
            for chunk_new in chunk_new_gen:
                bytes_ += chunk_new
                yield chunk_new
        del_huawei_res_map(huawei_id)
    else:
        async for chunk in r.aiter_bytes():
            if not ctx.first_time:
                ctx.first_time = time.perf_counter()

            bytes_ += chunk
            yield chunk

    ctx.all_time = time.perf_counter()

    logger.info(f"forward_key: {ctx.forward_key}. 请求完成。")
    ctx.res_content = bytes_.decode()

    try:
        ctx_info = get_context_info(ctx)
        await producer(ctx_info)
    except Exception as e:
        logger.exception(e)


async def parse_request(request: Request):
    """
    解析request，openai类型的参数。

    :param request:

    :return:
    """
    url_path = request.url.path
    if not url_path.startswith('/v1'):
        url_path = '/v1' + url_path

    body = orjson.loads(await request.body())

    openai_params = {
        'url_path': url_path,
        'body': body
    }

    return openai_params


async def parse_azure_request(request: Request):
    """
    解析request，openai类型的参数。

    :param request:

    :return:
    """
    url_path = request.url.path
    url_path = re.sub(path_azure, '/', url_path)
    if not url_path.startswith('/v1'):
        url_path = '/v1' + url_path

    body = orjson.loads(await request.body())

    openai_params = {
        'url_path': url_path,
        'body': body
    }

    return openai_params


def token_count(text, model_name='gpt-3.5-turbo'):
    """
    计算一段文本的使用的token数
    :param text:
    :param model_name:
    :return:
    """
    if not text:
        return

    enc = tiktoken.encoding_for_model(model_name)

    tokens = len(enc.encode(text))
    return tokens


def choose_one_key(keys: List[dict], params: dict, model_map=None):
    """
    选择一个可用key
    """
    if model_map:
        key = choose_appoint_model_one_key(model_map, keys, params)
        if key:
            return key

    model = params.get('body').get('model')

    if model:
        model_info = model.split('/')

        if len(model_info) == 2:
            model = model_info[0]
            api_type = model_info[1]
            params['body']['model'] = model

            return choose_appoint_one_key(api_type, keys, params)

    url_path = params.get('url_path')

    token = 0
    use_type = ''
    if 'chat/completions' in url_path:
        messages = params.get('body').get('messages')
        msg_text = ''.join([d['content'] for d in messages])
        token = token_count(msg_text)

        use_type = 'chat'
    elif 'embeddings' in url_path:
        use_type = 'embeddings'

    if token > 2000:
        use_16k = True
    else:
        use_16k = False

    allow_keys = []
    for key in keys:
        models = key.get('model').split(',')
        engine = key.get('engine').split(',')
        model_info = list(zip(models, engine))
        if use_type == 'embeddings':
            model_info = [(m, e) for m, e in model_info if 'embedding' in m]
        elif use_type == 'chat':
            if use_16k:
                model_info = [
                    (m, e) for m, e in model_info
                    if '16k' in m and 'embedding' not in m
                ]
            else:
                model_info = [
                    (m, e) for m, e in model_info
                    if '16k' not in m and 'embedding' not in m
                ]

        if not model_info:
            continue

        key['model'] = model_info[0][0]  # [m for m, e in model_info]
        key['engine'] = model_info[0][1]  # [e for m, e in model_info]
        allow_keys.append(key)

    one_key = allow_keys[random.randint(0, len(allow_keys)-1)]

    return one_key


def choose_appoint_model_one_key(model_map: dict, keys: List[dict], params: dict):
    """
    从model map中选择一个可用key
    """
    model = params.get('body').get('model')
    new_mode = model_map.get(model)
    if not new_mode:
        return

    keys = [
        k for k in keys
        if new_mode in k['model']
    ]

    one_key = keys[random.randint(0, len(keys) - 1)]

    models = one_key.get('model').split(',')
    engine = one_key.get('engine').split(',')
    model_info = list(zip(models, engine))
    for m, e in model_info:
        if m == new_mode:
            one_key['model'] = m
            one_key['engine'] = e

    return one_key


def choose_appoint_one_key(api_type: str, keys: List[dict], params: dict):
    """
    从一个可用区，选择一个可用key
    """
    model = params.get('body').get('model')

    keys = [
        k for k in keys
        if k['api_type'] == api_type and model in k['model']
    ]

    if not keys:
        raise RequestException(detail="没有可用指定类型的key!")

    one_key = keys[random.randint(0, len(keys) - 1)]

    models = one_key.get('model').split(',')
    engine = one_key.get('engine').split(',')
    model_info = list(zip(models, engine))
    for m, e in model_info:
        if m == model:
            one_key['model'] = m
            one_key['engine'] = e

    return one_key


def retry_decorator(retry_times=3, retry_exception=Exception):
    """
    重试修饰器
    :param retry_times: 重试次数
    :param retry_exception: 重试异常, 单个异常或者元组
    :return:
    """

    def _decorator(func):
        async def _wrapper(*args, **kwargs):
            for _ in range(retry_times):
                try:
                    return await func(*args, **kwargs)
                except retry_exception as e:
                    continue
            raise e

        return _wrapper

    return _decorator


# 缓存百度请求，解决由于tcp导致上下文被截断。
baidu_res_map = {}


def baidu_api_res_to_openai(res: bytes, baidu_id):
    res = res.decode()

    baidu_res_lst = baidu_res_map.get(baidu_id, [])
    baidu_res = ''.join(baidu_res_lst)
    baidu_res += res

    baidu_res_all = baidu_res.split('data:')
    baidu_res_all = [d.strip() for d in baidu_res_all if d.strip()]

    baidu_res_map[baidu_id] = []
    for _res in baidu_res_all:
        try:
            result = orjson.loads(_res)
            context = result['result']
            openai_res = {
                'created': result['created'],
                'id': result['id'],
                'object': result['object'],
                'choices': [{
                    'delta': {'content': context, 'role': 'assistant'},
                    'finish_reason': None,
                    'index': result['sentence_id']
                }],
                'usage': result['usage']
            }
            yield b'data: ' + orjson.dumps(openai_res) + b'\n'
        except JSONDecodeError:
            baidu_res_map[baidu_id].append(res)
        except Exception:
            raise RequestException(detail=_res)


def del_baidu_res_map(baidu_id):
    if baidu_id in baidu_res_map:
        del baidu_res_map[baidu_id]


letters = string.ascii_letters + string.digits  # 包含大小写字母和数字的所有字符


def generate_random_string(length):
    # 生成随机字符串
    random_string = ''.join(random.choice(letters) for _ in range(length))
    return random_string


def get_context_info(ctx: OpenaiContext):
    # 格式化上下文
    tmp = {
        'forward_key': ctx.forward_key,
        'openai_key': ctx.openai_key,
        'model_name': ctx.model_name,
        'req_params': ctx.req_params,
        'res_content': ctx.res_content,

        'start_time': ctx.start_time,
        'deal_time': ctx.deal_time,
        'first_time': ctx.first_time,
        'all_time': ctx.all_time,

        'retry_times': ctx.retry_times,
    }
    tmp = orjson.dumps(tmp).decode()

    return tmp


class AIOProducerLog:
    # 异步kafka生产者
    def __init__(self):
        self.aio_producer = None

    async def producer(self, value=None):
        if not SAVE_LOG:
            return

        try:
            if not self.aio_producer:
                self.aio_producer = AIOProducer(bootstrap_servers=KAFKA_URI, topic=KAFKA_OPENAI_TOPIC)

            if isinstance(value, (dict, list)):
                value = orjson.dumps(value).decode()

            await self.aio_producer.publish(value=value)

            logger.info('信息发送kafka成功！')
        except Exception as e:
            # 不影响整个流程
            logger.exception(e)


aio_producer_log = AIOProducerLog()
producer = aio_producer_log.producer


async def send_error_msg(ctx: OpenaiContext, error: str):
    # 发送错误日志
    error_info = {}
    ctx_info = get_context_info(ctx)
    error_info['ctx'] = ctx_info
    error_info['error'] = error

    error_info = orjson.dumps(error_info).decode()
    await producer(error_info)

# 缓存华为请求，解决由于tcp导致上下文被截断。
huawei_res_map = {}
huawei_split = re.compile('data:|event:')


def huawei_api_res_to_openai(res: bytes, huawei_id):
    res = res.decode()

    huawei_res_lst = huawei_res_map.get(huawei_id, [])
    huawei_res = ''.join(huawei_res_lst)
    huawei_res += res

    huawei_res_all = re.split(huawei_split, huawei_res)
    huawei_res_all = [d.strip() for d in huawei_res_all if d.strip()]

    huawei_res_map[huawei_id] = []
    for _res in huawei_res_all:
        try:
            if _res == '[DONE]':
                continue

            result = orjson.loads(_res)
            if 'token_number' in result:
                continue

            choices = result['choices'][0]
            context = (
                choices.get('text', '') or
                choices.get('message', {}).get('content', '')
            )

            openai_res = {
                'created': result['created'],
                'id': result['id'],
                'choices': [{
                    'delta': {'content': context, 'role': 'assistant'},
                    'finish_reason': None
                }]
            }
            yield b'data: ' + orjson.dumps(openai_res) + b'\n'
        except JSONDecodeError:
            huawei_res_map[huawei_id].append(res)
        except Exception:
            raise RequestException(detail=_res)


def del_huawei_res_map(huawei_id):
    if huawei_id in huawei_res_map:
        del huawei_res_map[huawei_id]
