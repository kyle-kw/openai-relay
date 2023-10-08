# -*- coding:utf-8 -*-

# @Time   : 2023/8/22 09:11
# @Author : huangkewei

import asyncio
import httpx
import orjson
import cachetools.func
API_TOKEN_TTL_SECONDS = 24 * 60 * 60

CACHE_TTL_SECONDS = API_TOKEN_TTL_SECONDS - 30


@cachetools.func.ttl_cache(maxsize=10, ttl=CACHE_TTL_SECONDS)
def get_api_token(ak, sk):
    auth_data = {
        "auth": {
            "identity": {
                "methods": [
                    "hw_ak_sk"
                ],
                "hw_ak_sk": {
                    "access": {
                        "key": ak
                    },
                    "secret": {
                        "key": sk
                    }
                }
            },
            "scope": {
                "project": {
                    "name": "cn-southwest-2"
                }
            }
        }
    }
    AUTH_URL = r'https://iam.myhuaweicloud.com/v3/auth/tokens'
    resp = httpx.post(AUTH_URL, json=auth_data, headers={"Content-Type": "application/json"})
    token = resp.headers.get('X-Subject-Token')
    if token:
        return token
    else:
        raise Exception(f"huawei Auth failed: {resp.status_code}")


def pangu_distribute(ak, sk, url, body):
    pangu_token = get_api_token(ak, sk)

    req_new = {
        'method': "POST",
        'url': url,
        'headers': {
            "Content-Type": "application/json",
            "X-Auth-Token": pangu_token
        },
        'data': orjson.dumps(body).decode(),
    }

    return req_new


async def pangu_test():
    """
    todo key 补充
    """

    ak = 'QDO2'
    sk = 'uNkFb'
    url_base = 'https://bd45b8ee418c470d996c7.apigw.cn-north-4.huaweicloud.com/v1/infers/b073736c/'
    project_id = '3d994d'
    deployment_id = '043a25'

    url_path = f'/v1/{project_id}/deployments/{deployment_id}/chat/completions'
    url = url_base + url_path

    msg = """你是谁？"""
    body = {
        # "prompt": "你是谁。",
        "messages": [{'role': 'user', 'content': msg}],
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
    # print(req_new)
    req = httpx.Request(**req_new)

    client = httpx.AsyncClient()
    res = await client.send(req, stream=True)
    print(res.status_code)
    async for one in res.aiter_bytes():
        resp = one.decode()
        print(resp)
        res_lst = resp.strip().split("data:")
        for res in res_lst:
            if not res:
                continue
            try:
                if res.strip() == 'moderation':
                    continue

                result = orjson.loads(res)
                choices = result['choices'][0]
                context = (
                        choices.get('text', '') or
                        choices.get('message', {}).get('content', '')
                )
                print(context, end='')
            except Exception as e:
                # print(res)
                pass
    print()


if __name__ == '__main__':
    asyncio.run(pangu_test())

