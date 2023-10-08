# -*- coding:utf-8 -*-

# @Time   : 2023/9/6 15:52
# @Author : huangkewei

import asyncio
import httpx
import time
import cachetools.func
import jwt

API_TOKEN_TTL_SECONDS = 3 * 60

CACHE_TTL_SECONDS = API_TOKEN_TTL_SECONDS - 30


@cachetools.func.ttl_cache(maxsize=10, ttl=CACHE_TTL_SECONDS)
def generate_token(apikey: str):
    try:
        api_key, secret = apikey.split(".")
    except Exception as e:
        raise Exception("invalid api_key", e)

    payload = {
        "api_key": api_key,
        "exp": int(round(time.time() * 1000)) + API_TOKEN_TTL_SECONDS * 1000,
        "timestamp": int(round(time.time() * 1000)),
    }

    return jwt.encode(
        payload,
        secret,
        algorithm="HS256",
        headers={"alg": "HS256", "sign_type": "SIGN"},
    )


def zhipu_chat(api_key, model, json_data):
    token = generate_token(api_key)

    # chatglm_pro, chatglm_std, chatglm_lite, chatglm_lite_32k
    url = f'https://open.bigmodel.cn/api/paas/v3/model-api/{model}/sse-invoke'

    kwargs = {
        "method": "POST",
        'url': url,
        'headers': {"Authorization": token},
        'json': json_data,
    }

    return kwargs


async def zhipu_chat_test():
    """
    todo key 补充
    """
    api_key = '30951'
    model = 'chatglm_pro'
    json_data = {'prompt': [{'content': '你是谁？', 'role': 'user'}], 'temperature': 0.9, 'top_p': 0.7}
    kwargs = zhipu_chat(api_key, model, json_data)

    client = httpx.AsyncClient(http1=True, http2=False, timeout=300)
    req = client.build_request(**kwargs)

    r = await client.send(req, stream=True)
    a = []
    async for chunk in r.aiter_bytes():
        chunk = chunk.decode()
        a.append(chunk)
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

        print(chunk_data['data'], end='')
    print()


if __name__ == '__main__':
    asyncio.run(zhipu_chat_test())
