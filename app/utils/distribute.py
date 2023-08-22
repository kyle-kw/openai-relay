# -*- coding:utf-8 -*-

# @Time   : 2023/8/16 17:59
# @Author : huangkewei

import time
import httpx
from urllib.parse import urljoin

from app.utils.logs import logger
from app.utils.magic_number import APIType
from app.utils.exception import InternalException, RequestException
from app.utils.huawei_sdk.pangu_api import pangu_distribute


def main_distribute(key, req_params):
    api_type = judge_key_type(key)

    if api_type == APIType.OpenAI:
        return openai_distribute(key, req_params)
    elif api_type == APIType.Azure:
        return azure_distribute(key, req_params)
    elif api_type == APIType.Baidu:
        return baidu_distribute(key, req_params)
    elif api_type == APIType.Huawei:
        return huawei_distribute(key, req_params)


def judge_key_type(key) -> APIType:
    key_type = key.get('api_type')
    if key_type == 'open_ai':
        return APIType.OpenAI
    elif key_type == 'azure':
        return APIType.Azure
    elif key_type == 'baidu':
        return APIType.Baidu
    elif key_type == 'huawei':
        return APIType.Huawei

    raise InternalException(detail='api类型异常！')


def openai_distribute(key: dict, req_params: dict):
    api_key = key.get('api_key')
    api_base = key.get('api_base')
    model = key.get('model')

    url_path: str = req_params.get('url_path')
    body = req_params.get('body')
    body['model'] = model

    full_url = urljoin(api_base, url_path)

    headers = {
        "Content-Type": "application/json",
        "Connection": "keep-alive",
        "Authorization": "Bearer " + api_key
    }

    req_new = {
        'method': 'POST',
        'url': full_url,
        'headers': headers,
        'json': body,
    }

    return req_new


def azure_distribute(key, req_params):
    api_key = key.get('api_key')
    api_base = key.get('api_base')
    api_version = key.get('api_version')
    model = key.get('model')
    engine = key.get('engine')

    url_path: str = req_params.get('url_path')
    body = req_params.get('body')
    body.pop('model', '')

    url_path = url_path.replace('v1', 'openai/deployments/'+engine)
    full_url = urljoin(api_base, url_path)

    params = {
        'api-version': api_version
    }
    headers = {
        "Content-Type": "application/json",
        "Connection": "keep-alive",
        "api-key": api_key
    }

    req_new = {
        'method': 'POST',
        'url': full_url,
        'params': params,
        'headers': headers,
        'json': body,
    }

    return req_new


def baidu_distribute(key, req_params):
    api_key = key.get('api_key')
    model = key.get('model')

    access_keys = api_key.split('/')
    access_token = get_access_token(*access_keys)

    body = req_params.get('body')

    if model == 'ERNIE-Bot-turbo':
        url = 'https://aip.baidubce.com/rpc/2.0/ai_custom/v1/wenxinworkshop/chat/eb-instant'  # ERNIE-Bot-turbo
    elif model == 'ERNIE-Bot':
        url = 'https://aip.baidubce.com/rpc/2.0/ai_custom/v1/wenxinworkshop/chat/completions'  # ERNIE-Bot
    else:  # if model == 'BLOOMZ-7B':
        url = 'https://aip.baidubce.com/rpc/2.0/ai_custom/v1/wenxinworkshop/chat/bloomz_7b1'  # BLOOMZ-7B

    # 目前百度支持的参数
    allow_keys = ['messages', 'temperature', 'top_p', 'penalty_score', 'stream', 'user_id']
    data_new = {
        k: v for k, v in body.items()
        if k in allow_keys
    }

    # 百度msg需要处理
    temperature = data_new.get('temperature')
    if temperature is not None and str(temperature) == '0.0':
        data_new['temperature'] = 0.1

    messages: list = data_new.get('messages')
    if not messages:
        raise RequestException(detail='baidu 没有可用信息!')

    if messages[0]['role'] == 'system':
        messages[1]['content'] = messages[0]['content'] + '\n' + messages[1]['content']
        messages.pop(0)

    messages_new = []
    for msg in messages:
        if not messages_new:
            messages_new.append(msg)
            continue
        if msg['role'] == messages_new[-1]['role']:
            messages_new[-1]['content'] += msg['content']
        else:
            messages_new.append(msg)

    if len(messages_new) % 2 == 0:
        raise RequestException(detail='baidu 信息个数必须为奇数。')

    data_new['messages'] = messages_new

    params = {
        'access_token': access_token
    }
    headers = {
        'Content-Type': 'application/json'
    }
    req_new = {
        'method': 'POST',
        'url': url,
        'params': params,
        'headers': headers,
        'json': data_new,
    }

    return req_new


access_token_cache = {
    'last_time': 0.0,
    'access_token': ''
}


def cache_decorator(cache_time=300):
    """
    缓存修饰器
    :param cache_time: 缓存时间，默认300s

    :return:
    """

    def _decorator(func):
        def _wrapper(*args, **kwargs):
            last_time = access_token_cache.get('last_time')
            access_token = access_token_cache.get('access_token')

            if not access_token or time.time()-last_time > cache_time:
                access_token = access_token_cache['access_token'] = func(*args, **kwargs)
                access_token_cache['last_time'] = time.time()

            return access_token

        return _wrapper

    return _decorator


@cache_decorator()
def get_access_token(grant_type, client_id, client_secret) -> str:
    """
    使用 API Key，Secret Key 获取access_token
    """

    url = "https://aip.baidubce.com/oauth/2.0/token"

    params = {
        'grant_type': grant_type,
        'client_id': client_id,  # API Key
        'client_secret': client_secret,  # Secret Key
    }

    headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json'
    }

    response = httpx.request("POST", url, headers=headers, params=params)

    return response.json().get("access_token")


def huawei_distribute(key, req_params):
    api_key = key.get('api_key')
    ak, sk, project_id, deployment_id = api_key.split('/')

    api_base = key.get('api_base')

    model = key.get('model')
    if model == 'pangu-text':
        url_path = f'/v1/{project_id}/deployments/{deployment_id}/text/completions'
        url = api_base + url_path

        body = req_params.get('body')
        allow_keys = ['prompt', 'user', 'temperature', 'top_p', 'max_tokens', 'n',
                      'presence_penalty', 'stream']
        data_new = {
            k: v for k, v in body.items()
            if k in allow_keys
        }

        data_new['prompt'] = '\n'.join([d['content'] for d in body['messages']])
        if 'max_tokens' in data_new:
            data_new['max_tokens'] = 2000 if data_new['max_tokens'] > 2000 else data_new['max_tokens']

    elif model == 'pangu-chat':
        url_path = f'/v1/{project_id}/deployments/{deployment_id}/chat/completions'
        url = api_base + url_path

        body = req_params.get('body')
        allow_keys = ['messages', 'user', 'temperature', 'top_p', 'max_tokens', 'n',
                      'presence_penalty', 'stream']
        data_new = {
            k: v for k, v in body.items()
            if k in allow_keys
        }

        if 'max_tokens' in data_new:
            data_new['max_tokens'] = 2000 if data_new['max_tokens'] > 2000 else data_new['max_tokens']

    req_new = pangu_distribute(ak, sk, url, data_new)

    return req_new
