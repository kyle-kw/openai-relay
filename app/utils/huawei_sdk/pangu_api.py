# -*- coding:utf-8 -*-

# @Time   : 2023/8/22 09:11
# @Author : huangkewei

import asyncio
import httpx
import orjson
from app.utils.huawei_sdk.signer import Signer, HttpRequest


def pangu_distribute(ak, sk, url, body):
    sig = Signer()
    sig.Key = ak
    sig.Secret = sk

    r = HttpRequest("POST", url)

    r.headers = {"content-type": "application/json"}
    r.body = orjson.dumps(body).decode()
    sig.Sign(r)

    req_new = {
        'method': r.method,
        'url': r.scheme + "://" + r.host + r.uri,
        'headers': r.headers,
        'data': r.body.decode(),
    }

    return req_new


async def pangu_test():

    ak = ''
    sk = ''
    url_base = ''
    project_id = ''
    deployment_id = ''
    url_path = f'/v1/{project_id}/deployments/{deployment_id}/chat/completions'
    url = url_base + url_path
    body = {
        # "prompt": "写一个穿越到宋朝的故事。",
        "messages": [{'role': 'user', 'content': '写一个穿越到宋朝的故事。'}],
        "max_tokens": 200,
        "temperature": 0.9,
        "n": 1,
        "stream": True
    }
    req_new = pangu_distribute(
        ak=ak,
        sk=sk,
        url=url,
        body=body,
    )

    req = httpx.Request(**req_new)

    client = httpx.AsyncClient()
    res = await client.send(req, stream=True)
    print(res.status_code)
    async for one in res.aiter_bytes():
        resp = one.decode()
        print(resp)


if __name__ == '__main__':
    asyncio.run(pangu_test())

