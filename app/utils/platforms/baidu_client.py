# -*- coding:utf-8 -*-

# @Time   : 2023/9/22 14:32
# @Author : huangkewei

import httpx
import cachetools.func
from app.utils.exception import RequestException


API_TOKEN_TTL_SECONDS = 3 * 60

CACHE_TTL_SECONDS = API_TOKEN_TTL_SECONDS - 30


@cachetools.func.ttl_cache(maxsize=10, ttl=CACHE_TTL_SECONDS)
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


def baidu_chat(api_key, model, params):
    access_keys = api_key.split('/')
    access_token = get_access_token(*access_keys)

    if model == 'ERNIE-Bot-turbo':
        url = 'https://aip.baidubce.com/rpc/2.0/ai_custom/v1/wenxinworkshop/chat/eb-instant'
    elif model == 'ERNIE-Bot':
        url = 'https://aip.baidubce.com/rpc/2.0/ai_custom/v1/wenxinworkshop/chat/completions'
    elif model == 'BLOOMZ-7B':
        url = 'https://aip.baidubce.com/rpc/2.0/ai_custom/v1/wenxinworkshop/chat/bloomz_7b1'
    else:
        raise RequestException(detail='baidu model类型错误！')

    # 目前百度支持的参数
    allow_keys = ['messages', 'temperature', 'top_p', 'penalty_score', 'stream', 'user_id']
    data_new = {
        k: v for k, v in params.items()
        if k in allow_keys
    }

    # 百度msg需要处理
    if 'temperature' in data_new:
        data_new['temperature'] = min(max(data_new['temperature'], 0.01), 1)

    messages = data_new.get('messages')
    if messages[0]['role'] == 'system':
        if len(messages) == 1:
            messages.append({'role': 'user', 'content': ''})
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


