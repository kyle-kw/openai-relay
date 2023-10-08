# -*- coding:utf-8 -*-

# @Time   : 2023/9/22 10:56
# @Author : huangkewei


import orjson
import random
import json
import asyncio
import httpx


def qwen_chat(api_key, messages, model, param=None):
    url = 'https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation'

    json_data = {
        "model": model,  # qwen-turbo,qwen-plus
        "parameters": {
            "temperature": 0.01,
            "seed": random.randint(1, 65535),
            "stream": True,
            # "top_k": 0, # 整数，大于等于1
            # "enable_search": False,
            "result_format": "message",  # text|message
        },
        "input": {
            "messages": messages
        }
    }
    if param:
        json_data['parameters'].update(param)

    headers = {
        'Accept': 'text/event-stream',
        'Authorization': f'Bearer {api_key}',
        'user-agent': 'dashscope/1.11.0; python/3.8.16; platform/macOS-10.16-x86_64-i386-64bit; processor/i386',
        'Content-Type': 'application/json',
        'X-Accel-Buffering': 'no',
        'X-DashScope-SSE': 'enable'
    }

    req_params = {
        'method': 'POST',
        'url': url,
        'headers': headers,
        'json': json_data
    }

    return req_params


def ali_api_res_to_openai(res, idx):
    chunk = res.decode()
    datas = chunk.split('\n')
    chunk_data = {
        'event': '',
        'id': '',
        'data': '',
    }
    for one in datas:
        if not one.strip():
            continue

        one = one.strip('\n')
        if one.startswith('event'):
            chunk_data['event'] = one[6:].strip()
        elif one.startswith('id'):
            chunk_data['id'] = one[3:].strip()
        elif one.startswith('data'):
            chunk_data['data'] = one[5:].strip()

    if chunk_data['event'] == ['error', 'interrupted']:
        pass
        # raise RequestException(detail=chunk_data['data'])
    data = orjson.loads(chunk_data['data'])
    content = data['output']['choices'][0]['message']['content']
    finish_reason = data['output']['choices'][0]['finish_reason']
    usage = data['usage']
    openai_res = {
        'id': chunk_data['id'],
        'choices': [{
            'delta': {'content': content[idx:], 'role': 'assistant'},
            'finish_reason': finish_reason,
        }],
        'usage': usage
    }
    idx = len(content)
    return b'data: ' + orjson.dumps(openai_res) + b'\n', idx


async def chat_test():
    """
    todo key 补充
    """
    api_key = 'sk-1994'
    msg = [
        {"role": "user", "content": "你是谁？"}
    ]
    model = 'qwen-turbo'
    req_params = qwen_chat(api_key, msg, model)

    req = httpx.Request(**req_params)
    client = httpx.AsyncClient(http1=True, http2=False)
    r = await client.send(req, stream=True)
    i = 0
    async for chunk in r.aiter_bytes():
        try:
            res, i = ali_api_res_to_openai(chunk, i)
            res_ = json.loads(res.decode()[len('data:'):])
            print(res_['choices'][0]['delta']['content'], end='')

        except Exception as e:
            print(e)
            print(chunk)

    print()


if __name__ == '__main__':
    asyncio.run(chat_test())
