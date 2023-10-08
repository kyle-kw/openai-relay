# -*- coding:utf-8 -*-

# @Time   : 2023/8/16 17:59
# @Author : huangkewei

from urllib.parse import urljoin

from app.utils.logs import logger
from app.utils.magic_number import APIType
from app.utils.exception import InternalException
from app.utils.platforms import pangu_distribute, zhipu_chat, qwen_chat, baidu_chat


def main_distribute(key, req_params):
    api_type = judge_key_type(key)

    if api_type in [APIType.OpenAI, APIType.Self]:
        return openai_distribute(key, req_params)
    elif api_type == APIType.Azure:
        return azure_distribute(key, req_params)
    elif api_type == APIType.Baidu:
        return baidu_distribute(key, req_params)
    elif api_type == APIType.Huawei:
        return huawei_distribute(key, req_params)
    elif api_type == APIType.Xunfei:
        return xunfei_distribute(key, req_params)
    elif api_type == APIType.Qinghua:
        return qinghua_distribute(key, req_params)
    elif api_type == APIType.Ali:
        return ali_distribute(key, req_params)


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
    elif key_type == 'xunfei':
        return APIType.Xunfei
    elif key_type == 'qinghua':
        return APIType.Qinghua
    elif key_type == 'ali':
        return APIType.Ali
    elif key_type == 'self':
        return APIType.Self

    raise InternalException(detail='api类型异常！')


def openai_distribute(key: dict, req_params: dict):
    api_key = key.get('api_key')
    api_base = key.get('api_base')
    model = key.get('model')

    url_path: str = req_params.get('url_path')
    body = req_params.get('body')
    body['model'] = model

    if url_path.startswith('/v1//'):
        url_path = '/v1/' + url_path[5:]

    if (('max_tokens' not in body or not body['max_tokens']) and
            model in ['jfh-bot-32k-chat', 'jfh-coder-34b',
                      'jfh-bot-13b-chat', 'jfh-bot-7b']):
        body['max_tokens'] = 500

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
    params = req_params.get('body')

    req_new = baidu_chat(api_key, model, params)

    return req_new


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
        if 'temperature' in data_new:
            data_new['temperature'] = min(max(data_new['temperature'], 0.1), 1)

        data_new['prompt'] = '\n'.join([d['content'] for d in body['messages']])
        if 'max_tokens' in data_new:
            data_new['max_tokens'] = min(max(data_new['max_tokens'], 1000), 4096)

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
        if 'temperature' in data_new:
            data_new['temperature'] = min(max(data_new['temperature'], 0.1), 1)

        if 'max_tokens' in data_new:
            data_new['max_tokens'] = min(max(data_new['max_tokens'], 1000), 2000)

    req_new = pangu_distribute(ak, sk, url, data_new)

    return req_new


def xunfei_distribute(key, req_params):
    api_key = key.get('api_key')
    model = key.get('model')
    appid, api_secret, api_key_ = api_key.split('/')

    if model == 'general':
        spark_url = 'wss://spark-api.xf-yun.com/v1.1/chat'
    elif model == 'generalv2':
        spark_url = 'wss://spark-api.xf-yun.com/v2.1/chat'
    else:
        spark_url = ''

    body = req_params.get('body')
    question = body.get('messages')

    if question[0]['role'] == 'system':
        if len(question) == 1:
            question.append({'role': 'user', 'content': ''})
        question[1]['content'] = question[0]['content'] + '\n' + question[1]['content']
        question.pop(0)

    allow_keys = ['random_threshold', 'temperature', 'max_tokens', 'auditing', 'top_k', 'chat_id']
    chat_param = {
        k: v for k, v in body.items()
        if k in allow_keys
    }
    if 'max_tokens' in chat_param:
        chat_param['max_tokens'] = min(max(chat_param['max_tokens'], 1000), 4096)

    if 'temperature' in chat_param:
        chat_param['temperature'] = min(max(chat_param['temperature'], 0.1), 1)

    ws_new = {
        'appid': appid,
        'api_key': api_key_,
        'api_secret': api_secret,
        'spark_url': spark_url,
        'domain': model,
        'question': question,
        'chat_param': chat_param,
    }

    return ws_new


def qinghua_distribute(key, req_params):
    api_key = key.get('api_key')
    model = key.get('model')

    body = req_params.get('body')
    messages = body.get('messages')

    if messages[0]['role'] == 'system':
        if len(messages) == 1:
            messages.append({'role': 'user', 'content': ''})
        messages[1]['content'] = messages[0]['content'] + '\n' + messages[1]['content']
        messages.pop(0)

    allow_keys = ['prompt', 'temperature', 'top_p', 'request_id', 'incremental']
    chat_param = {
        k: v for k, v in body.items()
        if k in allow_keys
    }
    chat_param['prompt'] = messages

    if 'temperature' in chat_param:
        chat_param['temperature'] = min(max(chat_param['temperature'], 0.1), 1)

    if 'top_p' in chat_param:
        chat_param['top_p'] = min(max(chat_param['top_p'], 0.1), 0.9)

    req_new = zhipu_chat(api_key, model, chat_param)

    return req_new


def ali_distribute(key, req_params):
    api_key = key.get('api_key')
    model = key.get('model')

    body = req_params.get('body')
    messages = body.get('messages')

    allow_keys = ['temperature', 'seed', 'stream', 'top_k', 'enable_search', 'result_format']
    chat_param = {
        k: v for k, v in body.items()
        if k in allow_keys
    }

    if 'temperature' in chat_param:
        chat_param['temperature'] = min(max(chat_param['temperature'], 0.01), 1)

    if 'top_p' in chat_param:
        chat_param['top_p'] = min(max(chat_param['top_p'], 1), 100)

    if 'seed' in chat_param:
        chat_param['seed'] = min(max(chat_param['seed'], 1), 65535)

    req_new = qwen_chat(api_key, messages, model, chat_param)

    return req_new
