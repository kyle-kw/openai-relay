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


